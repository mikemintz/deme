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
from django.utils.text import capfirst

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
    permission_cache = context['_permission_cache']
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
    permission_cache = context['_permission_cache']
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
        ImageDocument:          'mimetypes/images',
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
    return "/static/crystal_project/%dx%d/%s.png" % (size, size, icon)

@register.simple_tag
def list_results_navigator(viewer_name, collection, search_query, active, offset, limit, n_results, max_pages):
    """
    Make an HTML pagination navigator (page number links with prev and next
    links on both sides).
    
    The prev link will have class="list_results_prev". The next link will have
    class="list_results_next". Each page number link will have
    class="list_results_step". The current page number will be in a span with
    class="list_results_highlighted".
    """
    if n_results <= limit:
        return ''
    url_prefix = reverse('item_type_url', kwargs={'viewer': viewer_name}) + '?limit=%s&' % limit
    if search_query:
        url_prefix += 'q=%s&' % search_query
    if not active:
        url_prefix += 'active=0&'
    if collection:
        url_prefix += 'collection=%s&' % collection.pk
    result = []
    # Add a prev link
    if offset > 0:
        new_offset = max(0, offset - limit)
        prev_text = _('Prev')
        link = u'<a class="list_results_prev" href="%soffset=%d">&laquo; %s</a>' % (url_prefix, new_offset, prev_text)
        result.append(link)
    # Add the page links
    for new_offset in xrange(max(0, offset - limit * max_pages), min(n_results - 1, offset + limit * max_pages), limit):
        if new_offset == offset:
            link = '<span class="list_results_highlighted">%d</span>' % (1 + new_offset / limit,)
        else:
            link = '<a class="list_results_step" href="%soffset=%d">%d</a>' % (url_prefix, new_offset, 1 + new_offset / limit)
        result.append(link)
    # Add a next link
    if offset + limit < n_results:
        new_offset = offset + limit
        next_text = _('Next')
        link = u'<a class="list_results_next" href="%soffset=%d">%s &raquo;</a>' % (url_prefix, new_offset, next_text)
        result.append(link)
    return ''.join(result)

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
    permission_cache = context['_permission_cache']
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
    result = []
    for comment in comments:
        child = pk_to_comment_info[comment.pk]
        parent = pk_to_comment_info.get(comment.item_id)
        if parent:
            parent['subcomments'].append(child)
        else:
            result.append(child)
    return result

class ItemHeader(template.Node):
    def __init__(self, page_name):
        if page_name:
            self.page_name = template.Variable(page_name)
        else:
            self.page_name = None

    def __repr__(self):
        return "<ItemHeaderNode>"

    def render(self, context):
        if self.page_name is None:
            page_name = None
        else:
            try:
                page_name = self.page_name.resolve(context)
            except template.VariableDoesNotExist:
                if settings.DEBUG:
                    return "[Couldn't resolve page_name variable]"
                else:
                    return '' # Fail silently for invalid variables.

        item = context['item']
        version_number = item.version_number
        cur_item_type = context['_viewer'].accepted_item_type
        item_type_inheritance = []
        while issubclass(cur_item_type, Item):
            item_type_inheritance.insert(0, cur_item_type)
            cur_item_type = cur_item_type.__base__

        result = []

        history_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'history'}) + '?version=%s' % version_number
        subscribe_url = reverse('item_type_url', kwargs={'viewer': 'subscription', 'action': 'new'}) + '?item=%s' % item.pk
        relationships_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'relationships'}) + '?version=%s' % version_number
        permissions_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'itempermissions'})
        edit_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'edit'}) + '?version=%s' % version_number
        copy_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'copy'}) + '?version=%s' % version_number
        deactivate_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'deactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
        reactivate_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'reactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
        destroy_url = reverse('item_url', kwargs={'viewer': item.item_type_string.lower(), 'noun': item.pk, 'action': 'destroy'}) + '?redirect=%s' % urlquote(context['full_path'])
        add_authentication_method_url = reverse('item_type_url', kwargs={'viewer': 'authenticationmethod', 'action': 'new'}) + '?agent=%s' % item.pk
        add_contact_method_url = reverse('item_type_url', kwargs={'viewer': 'contactmethod', 'action': 'new'}) + '?agent=%s' % item.pk

        result.append('<div class="crumbs">')

        result.append('<div style="float: right; margin-bottom: 5px;">')
        if isinstance(item, Agent):
            if agentcan_helper(context, 'add_authentication_method', item):
                result.append('<a href="%s" class="img_button"><img src="%s" /><span>Add authentication method</span></a>' % (add_authentication_method_url, icon_url('AuthenticationMethod', 16)))
            if agentcan_helper(context, 'add_contact_method', item):
                result.append('<a href="%s" class="img_button"><img src="%s" /><span>Add contact method</span></a>' % (add_contact_method_url, icon_url('ContactMethod', 16)))
        result.append('<a href="%s" class="img_button"><img src="%s" /><span>History</span></a>' % (history_url, icon_url('history', 16)))
        result.append('<a href="%s" class="img_button"><img src="%s" /><span>Subscribe</span></a>' % (subscribe_url, icon_url('subscribe', 16)))
        result.append('<a href="%s" class="img_button"><img src="%s" /><span>Relationships</span></a>' % (relationships_url, icon_url('relationships', 16)))
        if agentcan_helper(context, 'do_anything', item):
            result.append('<a href="%s" class="img_button"><img src="%s" /><span>Permissions</span></a>' % (permissions_url, icon_url('permissions', 16)))
        if agentcan_helper(context, 'edit', item, wildcard_suffix=True):
            result.append('<a href="%s" class="img_button"><img src="%s" /><span>Edit</span></a>' % (edit_url, icon_url('edit', 16)))
        if agentcan_global_helper(context, 'create %s' % item.item_type_string):
            result.append('<a href="%s" class="img_button"><img src="%s" /><span>Copy</span></a>' % (copy_url, icon_url('copy', 16)))
        if item.can_be_deleted() and agentcan_helper(context, 'delete', item):
            result.append("""<form style="display: inline;" method="post" enctype="multipart/form-data" action="%s" class="item_form">""" % (deactivate_url if item.active else reactivate_url))
            result.append("""<a href="#" onclick="if (confirm('Are you sure you want to %s this item?'))this.parentNode.submit(); return false;" class="img_button"><img src="%s" /><span>%s</span></a>""" % ("deactivate" if item.active else "reactivate", icon_url('delete', 16), "Deactivate" if item.active else "Reactivate"))
            result.append("""</form>""")
            if not item.active:
                result.append("""<form style="display: inline;" method="post" enctype="multipart/form-data" action="%s" class="item_form">""" % destroy_url)
                result.append("""<a href="#" onclick="if (confirm('Are you sure you want to destroy this item?')) this.parentNode.submit(); return false;" class="img_button"><img src="%s" /><span>%s</span></a>""" % (icon_url('delete', 16), "Destroy"))
                result.append("""</form>""")
        result.append('</div>')

        result.append('<div style="float: left; margin-bottom: 5px; margin-top: 5px;">')
        for inherited_item_type in item_type_inheritance:
            result.append(u'<a href="%s" class="img_link"><img src="%s" /><span>%s</span></a> &raquo;' % (reverse('item_type_url', kwargs={'viewer': inherited_item_type.__name__.lower()}), icon_url(inherited_item_type, 16), capfirst(inherited_item_type._meta.verbose_name_plural)))
        result.append('<a href="%s" class="img_link"><img src="%s" /><span>%s</span></a>' % (item.get_absolute_url(), icon_url(item.item_type_string, 16), escape(get_viewable_name(context, item))))
        if context['specific_version']:
            result.append('&raquo; ')
            result.append('v%d' % item.version_number)
        if page_name is not None:
            result.append('&raquo; ')
            result.append(page_name)
        result.append('</div>')

        result.append('<div style="clear: both;">')
        result.append('</div>')

        result.append('</div>')

        if agentcan_helper(context, 'view created_at', item):
            created_at_text = '<span title="%s">%s ago</span>' % (item.created_at.strftime("%Y-%m-%d %H:%M:%S"), timesince(item.created_at))
        else:
            created_at_text = ''
        if agentcan_helper(context, 'view creator', item):
            creator_text = 'by <a href="%s">%s</a>' % (item.creator.get_absolute_url(), escape(get_viewable_name(context, item.creator)))
        else:
            creator_text = ''
        result.append('<div style="font-size: 8pt;">')
        result.append('<div style="float: left;">')
        result.append(u'%s' % capfirst(item.actual_item_type()._meta.verbose_name))
        if creator_text or created_at_text:
            result.append('originally created %s %s' % (creator_text, created_at_text))
        result.append('</div>')
        result.append('<div style="clear: both;">')
        result.append('</div>')
        result.append('</div>')

        result.append('<div style="font-size: 8pt; color: #aaa; margin-bottom: 10px;">')
        if agentcan_helper(context, 'view description', item) and item.description.strip():
            result.append('Description: %s' % escape(item.description))
        result.append('</div>')

        if item.destroyed:
            result.append('<div style="color: #c00; font-weight: bold; font-size: larger;">This item is destroyed</div>')
        elif not item.active:
            result.append('<div style="color: #c00; font-weight: bold; font-size: larger;">This item is inactive</div>')

        return '\n'.join(result)

@register.tag
def itemheader(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 1 or len(bits) > 2:
        raise template.TemplateSyntaxError, "%r takes zero or one arguments" % bits[0]
    if len(bits) == 2:
        page_name = bits[1]
    else:
        page_name = None
    return ItemHeader(page_name)


class TypeHeader(template.Node):
    def __init__(self, page_name):
        if page_name:
            self.page_name = template.Variable(page_name)
        else:
            self.page_name = None

    def __repr__(self):
        return "<TypeHeaderNode>"

    def render(self, context):
        if self.page_name is None:
            page_name = None
        else:
            try:
                page_name = self.page_name.resolve(context)
            except template.VariableDoesNotExist:
                if settings.DEBUG:
                    return "[Couldn't resolve page_name variable]"
                else:
                    return '' # Fail silently for invalid variables.

        item_type = context['_viewer'].accepted_item_type

        cur_item_type = context['_viewer'].accepted_item_type
        item_type_inheritance = []
        while issubclass(cur_item_type, Item):
            item_type_inheritance.insert(0, cur_item_type)
            cur_item_type = cur_item_type.__base__

        result = []

        new_url = reverse('item_type_url', kwargs={'viewer': item_type.__name__.lower(), 'action': "new"})

        result.append('<div class="crumbs">')
        result.append('<div style="float: right; margin-bottom: 5px;">')
        if agentcan_global_helper(context, 'create %s' % item_type.__name__):
            result.append(u'<a href="%s" class="img_button"><img src="%s" /><span>New %s</span></a>' % (new_url, icon_url('new', 16), item_type._meta.verbose_name))
        result.append('</div>')

        result.append('<div style="float: left; margin-bottom: 5px; margin-top: 5px;">')
        for i, inherited_item_type in enumerate(item_type_inheritance):
            link = u'<a href="%s" class="img_link"><img src="%s" /><span>%s</span></a>' % (reverse('item_type_url', kwargs={'viewer': inherited_item_type.__name__.lower()}), icon_url(inherited_item_type, 16), capfirst(inherited_item_type._meta.verbose_name_plural))
            if i > 0:
                link = '&raquo; %s' % link
            result.append(link)
        if page_name is not None:
            result.append('&raquo; ')
            result.append(page_name)
        result.append('</div>')

        result.append('<div style="clear: both;">')
        result.append('</div>')

        result.append('</div>')

        return '\n'.join(result)

@register.tag
def typeheader(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 1 or len(bits) > 2:
        raise template.TemplateSyntaxError, "%r takes zero or one arguments" % bits[0]
    if len(bits) == 2:
        page_name = bits[1]
    else:
        page_name = None
    return TypeHeader(page_name)


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


class CommentBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CommentBoxNode>"

    def render(self, context):
        item = context['item']
        version_number = item.version_number
        full_path = context['full_path']

        result = []
        result.append("""<div class="comment_box">""")
        result.append("""<div class="comment_box_header">""")
        if agentcan_helper(context, 'comment_on', item):
            result.append("""<a href="%s?item=%s&item_version_number=%s&redirect=%s">[+] Add Comment</a>""" % (reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'new'}), item.pk, version_number, urlquote(full_path)))
        result.append("""</div>""")
        def add_comments_to_div(comments, nesting_level=0):
            for comment_info in comments:
                comment = comment_info['comment']
                result.append("""<div class="comment_outer%s">""" % (' comment_outer_toplevel' if nesting_level == 0 else '',))
                result.append("""<div class="comment_header">""")
                result.append("""<div style="float: right;"><a href="%s?item=%s&item_version_number=%s&redirect=%s">[+] Reply</a></div>""" % (reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'new'}), comment.pk, comment.version_number, urlquote(full_path)))
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
                result.append("""<div class="comment_body">%s</div>""" % comment_body)
                add_comments_to_div(comment_info['subcomments'], nesting_level + 1)
                result.append("</div>")
        comment_dicts = comment_dicts_for_item(item, version_number, context, isinstance(item, Collection))
        add_comments_to_div(comment_dicts)
        result.append("</div>")

        return '\n'.join(result)

@register.tag
def commentbox(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CommentBox()


class ActionNoticeBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ActionNoticeBoxNode>"

    def render(self, context):
        item = context['item']
        version_number = item.version_number
        full_path = context['full_path']

        result = []
        if agentcan_helper(context, 'view_action_notices', item):
            #TODO include recursive threads (comment replies, and items in this collection) of action notices
            result.append(u"<div><b>Action Notices</b></div>")
            result.append(u'<table class="list">')
            result.append(u'<tr><th>Date/Time</th><th>Agent</th><th>Action</th><th>Item</th><th>Description</th></tr>')
            action_notices = ActionNotice.objects.filter(Q(item=item) | Q(creator=item)).order_by('created_at')
            action_notice_pk_to_object_map = {}
            for action_notice_subclass in [RelationActionNotice, DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, CreateActionNotice, EditActionNotice]:
                specific_action_notices = action_notice_subclass.objects.filter(pk__in=action_notices.values('pk').query)
                if action_notice_subclass == RelationActionNotice:
                    context['_permission_cache'].filter_items(context['cur_agent'], 'view name', Item.objects.filter(Q(pk__in=specific_action_notices.values('from_item').query)))
                for action_notice in specific_action_notices:
                    action_notice_pk_to_object_map[action_notice.pk] = action_notice
            context['_permission_cache'].filter_items(context['cur_agent'], 'view name', Item.objects.filter(Q(pk__in=action_notices.values('item').query) | Q(pk__in=action_notices.values('creator').query)))
            for action_notice in action_notices:
                action_notice = action_notice_pk_to_object_map[action_notice.pk]
                if isinstance(action_notice, RelationActionNotice):
                    if not agentcan_helper(context, 'view %s' % action_notice.from_field_name, action_notice.from_item):
                        continue
                created_at_text = '<span title="%s">%s ago</span>' % (action_notice.created_at.strftime("%Y-%m-%d %H:%M:%S"), timesince(action_notice.created_at))
                creator_name = get_viewable_name(context, action_notice.creator)
                agent_text = u'<a href="%s">%s</a>' % (escape(action_notice.creator.get_absolute_url()), escape(creator_name))
                item_name = get_viewable_name(context, action_notice.item)
                item_text = u'<a href="%s">%s</a>' % (escape(action_notice.item.get_absolute_url() + '?version=%d' % action_notice.item_version_number), escape(item_name))
                description_text = action_notice.description
                if isinstance(action_notice, RelationActionNotice):
                    from_item_name = get_viewable_name(context, action_notice.from_item)
                    from_item_text = u'<a href="%s">%s</a>' % (escape(action_notice.from_item.get_absolute_url() + '?version=%d' % action_notice.from_item_version_number), escape(from_item_name))
                    if action_notice.relation_added:
                        action_text = u"Set the %s of %s to" % (action_notice.from_field_name, from_item_text)
                    else:
                        action_text = u"Unset the %s of %s from" % (action_notice.from_field_name, from_item_text)
                if isinstance(action_notice, DeactivateActionNotice):
                    action_text = 'Deactivated'
                if isinstance(action_notice, ReactivateActionNotice):
                    action_text = 'Reactivated'
                if isinstance(action_notice, DestroyActionNotice):
                    action_text = 'Destroyed'
                if isinstance(action_notice, CreateActionNotice):
                    action_text = 'Created'
                if isinstance(action_notice, EditActionNotice):
                    action_text = 'Edited'
                result.append(u"<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (created_at_text, agent_text, action_text, item_text, description_text))
            result.append(u"</table>")

        return '\n'.join(result)

@register.tag
def actionnoticebox(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return ActionNoticeBox()


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
        for field in item._meta.fields:
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
                        result.append('<a href="/static/media/%s">%s</a>' % (escape(data), escape(data)))
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
        from cms.views import get_viewer_class_for_viewer_name, get_versioned_item
        viewer_name = self.viewer_name.resolve(context)
        viewer_class = get_viewer_class_for_viewer_name(viewer_name)
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
        item = get_versioned_item(item, None)
        viewer = viewer_class()
        viewer.init_from_div(context['_viewer'], 'show', item)
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

