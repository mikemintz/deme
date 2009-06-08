#TODO completely clean up code

from django.core.urlresolvers import reverse
from django import template
from django.db.models import Q
from django.db import models
from cms.models import *
from django.utils.http import urlquote
from django.utils.html import escape, urlize
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.timesince import timesince
from django.utils.text import capfirst, truncate_words
from django.utils import simplejson
from django.utils.safestring import mark_safe
from urlparse import urljoin
import os

register = template.Library()

###############################################################################
# Helper functions
###############################################################################

def agentcan_global_helper(context, ability, wildcard_suffix=False):
    """
    Return a boolean for whether the logged in agent has the specified global
    ability. If wildcard_suffix=True, then return True if the agent has **any**
    global ability whose first word is the specified ability.
    """
    agent = context['cur_agent']
    permission_cache = context['_viewer'].permission_cache
    if wildcard_suffix:
        global_abilities = permission_cache.global_abilities(agent)
        return any(x.startswith(ability) for x in global_abilities)
    else:
        return permission_cache.agent_can_global(agent, ability)


def agentcan_helper(context, ability, item, wildcard_suffix=False):
    """
    Return a boolean for whether the logged in agent has the specified ability.
    If wildcard_suffix=True, then return True if the agent has **any** ability
    whose first word is the specified ability.
    """
    agent = context['cur_agent']
    permission_cache = context['_viewer'].permission_cache
    if wildcard_suffix:
        abilities_for_item = permission_cache.item_abilities(agent, item)
        return any(x.startswith(ability) for x in abilities_for_item)
    else:
        return permission_cache.agent_can(agent, ability, item)


def get_viewable_name(context, item):
    """
    If the logged in agent can view the item's name, return the item's name.
    Otherwise, return a string like "GroupAgent 51".
    """
    can_view_name_field = agentcan_helper(context, 'view name', item)
    return item.display_name(can_view_name_field)


###############################################################################
# Filters and templates
###############################################################################

#TODO this should be a tag, not a filter
@register.filter
def icon_url(item_type, size=32):
    """
    Return a URL for an icon for the item type, size x size pixels.
    
    The item_type can either be a string for the name of the item type, or it
    can be a class. If nothing matches, return the generic Item icon.
    
    Special strings, such as "error" and "history", are set to specific icons.
    
    Not all sizes are available (look at static/crystal_project).
    """
    item_type_to_icon = {
        'error':                'apps/error',
        'checkbox':             'apps/clean',
        'new':                  'apps/easymoblog',
        'copy':                 'apps/easymoblog',
        'history':              'apps/cal',
        'subscribe':            'apps/knewsticker',
        'relationships':        'apps/proxy',
        'permissions':          'apps/ksysv',
        'edit':                 'apps/kedit',
        'delete':               'filesystems/trashcan_empty',
        Agent:                  'apps/personal',
        AuthenticationMethod:   'apps/password',
        ContactMethod:          'apps/kontact',
        CustomUrl:              'mimetypes/message',
        Comment:                'apps/filetypes',
        DemeSetting:            'apps/advancedsettings',
        Document:               'mimetypes/empty',
        DjangoTemplateDocument: 'mimetypes/html',
        EmailContactMethod:     'apps/kmail',
        Excerpt:                'mimetypes/shellscript',
        FileDocument:           'mimetypes/misc',
        Folio:                  'apps/kfm',
        Group:                  'apps/Login%20Manager',
        Item:                   'apps/kblackbox',
        Collection:             'filesystems/folder_blue',
        Membership:             'filesystems/folder_documents',
        Person:                 'apps/access',
        Site:                   'devices/nfs_unmount',
        Subscription:           'apps/knewsticker',
        TextDocument:           'mimetypes/txt',
        Transclusion:           'apps/knotes',
        ViewerRequest:          'mimetypes/message',
    }
    if isinstance(item_type, basestring):
        if item_type not in item_type_to_icon:
            item_type = get_item_type_with_name(item_type)
            if item_type:
                return icon_url(item_type, size)
    elif isinstance(item_type, Item):
        return icon_url(item_type.actual_item_type(), size)
    elif isinstance(item_type, type) and issubclass(item_type, Item):
        if item_type not in item_type_to_icon:
            return icon_url(item_type.__base__, size)
    else:
        item_type = Item
    icon = item_type_to_icon.get(item_type, item_type_to_icon[Item])
    return urljoin(settings.MEDIA_URL, "crystal_project/%dx%d/%s.png" % (size, size, icon))

@register.simple_tag
def media_url(path):
    fs_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(fs_path):
        return urljoin(settings.MEDIA_URL, path)
    else:
        if settings.DEBUG:
            return "[Couldn't find path %s on filesystem]" % path
        else:
            return '' # Fail silently for invalid paths.


class ListResultsNavigator(template.Node):
    def __init__(self, max_pages):
        self.max_pages = template.Variable(max_pages)

    def __repr__(self):
        return "<ListResultsNavigator>"

    def render(self, context):
        """
        Make an HTML pagination navigator (page number links with prev and next
        links on both sides).
        
        The prev link will have class="list_results_prev". The next link will have
        class="list_results_next". Each page number link will have
        class="list_results_step". The current page number will be in a span with
        class="list_results_highlighted".
        """
        try:
            max_pages = self.max_pages.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve max_pages variable]"
            else:
                return '' # Fail silently for invalid variables.
        viewer = context['_viewer']
        n_results = context['n_listable_items']
        limit = context['limit']
        offset = context['offset']
        def url_with_offset(offset):
            querydict = viewer.request.GET.copy()
            querydict['offset'] = str(offset)
            return '%s?%s' % (viewer.context['full_path'], querydict.urlencode())
        if n_results <= limit:
            return ''
        result = []
        # Add a prev link
        if offset > 0:
            new_offset = max(0, offset - limit)
            prev_text = _('Prev')
            link = u'<a class="list_results_prev" href="%s">&laquo; %s</a>' % (url_with_offset(new_offset), prev_text)
            result.append(link)
        # Add the page links
        for new_offset in xrange(max(0, offset - limit * max_pages), min(n_results - 1, offset + limit * max_pages), limit):
            if new_offset == offset:
                link = '<span class="list_results_highlighted">%d</span>' % (1 + new_offset / limit,)
            else:
                link = '<a class="list_results_step" href="%s">%d</a>' % (url_with_offset(new_offset), 1 + new_offset / limit)
            result.append(link)
        # Add a next link
        if offset + limit < n_results:
            new_offset = offset + limit
            next_text = _('Next')
            link = u'<a class="list_results_next" href="%s">%s &raquo;</a>' % (url_with_offset(new_offset), next_text)
            result.append(link)
        return ''.join(result)


@register.tag
def list_results_navigator(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one arguments" % bits[0]
    return ListResultsNavigator(bits[1])


class UniversalEditButton(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<UniversalEditButtonNode>"

    def render(self, context):
        item = context['item']
        if item and agentcan_helper(context, 'edit', item, wildcard_suffix=True):
            edit_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'edit'}) + '?version=%s' % item.version_number
            return '<link rel="alternate" type="application/wiki" title="Edit" href="%s" />' % escape(edit_url)
        else:
            return ''

@register.tag
def universal_edit_button(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return UniversalEditButton()

class IfAgentCan(template.Node):
    def __init__(self, ability, ability_parameter, item, nodelist_true, nodelist_false):
        self.ability = template.Variable(ability)
        self.ability_parameter = template.Variable(ability_parameter)
        self.item = template.Variable(item)
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def __repr__(self):
        return "<IfAgentCanNode>"

    def render(self, context):
        agent = context['cur_agent']
        try:
            item = self.item.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve item variable]"
            else:
                return '' # Fail silently for invalid variables.
        try:
            ability = self.ability.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve ability variable]"
            else:
                return '' # Fail silently for invalid variables.
        try:
            ability_parameter = self.ability_parameter.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve ability_parameter variable]"
            else:
                return '' # Fail silently for invalid variables.
        ability = '%s %s' % (ability, ability_parameter) if ability_parameter else ability
        if agentcan_helper(context, ability, item):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def ifagentcan(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 4:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfAgentCan(bits[1], bits[2], bits[3], nodelist_true, nodelist_false)

class IfAgentCanGlobal(template.Node):
    def __init__(self, ability, ability_parameter, nodelist_true, nodelist_false):
        self.ability = template.Variable(ability)
        self.ability_parameter = template.Variable(ability_parameter)
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def __repr__(self):
        return "<IfAgentCanNode>"

    def render(self, context):
        agent = context['cur_agent']
        try:
            ability = self.ability.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve ability variable]"
            else:
                return '' # Fail silently for invalid variables.
        try:
            ability_parameter = self.ability_parameter.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve ability_parameter variable]"
            else:
                return '' # Fail silently for invalid variables.
        ability = '%s %s' % (ability, ability_parameter) if ability_parameter else ability
        if agentcan_global_helper(context, ability):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def ifagentcanglobal(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfAgentCanGlobal(bits[1], bits[2], nodelist_true, nodelist_false)

# remember this includes inactive comments, which should be displayed differently after calling this
def comment_dicts_for_item(item, version_number, context, include_recursive_collection_comments):
    permission_cache = context['_viewer'].permission_cache
    comment_subclasses = [TextComment]
    comments = []
    if include_recursive_collection_comments:
        if agentcan_global_helper(context, 'do_anything'):
            recursive_filter = None
        else:
            visible_memberships = permission_cache.filter_items(context['cur_agent'], 'view item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members_and_me_pks_query = Item.objects.filter(active=True).filter(Q(pk=item.pk) | Q(pk__in=item.all_contained_collection_members(recursive_filter).values('pk').query)).values('pk').query
        comment_pks = RecursiveComment.objects.filter(parent__in=members_and_me_pks_query).values_list('child', flat=True)
    else:
        comment_pks = RecursiveComment.objects.filter(parent=item).values_list('child', flat=True)
    if comment_pks:
        permission_cache.filter_items(context['cur_agent'], 'view created_at', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.filter_items(context['cur_agent'], 'view creator', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.filter_items(context['cur_agent'], 'view name', Agent.objects.filter(pk__in=Comment.objects.filter(pk__in=comment_pks).values('creator_id').query))
        for comment_subclass in comment_subclasses:
            new_comments = comment_subclass.objects.filter(pk__in=comment_pks)
            related_fields = ['creator']
            if include_recursive_collection_comments:
                related_fields.extend(['item'])
            new_comments = new_comments.select_related(*related_fields)
            comments.extend(new_comments)
    comments.sort(key=lambda x: x.created_at)
    pk_to_comment_info = {}
    for comment in comments:
        comment_info = {'comment': comment, 'subcomments': []}
        pk_to_comment_info[comment.pk] = comment_info
    comment_dicts = []
    for comment in comments:
        child = pk_to_comment_info[comment.pk]
        parent = pk_to_comment_info.get(comment.item_id)
        if parent:
            parent['subcomments'].append(child)
        else:
            comment_dicts.append(child)
    return comment_dicts, len(comments)

class ItemToolbar(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ItemToolbarNode>"

    def render(self, context):
        item = context['item']
        version_number = item.version_number
        cur_item_type = context['_viewer'].accepted_item_type
        item_type_inheritance = []
        while issubclass(cur_item_type, Item):
            item_type_inheritance.insert(0, cur_item_type)
            cur_item_type = cur_item_type.__base__

        result = []

        subscribe_url = reverse('item_type_url', kwargs={'viewer': 'subscription', 'action': 'new'}) + '?item=%s' % item.pk
        edit_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'edit'}) + '?version=%s' % version_number
        copy_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'copy'}) + '?version=%s' % version_number
        deactivate_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'deactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
        reactivate_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'reactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
        destroy_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'destroy'}) + '?redirect=%s' % urlquote(context['full_path'])
        add_authentication_method_url = reverse('item_type_url', kwargs={'viewer': 'authenticationmethod', 'action': 'new'}) + '?agent=%s' % item.pk
        add_contact_method_url = reverse('item_type_url', kwargs={'viewer': 'contactmethod', 'action': 'new'}) + '?agent=%s' % item.pk

        #result.append('<div class="fg-toolbar ui-widget-header ui-corner-all ui-helper-clearfix">')
        result.append('<div class="ui-helper-clearfix" style="font-size: 85%;">')
        result.append('<div class="fg-buttonset ui-helper-clearfix">')

        if isinstance(item, Agent):
            if agentcan_helper(context, 'add_authentication_method', item):
                result.append('<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-circle-plus"></span>Add authentication method</a>' % add_authentication_method_url)
            if agentcan_helper(context, 'add_contact_method', item):
                result.append('<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-circle-plus"></span>Add contact method</a>' % add_contact_method_url)
        result.append('<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-mail-closed"></span>Subscribe</a>' % subscribe_url)
        if agentcan_helper(context, 'edit', item, wildcard_suffix=True):
            result.append('<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-pencil"></span>Edit</a>' % edit_url)
        if agentcan_global_helper(context, 'create %s' % item.item_type_string):
            result.append('<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-copy"></span>Copy</a>' % copy_url)
        if item.can_be_deleted() and agentcan_helper(context, 'delete', item):
            if item.active:
                result.append("""
                    <script type="text/javascript">
                        $(function() {
                            $("#deactivate_dialog").dialog({
                                autoOpen: false,
                                bgiframe: true,
                                modal: true,
                                buttons: {
                                    'Deactivate': function(){$(this).dialog('close'); $('#deactivate_dialog form').submit()},
                                    'Cancel': function(){$(this).dialog('close')}
                                }
                            });
                        });
                        </script>
                    <div id="deactivate_dialog" title="Deactivate this item?" style="display: none;">
                        <form method="post" action="%s" onsubmit="$('#deactivate_dialog').dialog('close');">
                        <p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>Are you sure you want to deactivate this item?</p>
                        <label for="deactivate_reason">Reason</label>
                        <input type="text" id="deactivate_reason" name="action_summary" />
                        </form>
                    </div>
                    <a href="#" onclick="$('#deactivate_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-solo ui-corner-all" title="Deactivate"><span class="ui-icon ui-icon-trash"></span> Deactivate</a>
                """ % deactivate_url)
            else:
                result.append("""
                    <script type="text/javascript">
                        $(function() {
                            $("#reactivate_dialog").dialog({
                                autoOpen: false,
                                bgiframe: true,
                                modal: true,
                                buttons: {
                                    'Reactivate': function(){$(this).dialog('close'); $('#reactivate_dialog form').submit()},
                                    'Cancel': function(){$(this).dialog('close')}
                                }
                            });
                        });
                        </script>
                    <div id="reactivate_dialog" title="Reactivate this item?" style="display: none;">
                        <form method="post" action="%s" onsubmit="$('#reactivate_dialog').dialog('close');">
                        <p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>Are you sure you want to reactivate this item?</p>
                        <label for="reactivate_reason">Reason</label>
                        <input type="text" id="reactivate_reason" name="action_summary" />
                        </form>
                    </div>
                    <a href="#" onclick="$('#reactivate_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Reactivate"><span class="ui-icon ui-icon-trash"></span>Reactivate</a>
                """ % reactivate_url)
                result.append("""
                    <script type="text/javascript">
                        $(function() {
                            $("#destroy_dialog").dialog({
                                autoOpen: false,
                                bgiframe: true,
                                modal: true,
                                buttons: {
                                    'Destroy': function(){$(this).dialog('close'); $('#destroy_dialog form').submit()},
                                    'Cancel': function(){$(this).dialog('close')}
                                }
                            });
                        });
                        </script>
                    <div id="destroy_dialog" title="Destroy this item?" style="display: none;">
                        <form method="post" action="%s" onsubmit="$('#destroy_dialog').dialog('close');">
                        <p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>Are you sure you want to destroy this item?</p>
                        <label for="destroy_reason">Reason</label>
                        <input type="text" id="destroy_reason" name="action_summary" />
                        </form>
                    </div>
                    <a href="#" onclick="$('#destroy_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Destroy"><span class="ui-icon ui-icon-trash"></span>Destroy</a>
                """ % destroy_url)

        result.append('</div>')
        result.append('</div>')

        return '\n'.join(result)

@register.tag
def itemtoolbar(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero arguments" % bits[0]
    return ItemToolbar()


class ItemDetails(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ItemDetailsNode>"

    def render(self, context):
        item = context['item']
        result = []

        result.append('<table class="twocol" cellspacing="0" style="font-size: 85%;">')

        if agentcan_helper(context, 'view name', item) and item.name:
            result.append('<tr>')
            result.append('<th>Name:</th>')
            result.append('<td>')
            result.append(escape(item.name))
            result.append('</td>')
            result.append('</tr>')

        if agentcan_helper(context, 'view description', item) and item.description:
            result.append('<tr>')
            result.append('<th>Preface:</th>')
            result.append('<td>')
            result.append(escape(item.description))
            result.append('</td>')
            result.append('</tr>')

        result.append('<tr>')
        result.append('<th>Item type:</th>')
        result.append('<td>')
        result.append(u'%s' % capfirst(item.actual_item_type()._meta.verbose_name))
        result.append('</td>')
        result.append('</tr>')

        result.append('<tr>')
        result.append('<th>Status:</th>')
        result.append('<td>')
        if item.destroyed:
            result.append('<span style="color: #c00;">Destroyed</span>')
        elif not item.active:
            result.append('<span style="color: #c00;">Inactive</span>')
        else:
            result.append('<span style="color: #070;">Active</span>')
        result.append('</td>')
        result.append('</tr>')

        if agentcan_helper(context, 'view created_at', item):
            result.append('<tr>')
            result.append('<th>Created:</th>')
            result.append('<td>')
            result.append('<span title="%s">%s ago</span>' % (item.created_at.strftime("%Y-%m-%d %H:%M:%S"), timesince(item.created_at)))
            result.append('</td>')
            result.append('</tr>')

        if agentcan_helper(context, 'view creator', item):
            result.append('<tr>')
            result.append('<th>Creator:</th>')
            result.append('<td>')
            result.append('<a href="%s">%s</a>' % (item.creator.get_absolute_url(), escape(get_viewable_name(context, item.creator))))
            result.append('</td>')
            result.append('</tr>')

        result.append('</table>')

        return '\n'.join(result)

@register.tag
def itemdetails(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero arguments" % bits[0]
    return ItemDetails()


@register.simple_tag
def display_body_with_inline_transclusions(item, is_html):
    #TODO permissions? you should be able to see any Transclusion, but maybe not the id of the comment it refers to
    #TODO don't insert these in bad places, like inside a tag <img <a href="....> />
    #TODO when you insert a transclusion in the middle of a tag like <b>hi <COMMENT></b> then it gets the style, this is bad
    if is_html:
        format = lambda text: text
    else:
        format = lambda text: urlize(escape(text)).replace('\n', '<br />')
    transclusions = Transclusion.objects.filter(from_item=item, from_item_version_number=item.version_number, active=True, to_item__active=True).order_by('-from_item_index')
    result = []
    last_i = None
    for transclusion in transclusions:
        i = transclusion.from_item_index
        result.insert(0, format(item.body[i:last_i]))
        result.insert(0, '<a href="%s" class="commentref">%s</a>' % (transclusion.to_item.get_absolute_url(), escape(transclusion.to_item.display_name())))
        last_i = i
    result.insert(0, format(item.body[0:last_i]))
    return ''.join(result)


class CalculateComments(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateCommentsNode>"

    def render(self, context):
        item = context['item']
        version_number = item.version_number
        full_path = context['full_path']

        result = []
        result.append("""<div class="comment_box">""")
        result.append("""<div class="comment_box_header">""")
        if agentcan_helper(context, 'comment_on', item):
            result.append("""<a href="%s?item=%s&amp;item_version_number=%s&amp;redirect=%s">[+] Add Comment</a>""" % (reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'new'}), item.pk, version_number, urlquote(full_path)))
        result.append("""</div>""")
        def add_comments_to_div(comments, nesting_level=0):
            for comment_info in comments:
                comment = comment_info['comment']
                result.append("""<div class="comment_outer%s">""" % (' comment_outer_toplevel' if nesting_level == 0 else '',))
                result.append("""<div class="comment_header">""")
                result.append("""<div style="float: right;"><a href="%s?item=%s&amp;item_version_number=%s&amp;redirect=%s">[+] Reply</a></div>""" % (reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'new'}), comment.pk, comment.version_number, urlquote(full_path)))
                if issubclass(comment.item.actual_item_type(), Comment):
                    if agentcan_helper(context, 'view body', comment):
                        comment_name = escape(truncate_words(comment.body, 4))
                    else:
                        comment_name = comment.display_name(can_view_name_field=False)
                else:
                    comment_name = escape(get_viewable_name(context, comment))
                result.append("""<a href="%s">%s</a>""" % (comment.get_absolute_url(), comment_name))
                if agentcan_helper(context, 'view creator', comment):
                    result.append('by <a href="%s">%s</a>' % (comment.creator.get_absolute_url(), escape(get_viewable_name(context, comment.creator))))
                if item.pk != comment.item_id and nesting_level == 0:
                    result.append('for <a href="%s">%s</a>' % (comment.item.get_absolute_url(), escape(get_viewable_name(context, comment.item))))
                if agentcan_helper(context, 'view created_at', comment):
                    result.append('<span title="%s">%s ago</span>' % (comment.created_at.strftime("%Y-%m-%d %H:%M:%S"), timesince(comment.created_at)))
                result.append("</div>")
                if comment.active:
                    if isinstance(comment, TextComment):
                        if agentcan_helper(context, 'view body', comment):
                            comment_body = escape(comment.body).replace('\n', '<br />')
                        else:
                            comment_body = ''
                    else:
                        comment_body = ''
                else:
                    comment_body = '[INACTIVE]'
                result.append("""<div class="comment_body" style="display: none;">%s</div>""" % comment_body)
                add_comments_to_div(comment_info['subcomments'], nesting_level + 1)
                result.append("</div>")
        comment_dicts, n_comments = comment_dicts_for_item(item, version_number, context, isinstance(item, Collection))
        add_comments_to_div(comment_dicts)
        result.append("</div>")
        context['comment_box'] = mark_safe('\n'.join(result))
        context['n_comments'] = n_comments
        return ''

@register.tag
def calculatecomments(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateComments()


class PermissionsBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<PermissionsBoxNode>"

    def render(self, context):
        permission_cache = context['_viewer'].permission_cache
        item = context['item']
        cur_agent = context['cur_agent']
        abilities = sorted(permission_cache.item_abilities(cur_agent, item))

        result = []
        if agentcan_helper(context, 'do_anything', item):
            modify_permissions_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'itempermissions'})
            result.append("""<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-locked"></span>Modify permissions</a>""" % modify_permissions_url)
        elif agentcan_helper(context, 'modify_privacy_settings', item):
            modify_privacy_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'privacy'})
            result.append("""<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-locked"></span>Modify privacy</a>""" % modify_privacy_url)
        for ability in abilities:
            result.append("""<div>%s</div>""" % escape(ability))
        return '\n'.join(result)

@register.tag
def permissions_box(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return PermissionsBox()


class CalculateRelationships(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateRelationshipsNode>"

    def render(self, context):
        permission_cache = context['_viewer'].permission_cache
        item = context['item']
        cur_agent = context['cur_agent']

        relationship_sets = []
        for name in sorted(item._meta.get_all_field_names()):
            field, model, direct, m2m = item._meta.get_field_by_name(name)
            if not isinstance(field, models.related.RelatedObject):
                continue
            if not isinstance(field.field, models.ForeignKey):
                continue
            if isinstance(field.field, models.OneToOneField):
                continue
            if not issubclass(field.model, Item):
                continue
            manager = getattr(item, name)
            relationship_set = {}
            relationship_set['name'] = name
            relationship_set['field'] = field
            viewable_items = manager.filter(active=True)
            viewable_items = permission_cache.filter_items(cur_agent, 'view %s' % field.field.name, viewable_items)
            if viewable_items.count() == 0:
                continue
            relationship_item_type = manager.model
            permission_cache.filter_items(cur_agent, 'view name', viewable_items)
            relationship_set['items'] = viewable_items
            relationship_sets.append(relationship_set)

        result = []
        for relationship_set in relationship_sets:
            friendly_name = capfirst(relationship_set['name']).replace('_', ' ')
            field = relationship_set['field']
            list_url = '%s?filter=%s.%d' % (reverse('item_type_url', kwargs={'viewer': field.model.__name__.lower()}), field.field.name, item.pk)
            result.append("""<div><a href="%s"><b>%s</b></a></div>""" % (list_url, friendly_name))
            for related_item in relationship_set['items']:
                related_item_url = related_item.get_absolute_url()
                related_item_name = get_viewable_name(context, related_item)
                result.append("""<div><a href="%s">%s</a></div>""" % (related_item_url, escape(related_item_name)))
        context['relationships_box'] = mark_safe('\n'.join(result))
        context['n_relationships'] = sum(len(x['items']) for x in relationship_sets)
        return ''

@register.tag
def calculaterelationships(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateRelationships()


class CalculateHistory(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateHistoryNode>"

    def render(self, context):
        item = context['item']

        result = []
        versions = item.versions.all()
        for version in versions:
            version_url = reverse('item_url', kwargs={'viewer': context['viewer_name'], 'action': 'show', 'noun': item.pk}) + '?version=%s' % version.version_number
            result.append("""<div><a href="%s">Version %s</a></div>""" % (version_url, version.version_number))
        current_url = reverse('item_url', kwargs={'viewer': context['viewer_name'], 'action': 'show', 'noun': item.pk})
        result.append("""<div><a href="%s">Current version</a></div>""" % (current_url,))
        context['history_box'] = mark_safe('\n'.join(result))
        context['n_versions'] = len(versions) + 1
        return ''

@register.tag
def calculatehistory(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateHistory()


class CalculateActionNotices(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateActionNoticesNode>"

    def render(self, context):
        item = context['item']

        result = []
        if agentcan_helper(context, 'view action_notices', item):
            #TODO include recursive threads (comment replies, and items in this collection) of action notices
            action_notices = ActionNotice.objects.filter(Q(action_item=item) | Q(action_agent=item)).order_by('action_time')
            action_notice_pk_to_object_map = {}
            for action_notice_subclass in [RelationActionNotice, DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, CreateActionNotice, EditActionNotice]:
                select_related_fields = ['action_agent__name', 'action_item__name']
                if action_notice_subclass == RelationActionNotice:
                    select_related_fields.append('from_item__name')
                specific_action_notices = action_notice_subclass.objects.filter(pk__in=action_notices.values('pk').query).select_related(*select_related_fields)
                if action_notice_subclass == RelationActionNotice:
                    context['_viewer'].permission_cache.filter_items(context['cur_agent'], 'view name', Item.objects.filter(Q(pk__in=specific_action_notices.values('from_item').query)))
                for action_notice in specific_action_notices:
                    action_notice_pk_to_object_map[action_notice.pk] = action_notice
            context['_viewer'].permission_cache.filter_items(context['cur_agent'], 'view name', Item.objects.filter(Q(pk__in=action_notices.values('action_item').query) | Q(pk__in=action_notices.values('action_agent').query)))
            for action_notice in action_notices:
                action_notice = action_notice_pk_to_object_map[action_notice.pk]
                if isinstance(action_notice, RelationActionNotice):
                    if not agentcan_helper(context, 'view %s' % action_notice.from_field_name, action_notice.from_item):
                        continue
                action_time_text = '<span title="%s">%s ago</span>' % (action_notice.action_time.strftime("%Y-%m-%d %H:%M:%S"), timesince(action_notice.action_time))
                action_agent_name = get_viewable_name(context, action_notice.action_agent)
                action_agent_text = u'<a href="%s">%s</a>' % (escape(action_notice.action_agent.get_absolute_url()), escape(action_agent_name))
                if action_notice.action_item.pk == item.pk:
                    action_item_name = 'this'
                else:
                    action_item_name = get_viewable_name(context, action_notice.action_item)
                action_item_text = u'<a href="%s">%s</a>' % (escape(action_notice.action_item.get_absolute_url() + '?version=%d' % action_notice.action_item_version_number), escape(action_item_name))
                if action_notice.action_summary:
                    action_summary_text = u'(%s)' % escape(action_notice.action_summary)
                else:
                    action_summary_text = ''
                if isinstance(action_notice, RelationActionNotice):
                    from_item_name = get_viewable_name(context, action_notice.from_item)
                    from_item_text = u'<a href="%s">%s</a>' % (escape(action_notice.from_item.get_absolute_url() + '?version=%d' % action_notice.from_item_version_number), escape(from_item_name))
                    if action_notice.relation_added:
                        action_text = u"set the %s of %s to" % (action_notice.from_field_name, from_item_text)
                    else:
                        action_text = u"unset the %s of %s from" % (action_notice.from_field_name, from_item_text)
                if isinstance(action_notice, DeactivateActionNotice):
                    action_text = 'deactivated'
                if isinstance(action_notice, ReactivateActionNotice):
                    action_text = 'reactivated'
                if isinstance(action_notice, DestroyActionNotice):
                    action_text = 'destroyed'
                if isinstance(action_notice, CreateActionNotice):
                    action_text = 'created'
                if isinstance(action_notice, EditActionNotice):
                    action_text = 'edited'
                result.append(u'<div style="font-size: 85%%; margin-bottom: 5px;">[%s]<br />%s %s %s %s</div>' % (action_time_text, action_agent_text, action_text, action_item_text, action_summary_text))
        else:
            action_notices = []

        context['n_action_notices'] = len(action_notices)
        context['action_notice_box'] = mark_safe('\n'.join(result))
        return ''

@register.tag
def calculateactionnotices(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateActionNotices()


class SubclassFieldsBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<SubclassFieldsBox>"

    def render(self, context):
        viewer = context['_viewer']
        viewer_method_name = "%s_%s_%s" % ('item' if viewer.noun else 'type', viewer.action, viewer.format)
        viewer_where_action_defined = type(viewer)
        while viewer_where_action_defined.__name__ != 'ItemViewer':
            parent_viewer = viewer_where_action_defined.__base__
            my_fn = getattr(viewer_where_action_defined, viewer_method_name, None)
            parent_fn = getattr(parent_viewer, viewer_method_name, None)
            if my_fn is None or parent_fn is None:
                break
            if my_fn.im_func is not parent_fn.im_func:
                break
            viewer_where_action_defined = parent_viewer
        viewer_item_type = viewer_where_action_defined.accepted_item_type
        viewer_item_type_field_names = set([x.name for x in viewer_item_type._meta.fields])
        item = context['item']
        fields = []
        field_names_used = set()
        for field in item._meta.fields:
            if field.name in field_names_used:
                continue
            field_names_used.add(field.name)
            if field.name in viewer_item_type_field_names:
                continue
            if isinstance(field, (models.OneToOneField, models.ManyToManyField)):
                continue
            fields.append(field)
        if item.destroyed or not fields:
            return ''
        fields.sort(key=lambda x:x.name)
        result = []
        result.append('<table cellspacing="0" class="twocol">')
        for field in fields:
            if agentcan_helper(context, 'view %s' % field.name, item):
                result.append('<tr>')
                result.append(u'<th style="white-space: nowrap;">%s</th>' % capfirst(field.verbose_name))
                result.append('<td>')
                if isinstance(field, models.ForeignKey):
                    foreign_item = getattr(item, field.name)
                    if foreign_item:
                        result.append('<a href="%s">%s</a>' % (escape(foreign_item.get_absolute_url()), get_viewable_name(context, foreign_item)))
                    else:
                        result.append('None')
                else:
                    data = getattr(item, field.name)
                    if isinstance(field, models.FileField):
                        #TODO use .url
                        result.append('<a href="%s%s">%s</a>' % (escape(settings.MEDIA_URL), escape(data), escape(data)))
                    elif isinstance(field, models.TextField):
                        result.append(urlize(escape(data)).replace('\n', '<br />'))
                    else:
                        result.append(escape(data))
                result.append('</td>')
                result.append('</tr>')
        result.append('</table>')
        return '\n'.join(result)


@register.tag
def subclassfields(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return SubclassFieldsBox()


class EmbeddedItem(template.Node):
    def __init__(self, viewer_name, item):
        self.viewer_name = template.Variable(viewer_name)
        self.item = template.Variable(item)

    def __repr__(self):
        return "<EmbeddedItemNode>"

    def render(self, context):
        from cms.base_viewer import get_viewer_class_by_name
        viewer_name = self.viewer_name.resolve(context)
        viewer_class = get_viewer_class_by_name(viewer_name)
        if viewer_class is None:
            return ''
        item = self.item.resolve(context)
        if isinstance(item, basestring):
            try:
                item = Item.objects.get(pk=item)
            except ObjectDoesNotExist:
                item = None
        if not isinstance(item, Item):
            return ''
        item = item.downcast()
        viewer = viewer_class()
        viewer.init_for_div(context['_viewer'], 'show', item)
        return """<div style="padding: 10px; border: thick solid #aaa;">%s</div>""" % viewer.dispatch().content


@register.tag
def embed(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    return EmbeddedItem(bits[1], bits[2])


class ViewableName(template.Node):
    def __init__(self, item):
        self.item = template.Variable(item)

    def __repr__(self):
        return "<ViewableName>"

    def render(self, context):
        try:
            item = self.item.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve item variable]"
            else:
                return '' # Fail silently for invalid variables.
        return get_viewable_name(context, item)

@register.tag
def viewable_name(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    return ViewableName(bits[1])


class PermissionEditor(template.Node):
    def __init__(self, item, is_global_permissions, privacy_only):
        if item is None:
            self.item = None
        else:
            self.item = template.Variable(item)
        self.is_global_permissions = is_global_permissions
        self.privacy_only = privacy_only

    def __repr__(self):
        return "<PermissionEditor>"

    def render(self, context):
        if self.item is None:
            item = None
        else:
            try:
                item = self.item.resolve(context)
            except template.VariableDoesNotExist:
                if settings.DEBUG:
                    return "[Couldn't resolve item variable]"
                else:
                    return '' # Fail silently for invalid variables.
        viewer = context['_viewer']

        if self.is_global_permissions:
            possible_abilities = viewer.permission_cache.all_possible_global_abilities()
        else:
            if item is None:
                possible_abilities = viewer.permission_cache.all_possible_item_abilities(viewer.accepted_item_type)
            else:
                possible_abilities = viewer.permission_cache.all_possible_item_abilities(viewer.item.actual_item_type())
        if self.privacy_only:
            possible_abilities = [x for x in possible_abilities if x.startswith('view ')]

        if item is None and not self.is_global_permissions and not self.privacy_only:
            # Default permissions when creating a new item
            agent_permissions = [AgentItemPermission(agent=context['cur_agent'], ability='do_anything', is_allowed=True)]
            collection_permissions = []
            everyone_permissions = []
            agents = sorted(set(x.agent for x in agent_permissions), key=lambda x: x.name)
            collections = sorted(set(x.collection for x in collection_permissions), key=lambda x: x.name)
        else:
            if self.is_global_permissions:
                agent_permissions = AgentGlobalPermission.objects.order_by('ability')
                collection_permissions = CollectionGlobalPermission.objects.order_by('ability')
                everyone_permissions = EveryoneGlobalPermission.objects.order_by('ability')
            else:
                agent_permissions = item.agent_item_permissions_as_item.order_by('ability')
                collection_permissions = item.collection_item_permissions_as_item.order_by('ability')
                everyone_permissions = item.everyone_item_permissions_as_item.order_by('ability')
                if self.privacy_only:
                    agent_permissions = agent_permissions.filter(ability__startswith='view ')
                    collection_permissions = collection_permissions.filter(ability__startswith='view ')
                    everyone_permissions = everyone_permissions.filter(ability__startswith='view ')
            agents = Agent.objects.filter(pk__in=agent_permissions.values('agent__pk').query).order_by('name')
            collections = Collection.objects.filter(pk__in=collection_permissions.values('collection__pk').query).order_by('name')
        
        existing_permission_data = []
        for agent in agents:
            datum = {}
            datum['permission_type'] = 'agent'
            datum['name'] = get_viewable_name(context, agent)
            datum['agent_or_collection_id'] = str(agent.pk)
            datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in agent_permissions if x.agent == agent]
            existing_permission_data.append(datum)
        collection_data = []
        for collection in collections:
            datum = {}
            datum['permission_type'] = 'collection'
            datum['name'] = get_viewable_name(context, collection)
            datum['agent_or_collection_id'] = str(collection.pk)
            datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in collection_permissions if x.collection == collection]
            existing_permission_data.append(datum)
        datum = {}
        datum['permission_type'] = 'everyone'
        datum['name'] = 'Everyone'
        datum['agent_or_collection_id'] = '0'
        datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in everyone_permissions]
        existing_permission_data.append(datum)

        from cms.views import AjaxModelChoiceField
        new_agent_select_widget = AjaxModelChoiceField(Agent.objects, cur_agent=viewer.cur_agent, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_agent', None)
        new_collection_select_widget = AjaxModelChoiceField(Collection.objects, cur_agent=viewer.cur_agent, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_collection', None)
        #TODO the widgets get centered-alignment in the dialog, which looks bad

        result = """
        <script>
            var permission_counter = 1;
            var possible_abilities = %(possible_ability_javascript_array)s;
            function add_permission_fields(wrapper, permission_type, agent_or_collection_id, is_allowed, ability) {
                var is_allowed_checkbox = $('<input type="checkbox" name="newpermission' + permission_counter + '_is_allowed" value="on">');
                is_allowed_checkbox.attr('checked', is_allowed);
                is_allowed_checkbox.attr('defaultChecked', is_allowed);
                var ability_select = $('<select name="newpermission' + permission_counter + '_ability">');
                for (var i in possible_abilities) {
                    var is_selected = (possible_abilities[i] == ability);
                    ability_select[0].options[i] = new Option(possible_abilities[i], possible_abilities[i], is_selected, is_selected);
                }
                var remove_button = $('<a href="#" class="img_link">');
                remove_button.addClass('img_link');
                remove_button.append('<img src="%(delete_img_url)s" />');
                remove_button.bind('click', function(e){wrapper.remove(); return false;});
                wrapper.append(is_allowed_checkbox);
                wrapper.append(ability_select);
                wrapper.append(remove_button);
                wrapper.append('<input type="hidden" name="newpermission' + permission_counter + '_permission_type" value="' + permission_type + '" />');
                wrapper.append('<input type="hidden" name="newpermission' + permission_counter + '_agent_or_collection_id" value="' + agent_or_collection_id + '" />');
                permission_counter += 1;
            }

            function add_permission_div(wrapper, permission_type, agent_or_collection_id, is_allowed, ability) {
                var permission_div = $('<div>');
                add_permission_fields(permission_div, permission_type, agent_or_collection_id, is_allowed, ability);
                wrapper.append(permission_div);
            }

            function add_agent_or_collection_row(permission_type, agent_or_collection_id, name) {
                var row = $('<tr>');
                if (permission_type == 'agent') {
                    var name_url = '%(sample_agent_url)s'.replace('1', agent_or_collection_id);
                    row.append('<td><a href="' + name_url + '">' + name + '</a></td>');
                } else if (permission_type == 'collection') {
                    var name_url = '%(sample_collection_url)s'.replace('1', agent_or_collection_id);
                    row.append('<td><a href="' + name_url + '">' + name + '</a></td>');
                } else if (permission_type == 'everyone') {
                    row.append('<td>' + name + '</td>');
                }
                var permissions_cell = $('<td>');
                permissions_cell.addClass('permissions_cell');
                var add_button = $('<a href="#" class="img_link">');
                add_button.append('<img src="%(new_img_url)s" /> New Permission');
                add_button.bind('click', function(e){
                    var permission_div = $('<div>');
                    add_permission_fields(permission_div, permission_type, agent_or_collection_id, true, '');
                    permissions_cell.append(permission_div);
                    return false;
                });
                permissions_cell.append(add_button);
                row.append(permissions_cell);
                $('#permission_table tbody').append(row);
                return row;
            }

            $(document).ready(function(){
                var existing_permission_data = %(existing_permission_data_javascript_array)s;
                for (var i in existing_permission_data) {
                    var datum = existing_permission_data[i];
                    var row = add_agent_or_collection_row(datum.permission_type, datum.agent_or_collection_id, datum.name);
                    var permissions_cell = row.children('td.permissions_cell');
                    for (var j in datum.permissions) {
                        var permission = datum.permissions[j];
                        add_permission_div(permissions_cell, datum.permission_type, datum.agent_or_collection_id, permission.is_allowed, permission.ability);
                    }
                    $('#permission_table tbody').append(row);
                }

                $('#new_agent_dialog').dialog({
                    autoOpen: false,
                    close: function(event, ui){
                        $('input[name="new_agent"]').val('');
                        $('input[name="new_agent_search"]').val('');
                    },
                    buttons: {
                        'Add Agent': function(){
                            add_agent_or_collection_row('agent', $('input[name="new_agent"]').val(), $('input[name="new_agent_search"]').val());
                            $(this).dialog("close");
                        },
                        'Cancel': function(){
                            $(this).dialog("close");
                        }
                    },
                });

                $('#new_collection_dialog').dialog({
                    autoOpen: false,
                    close: function(event, ui){
                        $('input[name="new_collection"]').val('');
                        $('input[name="new_collection_search"]').val('');
                    },
                    buttons: {
                        'Add Collection': function(){
                            add_agent_or_collection_row('collection', $('input[name="new_collection"]').val(), $('input[name="new_collection_search"]').val());
                            $(this).dialog("close");
                        },
                        'Cancel': function(){
                            $(this).dialog("close");
                        }
                    },
                });
            });
        </script>

        <div id="new_agent_dialog" style="display: none;">
            Name: %(new_agent_select_widget)s
        </div>

        <div id="new_collection_dialog" style="display: none;">
            Name: %(new_collection_select_widget)s
        </div>

        <table id="permission_table" class="list" cellspacing="0">
            <tbody>
                <tr>
                    <th>Name</th>
                    <th>Permissions</th>
                </tr>
            </tbody>
        </table>

        <a href="#" class="img_link" onclick="$('#new_agent_dialog').dialog('open'); return false;"><img src="%(agent_img_url)s" /> <span>Select Agent</span></a>
        <a href="#" class="img_link" onclick="$('#new_collection_dialog').dialog('open'); return false;"><img src="%(collection_img_url)s" /> <span>Select Collection</span></a>
""" % {
        'possible_ability_javascript_array': simplejson.dumps(sorted(possible_abilities), separators=(',',':')),
        'existing_permission_data_javascript_array': simplejson.dumps(existing_permission_data, separators=(',',':')),
        'sample_agent_url': reverse('item_url', kwargs={'viewer': 'agent', 'noun': '1'}),
        'sample_collection_url': reverse('item_url', kwargs={'viewer': 'collection', 'noun': '1'}),
        'delete_img_url': icon_url('delete', 16),
        'new_img_url': icon_url('new', 16),
        'agent_img_url': icon_url('Agent', 16),
        'collection_img_url': icon_url('Collection', 16),
        'new_agent_select_widget': AjaxModelChoiceField(Agent.objects, cur_agent=viewer.cur_agent, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_agent', None),
        'new_collection_select_widget': AjaxModelChoiceField(Collection.objects, cur_agent=viewer.cur_agent, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_collection', None),
        }
        return result

@register.tag
def privacy_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2 and len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero or one argument" % bits[0]
    item = bits[1] if len(bits) == 2 else None
    return PermissionEditor(item, is_global_permissions=False, privacy_only=True)

@register.tag
def item_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2 and len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero or one argument" % bits[0]
    item = bits[1] if len(bits) == 2 else None
    return PermissionEditor(item, is_global_permissions=False, privacy_only=False)

@register.tag
def global_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero arguments" % bits[0]
    item = None
    return PermissionEditor(item, is_global_permissions=True, privacy_only=False)

class Crumbs(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<Crumbs>"

    def render(self, context):
        #TODO we should not be raising exceptions, including database queries that could fail
        viewer = context['_viewer']
        item_type_parameter = viewer.request.GET.get('crumb_item_type')
        filter_parameter = viewer.request.GET.get('crumb_filter') or viewer.request.GET.get('filter')
        if item_type_parameter:
            item_type = get_item_type_with_name(item_type_parameter, case_sensitive=False)
        else:
            item_type = viewer.accepted_item_type
        result = []
        if not filter_parameter:
            top_level_item_type_url = reverse('item_type_url', kwargs={'viewer': 'item'})
            item_type_url = reverse('item_type_url', kwargs={'viewer': item_type.__name__.lower()})
            result.append(u'<a href="%s">%s</a>' % (top_level_item_type_url, capfirst(Item._meta.verbose_name_plural)))
            if item_type != Item:
                result.append(u' &raquo; <a href="%s">%s</a>' % (item_type_url, capfirst(item_type._meta.verbose_name_plural)))
        else:
            filter_string = str(filter_parameter) # Unicode doesn't work here
            parts = filter_string.split('.')
            target_pk = parts.pop()
            fields = []
            field_models = [item_type]
            cur_item_type = item_type
            for part in parts:
                field = cur_item_type._meta.get_field_by_name(part)[0]
                fields.append(field)
                if isinstance(field, models.ForeignKey):
                    cur_item_type = field.rel.to
                elif isinstance(field, models.related.RelatedObject):
                    cur_item_type = field.model
                else:
                    raise Exception("Cannot filter on field %s.%s (not a related field)" % (cur_item_type.__name__, field.name))
                if not issubclass(cur_item_type, Item):
                    raise Exception("Cannot filter on field %s.%s (non item-type model)" % (cur_item_type.__name__, field.name))
                field_models.append(cur_item_type)
            target = field_models[-1].objects.get(pk=target_pk)
            reverse_fields = []
            for field in reversed(fields):
                if isinstance(field, models.ForeignKey):
                    reverse_field = field.rel
                else:
                    reverse_field = field.field
                reverse_fields.append(reverse_field)

            result = []
            result.append('<a href="%s">%s</a>' % (target.get_absolute_url(), get_viewable_name(context, target)))
            for i, field in enumerate(reverse_fields):
                subfilter = []
                subfilter_fields = fields[len(fields)-i-1:]
                subfilter_field_models = field_models[len(fields)-i-1:]
                for subfilter_field in subfilter_fields:
                    if isinstance(subfilter_field, models.ForeignKey):
                        name = subfilter_field.name
                    else:
                        name = subfilter_field.field.related_query_name()
                    subfilter.append(name)
                subfilter.append(target_pk)
                subfilter = '.'.join(subfilter)
                subfilter_item_type = subfilter_field_models[0]
                subfilter_url = '%s?filter=%s' % (reverse('item_type_url', kwargs={'viewer': subfilter_item_type.__name__.lower()}), subfilter)
                if isinstance(field, models.OneToOneField):
                    # We don't display crumbs for OneToOneFields like item_ptr
                    continue
                if isinstance(field, models.ForeignKey):
                    # Make it plural
                    field_name = field.verbose_name + u's'
                else:
                    field_name = field.related_name
                result.append(u' &raquo; <a href="%s">' % subfilter_url)
                result.append(capfirst(field_name.replace('_', ' ')))
                result.append('</a>')
        action_title = context['action_title']
        if viewer.item:
            item_url = reverse('item_url', kwargs={'viewer': viewer.viewer_name, 'noun': viewer.noun})
            result.append(u' &raquo; <a href="%s">%s</a>' % (item_url, get_viewable_name(context, viewer.item)))
            if context['specific_version']:
                version_url = '%s?version=%d' % (item_url, viewer.item.version_number)
                result.append(u' &raquo; <a href="%s">v%d</a>' % (version_url, viewer.item.version_number))
        if action_title:
            result.append(u' &raquo; %s' % action_title)
        return ''.join(result)

@register.tag
def crumbs(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return Crumbs()


