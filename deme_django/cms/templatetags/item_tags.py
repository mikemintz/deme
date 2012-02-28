#TODO completely clean up code

from django.core.urlresolvers import reverse
from django import template
from django.db.models import Q
from django.db import models
from cms.models import *
from cms.permissions import all_possible_item_abilities, all_possible_item_and_global_abilities
from cms.base_viewer import all_viewer_classes
from django.utils.http import urlquote
from django.utils.html import escape, urlize
from django.utils.encoding import force_unicode
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.timesince import timesince
from django.utils.text import capfirst, truncate_words
from django.utils import simplejson
from django.utils.safestring import mark_safe
from urlparse import urljoin
import os
import itertools

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
        global_abilities = permission_cache.global_abilities()
        return any(x.startswith(ability) for x in global_abilities)
    else:
        return permission_cache.agent_can_global(ability)


def agentcan_helper(context, ability, item, wildcard_suffix=False):
    """
    Return a boolean for whether the logged in agent has the specified ability.
    If wildcard_suffix=True, then return True if the agent has **any** ability
    whose first word is the specified ability.
    """
    agent = context['cur_agent']
    permission_cache = context['_viewer'].permission_cache
    if wildcard_suffix:
        abilities_for_item = permission_cache.item_abilities(item)
        return any(x.startswith(ability) for x in abilities_for_item)
    else:
        return permission_cache.agent_can(ability, item)


def get_viewable_name(context, item):
    """
    If the logged in agent can view the item's name, return the item's name.
    Otherwise, return a string like "GroupAgent 51".
    """
    can_view_name_field = agentcan_helper(context, 'view Item.name', item)
    return item.display_name(can_view_name_field)


def get_item_link_tag(context, item, version_number=None):
    """
    Return an <a> tag for the item with its name as the text, using
    get_viewable_name to calculate the name.
    """
    url = escape(item.get_absolute_url())
    name = escape(get_viewable_name(context, item))
    if version_number is None:
        return '<a href="%s">%s</a>' % (url, name)
    else:
        return '<a href="%s?version=%d">%s</a>' % (url, version_number, name)


def is_method_defined_and_not_inherited_in_class(method_name, class_object):
    my_fn = getattr(getattr(class_object, method_name, None), 'im_func', None)
    parent_fn = getattr(getattr(class_object.__base__, method_name, None), 'im_func', None)
    return my_fn is not None and my_fn is not parent_fn


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
def item_type_verbose_name(item_type):
    if isinstance(item_type, basestring):
        item_type = get_item_type_with_name(item_type)
    elif isinstance(item_type, Item):
        item_type = item_type.actual_item_type()
    return item_type._meta.verbose_name

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

@register.simple_tag
def module_media_url(module_name, path):
    fs_path = os.path.join(settings.MODULES_DIR, module_name, 'static', path)
    if os.path.exists(fs_path):
        path = 'modules/%s/%s' % (module_name, path)
        return urljoin(settings.MEDIA_URL, path)
    else:
        if settings.DEBUG:
            return "[Couldn't find path %s on filesystem]" % fs_path
        else:
            return '' # Fail silently for invalid paths.


class UniversalEditButton(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<UniversalEditButtonNode>"

    def render(self, context):
        item = context['item']
        if item and agentcan_helper(context, 'edit ', item, wildcard_suffix=True):
            edit_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'edit'}) + ('?version=%s' % item.version_number if context['specific_version'] else '')
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
    def __init__(self, ability, item, nodelist_true, nodelist_false):
        self.ability = template.Variable(ability)
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
        if agentcan_helper(context, ability, item):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def ifagentcan(parser, token):
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
    return IfAgentCan(bits[1], bits[2], nodelist_true, nodelist_false)

class IfAgentCanGlobal(template.Node):
    def __init__(self, ability, nodelist_true, nodelist_false):
        self.ability = template.Variable(ability)
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
        if agentcan_global_helper(context, ability):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def ifagentcanglobal(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfAgentCanGlobal(bits[1], nodelist_true, nodelist_false)

# remember this includes inactive comments, which should be displayed differently after calling this
def comment_dicts_for_item(item, version_number, context, include_recursive_collection_comments):
    max_nesting_level = int(DemeSetting.get("cms.comment_max_nesting_level") or 99999)
    permission_cache = context['_viewer'].permission_cache
    comment_subclasses = [TextComment]
    comments = []
    if include_recursive_collection_comments:
        if agentcan_global_helper(context, 'do_anything'):
            recursive_filter = None
        else:
            visible_memberships = permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members_and_me_pks_query = Item.objects.filter(active=True).filter(Q(pk=item.pk) | Q(pk__in=item.all_contained_collection_members(recursive_filter).values('pk').query)).values('pk').query
        comment_pks = RecursiveComment.objects.filter(parent__in=members_and_me_pks_query).values_list('child', flat=True)
    else:
        comment_pks = RecursiveComment.objects.filter(parent=item).values_list('child', flat=True)
    if comment_pks:
        permission_cache.filter_items('view Item.created_at', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.filter_items('view Item.creator', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.filter_items('view Item.name', Agent.objects.filter(pk__in=Comment.objects.filter(pk__in=comment_pks).values('creator_id').query))
        for comment_subclass in comment_subclasses:
            new_comments = comment_subclass.objects.filter(pk__in=comment_pks)
            related_fields = ['creator']
            if include_recursive_collection_comments:
                related_fields.extend(['item'])
            #TODO the following line breaks on Django 1.2.5 due to https://code.djangoproject.com/ticket/13781 . Uncomment it when fixed, for improved performance of displaying comments
            #new_comments = new_comments.select_related(*related_fields) 
            comments.extend(new_comments)
    comments.sort(key=lambda x: x.created_at)
    transclusions_to = Transclusion.objects.filter(to_item__in=[x.pk for x in comments])
    transclusions_to = permission_cache.filter_items('view Transclusion.from_item', transclusions_to)
    transclusions_to = permission_cache.filter_items('view Transclusion.to_item', transclusions_to)
    pk_to_comment_info = {}
    for comment in comments:
        transclusions_to_comment = [x for x in transclusions_to if x.to_item_id == comment.pk]
        comment_info = {'comment': comment, 'transclusions_to': transclusions_to_comment, 'subcomments': []}
        pk_to_comment_info[comment.pk] = comment_info
    root_node = {'subcomments': []}
    for comment in comments:
        child = pk_to_comment_info[comment.pk]
        parent = pk_to_comment_info.get(comment.item_id) or root_node
        parent['subcomments'].append(child)

    def set_max_nesting_level(child, parent, nesting_level=1):
        if nesting_level + 1 > max_nesting_level:
            parent['subcomments'].extend(child['subcomments'])
            parent['subcomments'].sort(key=lambda x: x['comment'].created_at)
            for grandchild in child['subcomments']:
                set_max_nesting_level(grandchild, parent, nesting_level + 1)
            child['subcomments'] = []
        else:
            for grandchild in child['subcomments']:
                set_max_nesting_level(grandchild, child, nesting_level + 1)
    for child in root_node['subcomments']:
        set_max_nesting_level(child, root_node)

    def set_siblings(child, parent):
        child['siblings'] = parent['subcomments']
        for grandchild in child['subcomments']:
            set_siblings(grandchild, child)
    for child in root_node['subcomments']:
        set_siblings(child, root_node)

    return root_node['subcomments'], len(comments)

class ActionsMenu(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ActionsMenuNode>"

    def render(self, context):
        result = []

        item = context['item']
        if item:
            item_name = get_viewable_name(context, item)
            version_number = item.version_number

            subscribe_url = reverse('item_type_url', kwargs={'viewer': 'subscription', 'action': 'new'}) + '?populate_item=%s' % item.pk
            edit_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'edit'}) + ('?version=%s' % version_number if context['specific_version'] else '')
            copy_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'copy'}) + ('?version=%s' % version_number if context['specific_version'] else '')
            deactivate_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'deactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
            reactivate_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'reactivate'}) + '?redirect=%s' % urlquote(context['full_path'])
            destroy_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'destroy'})
            add_authentication_method_url = reverse('item_type_url', kwargs={'viewer': 'authenticationmethod', 'action': 'new'}) + '?populate_agent=%s' % item.pk
            add_contact_method_url = reverse('item_type_url', kwargs={'viewer': 'contactmethod', 'action': 'new'}) + '?populate_agent=%s' % item.pk

        list_items = []
        if item:
            if agentcan_global_helper(context, 'create Membership'):
                list_items.append("""<li><a href="#" onclick="openCommentDialog('additemtocollection%s'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-circle-plus"></span>Add this item to collection</a></li>""" % (item.pk))
            if isinstance(item, Agent):
                if agentcan_helper(context, 'add_authentication_method', item):
                    list_items.append('<li><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-circle-plus"></span>Add authentication method</a></li>' % add_authentication_method_url)
                if agentcan_helper(context, 'add_contact_method', item):
                    list_items.append('<li><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-circle-plus"></span>Add contact method</a></li>' % add_contact_method_url)
            if not context['cur_agent'].is_anonymous():
                list_items.append("""<li><a href="#" onclick="openCommentDialog('subscribe_dialog'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-mail-closed"></span>Subscribe</a></li>""")
            if agentcan_helper(context, 'edit ', item, wildcard_suffix=True):
                list_items.append('<li><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-pencil"></span>Edit</a></li>' % edit_url)
            if agentcan_global_helper(context, 'create %s' % item.item_type_string):
                list_items.append('<li><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-copy"></span>Copy</a></li>' % copy_url)
            if item.can_be_deleted() and agentcan_helper(context, 'delete', item):
                if item.active:
                    list_items.append("""<li><a href="#" onclick="$('#deactivate_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Deactivate"><span class="ui-icon ui-icon-trash"></span>Deactivate</a></li>""")
                else:
                    list_items.append("""<li><a href="#" onclick="$('#reactivate_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Reactivate"><span class="ui-icon ui-icon-trash"></span>Reactivate</a></li>""")
                    list_items.append("""<li><a href="#" onclick="$('#destroy_dialog').dialog('open'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Destroy"><span class="ui-icon ui-icon-trash"></span>Destroy</a></li>""")
        if agentcan_global_helper(context, 'create', wildcard_suffix=True):
            list_items.append("""<li><a href="#" onclick="toggleNewItemMenu('HiddenNewItemMenu'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all" title="Create"><span class="ui-icon ui-icon-circle-plus"></span>Create</a></li>""")

        if not list_items:
            return ''

        if item:
            from cms.forms import AjaxModelChoiceField
            result.append("""
                <div id="subscribe_dialog" style="display: none;" title="Subscribe to '%s'">
                    <div style="font-size: 9pt;">Subscriptions send emails to the email contact method specified below for every new notification on this item</div>
                    <br>
                    <form method="post" action="%s?redirect=%s"> 
                        <input type="hidden" name="item" value="%s" />
                        Contact Method: %s 
                        <a href="%s" style="float: right; font-size: 9pt;">Advanced</a>
                        <input type="submit" value="Submit" />
                    </form>
                </div>
                """ % (item_name, reverse('item_type_url', kwargs={'viewer':'subscription', 'action':'dialogcreate'}), context['full_path'], item.pk, AjaxModelChoiceField(EmailContactMethod.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=['add_subscription']).widget.render('email', None, {'id':'subscribe_email_field'}), subscribe_url))

            result.append( """
            <div style="display: none;" id="additemtocollection%(item.pk)s"> 
            <form method="post" action="%(create_url)s?redirect=%(full_path)s"> 
                Collection: %(ajax_field)s 
                <input type="hidden" name="item" value="%(item.pk)s" /><br><br>
                <a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv('advancedaddtocollection%(item.pk)s'); return false;">Advanced</a>
                <div style="display: none;" id="advancedaddtocollection%(item.pk)s">
                    Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br>
                    Permission Enabled: <input name="permissionenabled" type="checkbox" />
                    <div style="float: top; font-size: 7pt;">Enable this if you want collection-wide permissions to apply to this child item</div>
                </div>
                <input type="submit" value="Submit" />
            </form>
            </div>  """ %
            {
                'item.pk': item.pk,
                'full_path': context['full_path'],
                'create_url': reverse('item_type_url', kwargs={'viewer':'membership', 'action':'itemmembercreate'}),
                'ajax_field': AjaxModelChoiceField(Collection.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('collection', None, {'id':'add_item_to_collection_collection_field'}),
             })
            
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
            """ % deactivate_url)
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
            """ % destroy_url)

        result.append("""
        <a href="#" class="fg-button fg-button-icon-right ui-widget ui-state-default ui-corner-all" id="actions_menu_link"><span class="ui-icon ui-icon-triangle-1-s"></span>------</a>
        <div style="display: none;">
            <ul style="font-size: 85%;">
        """)
        result.extend(list_items)
        result.append("""
            </ul>
        </div>
        <script type="text/javascript">
        $(function(){
            $('#actions_menu_link').fgmenu({
                content: $('#actions_menu_link').next().html(),
                showSpeed: 50,
                fixedPosition: true,
            });
            var menu = allUIMenus[allUIMenus.length - 1];
            menu.chooseItem = function(item){
                menu.kill();
                var href = $(item).attr('href');
                if (href != '#') {
                    location.href = $(item).attr('href');
                }
            };
        });
        </script>
        """)
        return '\n'.join(result)

@register.tag
def actionsmenu(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero arguments" % bits[0]
    return ActionsMenu()


class ItemDetails(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ItemDetailsNode>"

    def render(self, context):
        item = context['item']
        result = []

        result.append('<h3>Item details</h3>')
        result.append('<div>')
        result.append('<table class="twocol" cellspacing="0" style="font-size: 85%;">')

        if agentcan_helper(context, 'view Item.name', item) and item.name:
            result.append('<tr>')
            result.append('<th>Item Name:</th>')
            result.append('<td>')
            result.append(escape(item.name))
            result.append('</td>')
            result.append('</tr>')

        if agentcan_helper(context, 'view Item.description', item) and item.description:
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

        if agentcan_helper(context, 'view Item.created_at', item):
            result.append('<tr>')
            result.append('<th>Created:</th>')
            result.append('<td>')
            result.append('<span title="%s">%s ago</span>' % (item.created_at.strftime("%Y-%m-%d %H:%M:%S"), timesince(item.created_at)))
            result.append('</td>')
            result.append('</tr>')

        if agentcan_helper(context, 'view Item.creator', item):
            result.append('<tr>')
            result.append('<th>Creator:</th>')
            result.append('<td>')
            result.append(get_item_link_tag(context, item.creator))
            result.append('</td>')
            result.append('</tr>')

        for edit_action_notice in EditActionNotice.objects.filter(action_item=item, action_item_version_number=item.version_number)[0:1]:
            if agentcan_helper(context, 'view Item.created_at', item):
                result.append('<tr>')
                result.append('<th>Updated:</th>')
                result.append('<td>')
                result.append('<span title="%s">%s ago</span>' % (edit_action_notice.action_time.strftime("%Y-%m-%d %H:%M:%S"), timesince(edit_action_notice.action_time)))
                result.append('</td>')
                result.append('</tr>')

            if agentcan_helper(context, 'view Item.creator', item):
                result.append('<tr>')
                result.append('<th>Updater:</th>')
                result.append('<td>')
                result.append(get_item_link_tag(context, edit_action_notice.action_agent))
                result.append('</td>')
                result.append('</tr>')

        result.append('</table>')
        result.append('</div>')

        return '\n'.join(result)

@register.tag
def metadata_item_details(parser, token):
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
        if RecursiveComment.objects.filter(parent=item, child=transclusion.to_item).exists():
            n_replies = RecursiveComment.objects.filter(parent=transclusion.to_item).count()
            transclusion_main_html = u'<a href="#" onclick="highlight_comment(\'%d\', \'%d\', false, true); return false;" class="commentref" id="inline_transclusion_%d">%s</a>' % (transclusion.to_item.pk, transclusion.pk, transclusion.pk, escape(transclusion.to_item.display_name()))
            if n_replies > 0:
                #TODO this should point to the replies, not the first comment (ideally by just having a class name for each parent)
                transclusion_replies_html = u' <a href="#" onclick="highlight_comment(\'%d\', \'replies%d\', false, true); return false;" class="commentref" id="inline_transclusion_replies%d">%d replies</a>' % (transclusion.to_item.pk, transclusion.pk, transclusion.pk, n_replies)
            else:
                transclusion_replies_html = u''
            transclusion_html = u'%s%s' % (transclusion_main_html, transclusion_replies_html)
        else:
            transclusion_url = u'%s?crumb_filter=transclusions_to.from_item.%d' % (transclusion.to_item.get_absolute_url(), item.pk)
            transclusion_html = u'<a href="%s" class="commentref" id="inline_transclusion_%d">%s</a>' % (transclusion_url, transclusion.pk, escape(transclusion.to_item.display_name()))
        i = transclusion.from_item_index
        result.insert(0, format(item.body[i:last_i]))
        result.insert(0, transclusion_html)
        last_i = i
    result.insert(0, format(item.body[0:last_i]))
    return ''.join(result)


@register.tag
def newmemberdialog(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return NewMemberDialog()

class NewMemberDialog(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<NewMemberDialogNode>"

    def render(self, context):
        from cms.forms import AjaxModelChoiceField
        item = context['item']
        full_path = context['full_path']
        result = []

        result.append( """
            <div style="display: none;" id="addmember%(item.pk)s"> 
            <form method="post" action="%(create_url)s?redirect=%(full_path)s"> 
                Item: %(ajax_field)s 
                <input type="hidden" name="collection" value="%(item.pk)s" /><br><br>
                <a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv('advancedaddmember%(item.pk)s'); return false;">Advanced</a>
                <div style="display: none;" id="advancedaddmember%(item.pk)s">
                    Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br>
                    Permission Enabled: <input name="permissionenabled" type="checkbox" />
                    <div style="float: top; font-size: 7pt;">Enable this if you want collection-wide permissions to apply to this child item</div>
                </div>
                <input type="submit" value="Submit" />
            </form>
            </div>  """ %
            {
                'item.pk': item.pk,
                'full_path': full_path,
                'create_url': reverse('item_type_url', kwargs={'viewer':'membership', 'action':'collectioncreate'}),
                'ajax_field': AjaxModelChoiceField(Item.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('item', None, {'id':'add_item_to_collection_item_field'}),
             })

        return mark_safe('\n'.join(result))

class CalculateComments(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateCommentsNode>"

    def render(self, context):
        from cms.forms import CaptchaField 
        from cms.forms import AjaxModelChoiceField
        item = context['item']
        version_number = item.version_number
        full_path = context['original_full_path']
        try:
            default_from_contact_method_pk = EmailContactMethod.objects.filter(agent=context['cur_agent'])[:1].get().pk
        except ObjectDoesNotExist:
            default_from_contact_method_pk = None
        result = []
        def add_comment_to_div(comment_info, parents):
            comment = comment_info['comment']
            transclusions_to = []
            for node in parents + (comment_info,):
                transclusions_to.extend(node['transclusions_to'])
            relevant_transclusions = [x for x in transclusions_to if x.from_item_version_number == x.from_item.version_number]
            relevant_transclusions.sort(key=lambda x: (x.to_item_id != comment.pk, x.from_item_id == item.pk, x.from_item_index))
            for node in parents + (comment_info,):
                if node['siblings'][-1]['comment'].pk == node['comment'].pk:
                    result.append(u'<div class="subcomments_last">')
                else:
                    result.append(u'<div class="subcomments">')
            original_comment = parents[0]['comment'] if parents else comment
            result.append(u'<div id="comment%s" style="display: none;"><form method="post" action="%s?redirect=%s">'% (comment.pk, reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'accordioncreate'}), urlquote(full_path)))
            result.append(u'<p>Comment Title: <input name="title" value="Re: %s" type="text" size="25" maxlength="255" /></p><p>Body: <br><textarea name="comment_body" style="height: 200px; width: 250px;"></textarea> </p> ' % (comment.name))
            if context['cur_agent'].is_anonymous():
                result.append(u'To verify you are not a spammer, please enter in "abc123" <input name="simple_captcha" type="text" size="25" />')
            result.append(u'<div id="advancedcomment%s" style="display: none;">Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br> From Contact Method: %s</div><br> ' % (comment.pk, AjaxModelChoiceField(ContactMethod.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('new_from_contact_method', default_from_contact_method_pk)))
            result.append(u' <input type="submit" value="Submit" /> <input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" /> ' % (comment.pk, comment.version_number))
            result.append(u'<a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv(\'advancedcomment%s\'); return false;">Advanced</a> ' % (comment.pk))
            result.append(u'</form></div>')
            result.append(u'<div style="position: relative;">')
            result.append(u'<div style="position: absolute; top: 10px; left: 0; width: 20px; border-top: 2px dotted #bbb;"></div>')
            if comment_info['subcomments']:
                result.append(u'<div style="position: absolute; top: 1px; left: -10px; border: 2px solid #bbb; background: #fff; width: 15px; height: 15px; text-align: center; vertical-align: middle; font-size: 12px; font-weight: bold; cursor: pointer;" onclick="$(\'#comment_children%s\').toggle(); if ($(this).text() == \'+\') { $(this).text(\'-\') } else { $(this).text(\'+\') }">+</div>' % comment.pk)
            result.append(u'</div>')
            result.append(u'<div class="comment_header" id="right_pane_comment_%d">' % comment.pk)
            result.append(u'<div style="position: relative;"><div style="position: absolute; top: 0; left: 0;">')
            if original_comment.item.pk == item.pk:
                #TODO point to all transclusions
                transclusion = relevant_transclusions[0] if relevant_transclusions else None
                if context.get('in_textdocument_show', False):
                    if transclusion:
                        transclusion_html_id = ('' if transclusion.to_item_id == comment.pk else 'replies') + ('%d' % transclusion.pk)
                        result.append(u'<a href="#" onclick="highlight_comment(\'%s\', \'%s\', true, false); return false;">' % (comment.pk, transclusion_html_id))
                    else:
                        result.append(u'<a href="#" onclick="highlight_comment(\'%s\', null, false, false); return false;">' % comment.pk)
                else:
                    result.append(u'<a href="#" onclick="return false;">')
            else:
                itemref_url = '%s?crumb_filter=recursive_memberships_as_child.parent.%d' % (original_comment.item.get_absolute_url(), item.pk)
                result.append(u'<a href="%s">' % itemref_url)
            result.append(u'<img src="%s" />' % icon_url(original_comment.item, 24))
            result.append(u'</a>')
            result.append(u'</div></div>')
            result.append(u'<div style="margin-left: 7px; padding-left: 19px;%s">' % (' border-left: 2px dotted #bbb;' if comment_info['subcomments'] else ''))
            if comment.active:
                if agentcan_helper(context, 'view Item.name', comment):
                    comment_name = escape(truncate_words(comment.display_name(), 4))
                else:
                    comment_name = comment.display_name(can_view_name_field=False)
            else:
                comment_name = '(Inactive comment)'
            result.append(u'<a href="#" onclick="$(\'#comment_body%s\').toggle(); return false;">%s</a>' % (comment.pk, comment_name))
            if agentcan_helper(context, 'view Item.creator', comment):
                result.append('- %s' % get_item_link_tag(context, comment.creator))
            if agentcan_helper(context, 'view Item.created_at', comment):
                result.append(comment.created_at.strftime("- %Y %b %d %H:%M"))
            if comment.version_number > 1:
                result.append(' (updated)')
            result.append(u'</div>')
            result.append(u'</div>')
            for i in xrange(len(parents) + 1):
                result.append(u'</div>')
            transclusion_text = ''
            for transclusion in relevant_transclusions:
                transclusion_text += u'<div style="float: left; border: thin dotted #aaa; margin: 3px; padding: 3px;">'
                if transclusion.from_item_id == item.pk:
                    transclusion_html_id = ('' if transclusion.to_item_id == comment.pk else 'replies') + ('%d' % transclusion.pk)
                    transclusion_text += u'<a href="#" onclick="highlight_comment(\'%s\', \'%s\', true, false); return false;">%s</a>' % (comment.pk, transclusion_html_id, get_viewable_name(context, transclusion.from_item))
                else:
                    transclusion_text += u'<a href="%s?highlighted_transclusion=%s">%s</a>' % (transclusion.from_item.get_absolute_url(), transclusion.pk, get_viewable_name(context, transclusion.from_item))
                transclusion_text += u'</div>'
            transclusion_text += u'<div style="clear: both;"></div>'
            if isinstance(comment, TextComment):
                if agentcan_helper(context, 'view TextDocument.body', comment):
                    comment_body = escape(comment.body).replace('\n', '<br />')
                else:
                    comment_body = ''
            else:
                comment_body = ''
            comment_url = u'%s?crumb_filter=recursive_comments_as_child.parent.%d' % (comment.get_absolute_url(), item.pk)
            result.append(u'<div id="comment_body%d" class="comment_body" style="display: none;">' % comment.pk)
            if relevant_transclusions:
                result.append(u'<div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: thin solid #ccc;">%s</div>' % transclusion_text)
            result.append(u'<div>%s</div>' % comment_body)
            result.append(u'<div style="clear: both; font-size: smaller; margin-top: 5px; padding-top: 5px; border-top: thin solid #ccc;">')
            result.append(u'<a href="#" onclick="openCommentDialog(\'comment%s\'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-comment"></span>Respond</a>' % comment.pk)
            result.append(u'<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-newwin"></span>View comment as item</a>' % comment_url)
            result.append(u'<div style="clear: both;"></div>')
            result.append(u'</div>')
            result.append(u'</div>')
            result.append(u'<div id="comment_children%s" style="display: none;">' % comment.pk)
            for subcomment in comment_info['subcomments']:
                add_comment_to_div(subcomment, parents + (comment_info,))
            result.append(u'</div>')
        comment_dicts, n_comments = comment_dicts_for_item(item, version_number, context, isinstance(item, Collection))
        result.append("<h3>%d comment%s</h3>" % (n_comments, '' if n_comments == 1 else 's'))
        result.append(u'<div class="comment_box">')
        result.append(u'<div class="comment_box_header">')
        grid_url = u'%s?filter=recursive_comments_as_child.parent.%d' % (reverse('item_type_url', kwargs={'viewer': 'textcomment'}), item.pk)
        result.append(u'<a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-calculator"></span>Grid view</a>' % grid_url)
        if agentcan_helper(context, 'comment_on', item):
            result.append(u'<a href="#" onclick="openCommentDialog(\'comment%s\'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-comment"></span>Add comment</a>' % item.pk)
            result.append(u'<div id="comment%s" style="display: none;"><form method="post" action="%s?redirect=%s">'% (item.pk, reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'accordioncreate'}), urlquote(full_path)))
            result.append(u'<p>Comment Title: <input name="title" type="text" size="25" maxlength="255" /></p><p>Body: <br><textarea name="comment_body" style="height: 200px; width: 250px;"></textarea> ')
            if context['cur_agent'].is_anonymous():
                result.append(u'To verify you are not a spammer, please enter in "abc123" <input name="simple_captcha" type="text" size="25" />')
            result.append(u'<div id="advancedcomment%s" style="display: none;">Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br> From Contact Method: %s</div><br> ' % (item.pk, AjaxModelChoiceField(ContactMethod.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('new_from_contact_method', default_from_contact_method_pk, {'id':'commentajaxfield'})))
            result.append(u' <input type="submit" value="Submit" /> <input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" /> ' % (item.pk, item.version_number))
            result.append(u'<a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv(\'advancedcomment%s\'); return false;">Advanced</a> ' % (item.pk))
            result.append(u'</form></div>')
        result.append(u'<div style="clear: both;"></div>')
        result.append(u'</div>')
        for comment_dict in comment_dicts:
            add_comment_to_div(comment_dict, ())
        result.append("</div>")
        return '\n'.join(result)

@register.tag
def metadata_comments(parser, token):
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
        abilities = permission_cache.item_abilities(item)

        result = []
        result.append("<h3>Permissions</h3>")
        result.append("<div>")
        if agentcan_helper(context, 'view_permissions', item):
            if agentcan_helper(context, 'do_anything', item):
                item_permissions_name = 'Modify permissions'
            else:
                item_permissions_name = 'View permissions'
            item_permissions_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'itempermissions'})
            result.append("""<div><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-locked"></span>%s</a></div>""" % (item_permissions_url, item_permissions_name))
            if issubclass(item.actual_item_type(), Collection):
                if agentcan_helper(context, 'do_anything', item):
                    collection_permissions_name = 'Modify collection permissions'
                else:
                    collection_permissions_name = 'View collection permissions'
                collection_permissions_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'collectionpermissions'})
                result.append("""<div><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-locked"></span>%s</a></div>""" % (collection_permissions_url, collection_permissions_name))
        if agentcan_helper(context, 'modify_privacy_settings', item) and not agentcan_helper(context, 'do_anything', item):
            modify_privacy_url = reverse('item_url', kwargs={'viewer': item.get_default_viewer(), 'noun': item.pk, 'action': 'privacy'})
            result.append("""<div><a href="%s" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-locked"></span>Modify privacy</a></div>""" % modify_privacy_url)
        result.append('<div style="clear: both;">As user %s, you can:</div>' % get_item_link_tag(context, cur_agent))
        result.append("<ul>")
        friendly_names = [x[1] for x in POSSIBLE_ITEM_AND_GLOBAL_ABILITIES if x[0] in abilities]
        for friendly_name in friendly_names:
            result.append("<li>%s</li>" % escape(capfirst(friendly_name)))
        result.append("</ul>")
        result.append("</div>")
        return '\n'.join(result)

@register.tag
def metadata_permissions(parser, token):
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
        all_pks = []
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
            if viewable_items.count() == 0:
                continue
            viewable_items = permission_cache.filter_items('view %s.%s' % (field.model.__name__, field.field.name), viewable_items, cache_results=False)
            if field.field.name in field.model.dyadic_relations:
                target_field_name, relation_name = field.model.dyadic_relations[field.field.name]
                target_field = field.model._meta.get_field_by_name(target_field_name)[0]
                target_model = target_field.rel.to
                viewable_items = permission_cache.filter_items('view %s.%s' % (field.model.__name__, target_field_name), viewable_items, cache_results=False)
                filter_dict = {target_field.rel.related_name + "__in": list(viewable_items), 'active': True}
                viewable_items = target_model.objects.filter(**filter_dict)
                relationship_set['name'] = relation_name
                #TODO set relationship_set['field'] (or just set list_url) so it's correct for this dyadic relation
            for related_item in viewable_items:
                all_pks.append(item.pk)
            relationship_set['items'] = viewable_items
            relationship_sets.append(relationship_set)

        permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=all_pks))
        n_relationships = sum(len(x['items']) for x in relationship_sets)
        result = []
        memberOf = []
        result.append("<h3>%d related item%s</h3>" % (n_relationships, '' if n_relationships == 1 else 's'))
        result.append("<div>")
        for relationship_set in relationship_sets:
            friendly_name = capfirst(relationship_set['name']).replace('_', ' ')
            field = relationship_set['field']
            list_url = '%s?filter=%s.%d' % (reverse('item_type_url', kwargs={'viewer': field.model.__name__.lower()}), field.field.name, item.pk)
            result.append('<div><a href="%s"><b>%s</b></a></div>' % (list_url, friendly_name))
            for related_item in relationship_set['items']:
                result.append('<div>%s</div>' % get_item_link_tag(context, related_item))
                if friendly_name == "Member of":
                    memberOf.append('<div>%s</div>' % get_item_link_tag(context, related_item))             
        result.append("</div>")
        context['memberOf_box'] = mark_safe('\n'.join(memberOf))
        return '\n'.join(result)

@register.tag
def metadata_related_items(parser, token):
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
        n_versions = len(versions) + 1 if versions.exists() else 0
        result.append("<h3>%d version%s</h3>" % (n_versions, '' if n_versions == 1 else 's'))
        if versions.exists():
            result.append(u'<div>')
            edit_action_notices = EditActionNotice.objects.filter(action_item=item)
            create_action_notices = CreateActionNotice.objects.filter(action_item=item)
            action_notices = itertools.chain(edit_action_notices, create_action_notices)
            action_notice_map = {}
            for action_notice in action_notices:
                action_notice_map[action_notice.action_item_version_number] = action_notice
            for version in itertools.chain(versions, [item]):
                action_notice = action_notice_map[version.version_number]
                version_url = reverse('item_url', kwargs={'viewer': context['viewer_name'], 'action': 'show', 'noun': item.pk}) + '?version=%s' % version.version_number
                version_name = u'Version %d' % version.version_number
                version_text = u'<a href="%s">%s</a>' % (version_url, version_name)
                diff_url = reverse('item_url', kwargs={'viewer': context['viewer_name'], 'action': 'diff', 'noun': item.pk}) + '?version=%s&reference_version=%s' % (version.version_number, version.version_number - 1)
                diff_text = u'<a href="%s">(Diff)</a>' % diff_url if version.version_number > 1 else ''
                time_text = u'<span title="%s">[%s ago]</span><br />' % (action_notice.action_time.strftime("%Y-%m-%d %H:%M:%S"), timesince(action_notice.action_time))
                agent_text = u'by %s' % get_item_link_tag(context, action_notice.action_agent)
                result.append(u'<div style="font-size: 85%%; margin-bottom: 5px;">')
                if agentcan_helper(context, 'view Item.created_at', item):
                    result.append(time_text)
                result.append(version_text)
                result.append(diff_text)
                if agentcan_helper(context, 'view Item.creator', item):
                    result.append(agent_text)
                result.append(u'</div>')
            result.append(u'</div>')
        return '\n'.join(result)


@register.tag
def metadata_versions(parser, token):
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

        n_action_notices = 0
        result = []
        result.append('<div>')
        if agentcan_helper(context, 'view Item.action_notices', item):
            #TODO include recursive threads (comment replies, and items in this collection) of action notices
            action_notices = ActionNotice.objects.filter(Q(action_item=item) | Q(action_agent=item)).order_by('action_time')
            action_notice_pk_to_object_map = {}
            for action_notice_subclass in [RelationActionNotice, DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, CreateActionNotice, EditActionNotice]:
                select_related_fields = ['action_agent__name', 'action_item__name']
                if action_notice_subclass == RelationActionNotice:
                    select_related_fields.append('from_item__name')
                specific_action_notices = action_notice_subclass.objects.filter(pk__in=action_notices.values('pk').query).select_related(*select_related_fields)
                if action_notice_subclass == RelationActionNotice:
                    context['_viewer'].permission_cache.filter_items('view Item.name', Item.objects.filter(Q(pk__in=specific_action_notices.values('from_item').query)))
                for action_notice in specific_action_notices:
                    action_notice_pk_to_object_map[action_notice.pk] = action_notice
            context['_viewer'].permission_cache.filter_items('view Item.name', Item.objects.filter(Q(pk__in=action_notices.values('action_item').query) | Q(pk__in=action_notices.values('action_agent').query)))
            for action_notice in action_notices:
                action_notice = action_notice_pk_to_object_map[action_notice.pk]
                if isinstance(action_notice, RelationActionNotice):
                    if not agentcan_helper(context, 'view %s.%s' % (action_notice.from_field_model, action_notice.from_field_name), action_notice.from_item):
                        continue
                action_time_text = '<span title="%s">[%s ago]</span>' % (action_notice.action_time.strftime("%Y-%m-%d %H:%M:%S"), timesince(action_notice.action_time))
                action_agent_text = get_item_link_tag(context, action_notice.action_agent)
                if action_notice.action_item.pk == item.pk:
                    action_item_name = 'this'
                else:
                    action_item_name = get_viewable_name(context, action_notice.action_item)
                action_item_text = get_item_link_tag(context, action_notice.action_item, action_notice.action_item_version_number)
                if action_notice.action_summary:
                    action_summary_text = u' (%s)' % escape(action_notice.action_summary)
                else:
                    action_summary_text = ''
                if isinstance(action_notice, RelationActionNotice):
                    from_item_text = get_item_link_tag(context, action_notice.from_item, action_notice.from_item_version_number)
                    natural_language_representation = action_notice.natural_language_representation(context['_viewer'].permission_cache)
                    action_sentence_parts = []
                    action_sentence_parts.append(action_agent_text)
                    action_sentence_parts.append(u' made it so ')
                    for part in natural_language_representation:
                        if isinstance(part, Item):
                            if part == action_notice.from_item:
                                action_sentence_parts.append(from_item_text)
                            elif part == action_notice.action_item:
                                action_sentence_parts.append(action_item_text)
                            else:
                                action_sentence_parts.append(get_item_link_tag(context, part))
                        else:
                            action_sentence_parts.append(unicode(part))
                    action_sentence = u''.join(action_sentence_parts)
                else:
                    if isinstance(action_notice, DeactivateActionNotice):
                        action_text = 'deactivated'
                    if isinstance(action_notice, ReactivateActionNotice):
                        action_text = 'reactivated'
                    if isinstance(action_notice, DestroyActionNotice):
                        action_text = 'destroyed'
                    if isinstance(action_notice, CreateActionNotice):
                        action_text = 'created'
                    if isinstance(action_notice, EditActionNotice):
                        diff_url = reverse('item_url', kwargs={'viewer': context['viewer_name'], 'action': 'diff', 'noun': action_notice.action_item.pk}) + '?version=%s&reference_version=%s' % (action_notice.action_item_version_number, action_notice.action_item_version_number - 1)
                        action_text = '<a href="%s">edited</a>' % diff_url
                    action_sentence = '%s %s %s' % (action_agent_text, action_text, action_item_text)
                result.append(u'<div style="font-size: 85%; margin-bottom: 5px;">')
                result.append(action_time_text)
                result.append(u'<br />')
                result.append(action_sentence)
                result.append(action_summary_text)
                result.append(u'</div>')
                n_action_notices += 1
        result.append('</div>')
        result.insert(0, "<h3>%d action notice%s</h3>" % (n_action_notices, '' if n_action_notices == 1 else 's'))
        return u'\n'.join(result)

@register.tag
def metadata_action_notices(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateActionNotices()


class ListGridBox(template.Node):
    def __init__(self, item_type):
        self.item_type = template.Variable(item_type)

    def __repr__(self):
        return "<ListGridBox>"

    def render(self, context):
        viewer = context['_viewer']
        item_type = self.item_type.resolve(context)
        filter_string = viewer.request.GET.get('filter', '')
        q = viewer.request.GET.get('q', '')
        collection = viewer.request.GET.get('collection', '')
        fields = []
        possible_abilities = all_possible_item_abilities(item_type)
        for field in item_type._meta.fields:
            if isinstance(field, (models.OneToOneField, models.ManyToManyField)):
                continue
            if force_unicode(field.help_text).startswith('(Advanced)'):
                continue
            ability = 'view %s.%s' % (field.model.__name__, field.name)
            if field not in fields: # prevent duplicates due to multiple inheritance
                if ability in possible_abilities:
                    fields.append(field)
        fields.sort(key=lambda field: 0 if field.name == 'name' else 1)
        col_names = [u'%s' % capfirst(field.verbose_name) for field in fields]
        col_model = []
        for field in fields:
            field_dict = {}
            field_dict['name'] = field.name
            field_dict['index'] = field.name
            col_model.append(field_dict)
        post_data = {'fields': ','.join([field.name for field in fields]), 'filter': filter_string}
        if q:
            post_data['searchField'] = 'name'
            post_data['searchOper'] = 'cn'
            post_data['searchString'] = q
        if collection:
            post_data['collection'] = collection
        url = reverse('item_type_url', kwargs={'viewer': item_type.__name__.lower(), 'action': 'grid', 'format': 'json'})
        r = []
        r.append("""<table id="jqgrid_list"></table>""")
        r.append("""<div id="jqgrid_pager"></div>""")
        r.append("""<script type="text/javascript">""")
        r.append("""$(document).ready(function () {""")
        r.append("""  $("#jqgrid_list").jqGrid({""")
        r.append("""    url: '%s',""" % url)
        r.append("""    postData: %s,""" % simplejson.dumps(post_data))
        r.append("""    datatype: "json",""")
        r.append("""    colNames: %s,""" % simplejson.dumps(col_names))
        r.append("""    colModel: %s,""" % simplejson.dumps(col_model))
        r.append("""    rowNum: 10,""")
        r.append("""    rowList: [10,20,50,100],""")
        r.append("""    viewrecords: true,""")
        r.append("""    pager: '#jqgrid_pager',""")
        r.append("""    height: "100%",""")
        r.append("""    autowidth: true,""")
        r.append("""  });""")
        r.append("""  $("#jqgrid_list").jqGrid('navGrid','#jqgrid_pager',{edit:false,add:false,del:false});""")
        r.append("""  $("#jqgrid_list").jqGrid('navButtonAdd',"#jqgrid_pager",{caption:"Columns",title:"Choose columns",buttonicon:"ui-icon-gear",onClickButton:function(){$("#jqgrid_list").jqGrid('columnChooser',{});}});""")
        r.append("""});""")
        r.append("""</script>""")
        return '\n'.join(r)


@register.tag
def listgridbox(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one arguments" % bits[0]
    return ListGridBox(bits[1])


class SubclassFieldsBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<SubclassFieldsBox>"

    def render(self, context):
        viewer = context['_viewer']
        viewer_method_name = "%s_%s_%s" % ('item' if viewer.noun else 'type', viewer.action, viewer.format)
        viewer_where_action_defined = type(viewer)
        while viewer_where_action_defined.accepted_item_type != Item:
            if is_method_defined_and_not_inherited_in_class(viewer_method_name, viewer_where_action_defined):
                break
            viewer_where_action_defined = viewer_where_action_defined.__base__
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
            model = item._meta.get_field_by_name(field.name)[1]
            if model is None:
                model = type(item)
            if agentcan_helper(context, 'view %s.%s' % (model.__name__, field.name), item):
                result.append('<tr>')
                result.append(u'<th style="white-space: nowrap;">%s</th>' % capfirst(field.verbose_name))
                result.append('<td>')
                if isinstance(field, models.ForeignKey):
                    foreign_item = getattr(item, field.name)
                    if foreign_item:
                        result.append(get_item_link_tag(context, foreign_item))
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
        if isinstance(item, (basestring, int)):
            try:
                item = Item.objects.get(pk=item)
            except ObjectDoesNotExist:
                item = None
        if not isinstance(item, Item):
            return ''
        item = item.downcast()
        viewer = viewer_class()
        viewer.init_for_div(context['_viewer'], 'show', item, '')
        return """<div>%s</div>""" % viewer.dispatch().content


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
        return mark_safe(escape(get_viewable_name(context, item)))

@register.tag
def viewable_name(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    return ViewableName(bits[1])


class PermissionEditor(template.Node):
    def __init__(self, target, target_level, privacy_only, is_new_item):
        if target is None:
            self.target = None
        else:
            self.target = template.Variable(target)
        self.target_level = target_level
        self.privacy_only = privacy_only
        self.is_new_item = is_new_item

    def __repr__(self):
        return "<PermissionEditor>"

    def render(self, context):
        if self.target is None:
            target = None
        else:
            try:
                target = self.target.resolve(context)
            except template.VariableDoesNotExist:
                if settings.DEBUG:
                    return "[Couldn't resolve item variable]"
                else:
                    return '' # Fail silently for invalid variables.
        viewer = context['_viewer']

        if self.target_level == 'one':
            if target is None:
                possible_abilities = all_possible_item_abilities(viewer.accepted_item_type)
            else:
                possible_abilities = all_possible_item_abilities(target.actual_item_type())
        else:
            possible_abilities = all_possible_item_and_global_abilities()
        if self.privacy_only:
            possible_abilities = set([x for x in possible_abilities if x.startswith('view ')])
        possible_abilities = list((ability, capfirst(friendly_name)) for (ability, friendly_name) in POSSIBLE_ITEM_AND_GLOBAL_ABILITIES if ability in possible_abilities)


        if self.target_level == 'all':
            agent_permissions = OneToAllPermission.objects.all()
            collection_permissions = SomeToAllPermission.objects.all()
            everyone_permissions = AllToAllPermission.objects.all()
            can_edit_permissions = agentcan_global_helper(context, 'do_anything')
        else:
            if target is None or not agentcan_helper(context, 'view_permissions', target):
                agent_permissions = []
                collection_permissions = []
                everyone_permissions = []
            else:
                if self.target_level == 'one':
                    agent_permissions = target.one_to_one_permissions_as_target.all()
                    collection_permissions = target.some_to_one_permissions_as_target.all()
                    everyone_permissions = target.all_to_one_permissions_as_target.all()
                elif self.target_level == 'some':
                    agent_permissions = target.one_to_some_permissions_as_target.all()
                    collection_permissions = target.some_to_some_permissions_as_target.all()
                    everyone_permissions = target.all_to_some_permissions_as_target.all()
                else:
                    assert False
            if self.is_new_item:
                # Creator has do_anything ability when creating a new item
                creator = Agent.objects.get(pk=context['cur_agent'].pk)
                creator_permission = OneToOnePermission(source=creator, ability='do_anything', is_allowed=True)
                agent_permissions = [x for x in agent_permissions if not (x.source == creator and x.ability == 'do_anything')]
                agent_permissions.append(creator_permission)
                can_edit_permissions = True
            else:
                can_edit_permissions = agentcan_helper(context, 'do_anything', target)
        
        agents = Agent.objects.filter(pk__in=set(x.source_id for x in agent_permissions))
        collections = Collection.objects.filter(pk__in=set(x.source_id for x in collection_permissions))

        existing_permission_data = []
        for agent in agents:
            datum = {}
            datum['permission_type'] = 'agent'
            datum['name'] = get_viewable_name(context, agent)
            datum['agent_or_collection_id'] = str(agent.pk)
            datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in agent_permissions if x.source == agent]
            datum['permissions'].sort(key=lambda x: friendly_name_for_ability(x))
            existing_permission_data.append(datum)
        collection_data = []
        for collection in collections:
            datum = {}
            datum['permission_type'] = 'collection'
            datum['name'] = get_viewable_name(context, collection)
            datum['agent_or_collection_id'] = str(collection.pk)
            datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in collection_permissions if x.source == collection]
            datum['permissions'].sort(key=lambda x: friendly_name_for_ability(x))
            existing_permission_data.append(datum)
        datum = {}
        datum['permission_type'] = 'everyone'
        datum['name'] = 'Everyone'
        datum['agent_or_collection_id'] = '0'
        datum['permissions'] = [{'ability': x.ability, 'is_allowed': x.is_allowed} for x in everyone_permissions]
        datum['permissions'].sort(key=lambda x: friendly_name_for_ability(x))
        existing_permission_data.append(datum)
        existing_permission_data.sort(key=lambda x: (x['permission_type'], x['name']))

        from cms.forms import AjaxModelChoiceField
        new_agent_select_widget = AjaxModelChoiceField(Agent.objects, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_agent', None)
        new_collection_select_widget = AjaxModelChoiceField(Collection.objects, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_collection', None)
        #TODO the widgets get centered-alignment in the dialog, which looks bad

        result = """
        <script>
            var permission_counter = 1;
            var possible_abilities = %(possible_ability_javascript_array)s;
            var can_edit_permissions = %(can_edit_permissions)s;
            function add_permission_fields(wrapper, permission_type, agent_or_collection_id, is_allowed, ability) {
                if (can_edit_permissions) {
                    var remove_button = $('<a href="#" class="img_link"><img src="%(delete_img_url)s" /></a>');
                    remove_button.bind('click', function(e){wrapper.remove(); return false;});
                    wrapper.append(remove_button);
                }
                var is_allowed_checkbox = $('<input type="checkbox" id="newpermission' + permission_counter + '_is_allowed" name="newpermission' + permission_counter + '_is_allowed" value="on">');
                is_allowed_checkbox.attr('checked', is_allowed);
                is_allowed_checkbox.attr('defaultChecked', is_allowed);
                if (!can_edit_permissions) {
                    is_allowed_checkbox.attr('disabled', true);
                    is_allowed_checkbox.attr('readonly', true);
                }
                wrapper.append(is_allowed_checkbox);
                if (ability == '') {
                    var ability_select = $('<select name="newpermission' + permission_counter + '_ability">');
                    for (var i in possible_abilities) {
                        var is_selected = (possible_abilities[i][0] == ability);
                        ability_select[0].options[i] = new Option(possible_abilities[i][1], possible_abilities[i][0], is_selected, is_selected);
                    }
                    wrapper.append(ability_select);
                } else {
                    var friendly_name = ability;
                    for (var i in possible_abilities) {
                        if (possible_abilities[i][0] == ability) {
                            friendly_name = possible_abilities[i][1];
                            break;
                        }
                    }
                    wrapper.append('<label for="newpermission' + permission_counter + '_is_allowed">' + friendly_name + '</label>');
                    wrapper.append('<input type="hidden" name="newpermission' + permission_counter + '_ability" value="' + ability + '" />');
                }
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
                var row = $('<tr style="border: 2px solid #aaa">');
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
                if (can_edit_permissions) {
                    var add_button = $('<a href="#" class="img_link">');
                    add_button.append('<img src="%(new_img_url)s" /> New Permission');
                    add_button.bind('click', function(e){
                        var permission_div = $('<div>');
                        add_permission_fields(permission_div, permission_type, agent_or_collection_id, true, '');
                        permissions_cell.append(permission_div);
                        return false;
                    });
                    permissions_cell.append(add_button);
                }
                row.append(permissions_cell);
                return row;
            }

            function setup_permission_editor() {
                var existing_permission_data = %(existing_permission_data_javascript_array)s;
                rows = [];
                for (var i in existing_permission_data) {
                    var datum = existing_permission_data[i];
                    var row = add_agent_or_collection_row(datum.permission_type, datum.agent_or_collection_id, datum.name);
                    var permissions_cell = row.children('td.permissions_cell');
                    for (var j in datum.permissions) {
                        var permission = datum.permissions[j];
                        add_permission_div(permissions_cell, datum.permission_type, datum.agent_or_collection_id, permission.is_allowed, permission.ability);
                    }
                    rows.push(row);
                }
                for (var i in rows) {
                    $('#permission_table tbody').append(rows[i]);
                }

                $('#new_agent_dialog').dialog({
                    autoOpen: false,
                    close: function(event, ui){
                        $('input[name="new_agent"]').val('');
                        $('input[name="new_agent_search"]').val('');
                    },
                    buttons: {
                        'Add Agent': function(){
                            var row = add_agent_or_collection_row('agent', $('input[name="new_agent"]').val(), $('input[name="new_agent_search"]').val());
                            $('#permission_table tbody').append(row);
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
                            var row = add_agent_or_collection_row('collection', $('input[name="new_collection"]').val(), $('input[name="new_collection_search"]').val());
                            $('#permission_table tbody').append(row);
                            $(this).dialog("close");
                        },
                        'Cancel': function(){
                            $(this).dialog("close");
                        }
                    },
                });

                if (can_edit_permissions) {
                    $('#agent_and_collection_select_div').show();
                }
            }

            $(document).ready(function(){
                setup_permission_editor();
            });
        </script>

        <table id="permission_table" class="list" cellspacing="0">
            <tbody>
                <tr>
                    <th>Name</th>
                    <th>Permissions</th>
                </tr>
            </tbody>
        </table>

        <div id="new_agent_dialog" style="display: none;">
            Name of the user: %(new_agent_select_widget)s
        </div>

        <div id="new_collection_dialog" style="display: none;">
            Name of the group: %(new_collection_select_widget)s
        </div>

        <div style="display: none;" id="agent_and_collection_select_div">
            <a href="#" class="img_link" onclick="$('#new_agent_dialog').dialog('open'); return false;"><img src="%(agent_img_url)s" /> <span>Assign a Permission to a User</span></a>
            <a href="#" class="img_link" onclick="$('#new_collection_dialog').dialog('open'); return false;"><img src="%(collection_img_url)s" /> <span>Assign a Permission to a Group of Users</span></a>
        </div>
        <div style="margin-top: 10px;">
            Having trouble with permissions? Try reading the <a href="%(permissions_help_url)s">guide to using Permissions</a>
        </div>
""" % {
        'can_edit_permissions': simplejson.dumps(can_edit_permissions),
        'possible_ability_javascript_array': simplejson.dumps(possible_abilities, separators=(',',':')),
        'existing_permission_data_javascript_array': simplejson.dumps(existing_permission_data, separators=(',',':')),
        'sample_agent_url': reverse('item_url', kwargs={'viewer': 'agent', 'noun': '1'}),
        'sample_collection_url': reverse('item_url', kwargs={'viewer': 'collection', 'noun': '1'}),
        'delete_img_url': icon_url('delete', 16),
        'new_img_url': icon_url('new', 16),
        'agent_img_url': icon_url('Agent', 16),
        'collection_img_url': icon_url('Collection', 16),
        'new_agent_select_widget': AjaxModelChoiceField(Agent.objects, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_agent', None),
        'new_collection_select_widget': AjaxModelChoiceField(Collection.objects, permission_cache=viewer.permission_cache, required_abilities=[]).widget.render('new_collection', None),
        'permissions_help_url': reverse('item_type_url', kwargs={'viewer': 'item', 'action':'permissionshelp'}),
        }
        return result

@register.tag
def privacy_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    item = bits[1]
    return PermissionEditor(item, target_level='one', privacy_only=True, is_new_item=False)

@register.tag
def item_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    item = bits[1]
    return PermissionEditor(item, target_level='one', privacy_only=False, is_new_item=False)

@register.tag
def new_item_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2 and len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero or one argument" % bits[0]
    item = bits[1] if len(bits) == 2 else None
    return PermissionEditor(item, target_level='one', privacy_only=False, is_new_item=True)

@register.tag
def collection_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    item = bits[1]
    return PermissionEditor(item, target_level='some', privacy_only=False, is_new_item=False)

@register.tag
def global_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes zero arguments" % bits[0]
    item = None
    return PermissionEditor(item, target_level='all', privacy_only=False, is_new_item=False)

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
            result.append(get_item_link_tag(context, target))
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
                if not issubclass(subfilter_item_type, Item):
                    # We don't display crumbs for non-item-types
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
            result.append(u' &raquo; %s' % get_item_link_tag(context, viewer.item))
            if context['specific_version']:
                version_url = '%s?version=%d' % (viewer.item.get_absolute_url(), viewer.item.version_number)
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


class NewItemMenu(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<NewItemMenu>"

    def render(self, context):
        viewer = context['_viewer']
        sorted_item_types = sorted(all_item_types(), key=lambda x: x._meta.verbose_name_plural.lower())
        all_item_types_can_create = [x for x in sorted_item_types if agentcan_global_helper(context, 'create %s' % x.__name__)]
        if not all_item_types_can_create:
            return ''
        result = []
        result.append("""
        <script type="text/javascript">
        $(function(){
            $('#new_item_menu_link').fgmenu({
                content: $('#new_item_menu_link').next().html(),
                width: 240,
                maxHeight: 445,
                showSpeed: 50,
                backLink: true,
                topLinkText: 'Items',
                crumbDefaultText: ' ',
                //flyOut: true,
                fixedPosition: true,
            });
        });
        </script>
        <a href="#" class="fg-button fg-button-icon-right ui-widget ui-state-default ui-corner-all" id="new_item_menu_link"><span class="ui-icon ui-icon-triangle-1-s"></span>New item</a>
        <div style="display: none;">
        <ul style="font-size: 85%;">
        """)
        def add_item_type_to_menu(item_type):
            top_item_types = [item_type]
            if item_type == Item and viewer.accepted_item_type != Item:
                top_item_types.append(viewer.accepted_item_type)
            for top_item_type in top_item_types:
                if agentcan_global_helper(context, 'create %s' % top_item_type.__name__):
                    result.append(u'<li><a href="%s" class="img_link"><img src="%s" /> New %s</a></li>' % (reverse('item_type_url', kwargs={'viewer': top_item_type.__name__.lower(), 'action': 'new'}), icon_url(top_item_type, 16), top_item_type._meta.verbose_name))
            sub_item_types = [x for x in sorted_item_types if item_type in x.__bases__]
            if sub_item_types:
                result.append('<li style="border-top: thin solid #aaa; margin-top: 3px; margin-bottom: 3px;"></li>')
            for sub_item_type in sub_item_types:
                result.append('<li>')
                result.append(u'<a href="#">%s</a>' % (escape(capfirst(sub_item_type._meta.verbose_name_plural))))
                result.append('<ul>')
                add_item_type_to_menu(sub_item_type)
                result.append('</ul>')
                result.append('</li>')
        add_item_type_to_menu(Item)
        result.append("</ul></div>")
        return '\n'.join(result)

@register.tag
def new_item_menu(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return NewItemMenu()


class RecentlyViewed(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<RecentlyViewed>"

    def render(self, context):
        viewer = context['_viewer']

        if viewer.item:
            new_title = get_viewable_name(context, viewer.item)
            if context['action_title']:
                new_title += ' &raquo; %s' % context['action_title']
        else:
            if context['action_title']:
                new_title = context['action_title']
            else:
                new_title = capfirst(viewer.accepted_item_type._meta.verbose_name_plural)
        ajax_url = reverse('item_type_url', kwargs={'viewer': 'item', 'action': 'recentlyviewedbox', 'format': 'json'})
        result = """
        <div id="recently_viewed_data">
        </div>
        <script type="text/javascript">
        var num_recently_viewed_pages = 3;
        function display_recently_viewed_pages(is_initial, is_clear) {
            var data = {};
            data['num_pages'] = num_recently_viewed_pages;
            if (is_clear) {
                data['clear_history'] = true;
            }
            if (is_initial) {
                data['new_url'] = "%(new_url)s";
                data['new_title'] = "%(new_title)s";
            }
            var outer_div = $("#recently_viewed_data");
            jQuery.getJSON('%(ajax_url)s', data, function(json) {
                $("#recently_viewed_data div").remove('div');
                $.each(json, function(i, datum){
                    var url = datum[0];
                    var title = datum[1];
                    outer_div.append('<div><a href="' + url + '">' + title + '</a></div>');
                });
                outer_div.append('<div><a href="#" onclick="num_recently_viewed_pages += 10; display_recently_viewed_pages(false, false); return false;">[More]</a> <a href="#" onclick="num_recently_viewed_pages += 10; display_recently_viewed_pages(false, true); return false;">[Clear]</a></div>');
            });
        }
        $(function(){
            display_recently_viewed_pages(true, false);
        });
        </script>
        """ % {'new_url': context['full_path'], 'new_title': new_title, 'ajax_url': ajax_url}
        return result

@register.tag
def recently_viewed(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return RecentlyViewed()


class LoginMenu(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<LoginMenu>"

    def render(self, context):
        viewer = context['_viewer']
        authentication_method_viewer_classes = list(x for x in all_viewer_classes() if issubclass(x.accepted_item_type, AuthenticationMethod))
        authentication_method_viewer_classes_with_loginmenuitem = []
        for viewer_class in authentication_method_viewer_classes:
            if is_method_defined_and_not_inherited_in_class('type_loginmenuitem_html', viewer_class):
                authentication_method_viewer_classes_with_loginmenuitem.append(viewer_class)
        result = []

        if viewer.cur_agent.is_anonymous():
            login_menu_text = 'Login'
        else:
            login_menu_text = u'%s' % get_viewable_name(context, viewer.cur_agent)

        result.append("""
        <script type="text/javascript">
        $(function(){
            var menuContent = '<ul style="font-size: 85%%;">';
            $.each($('#login_menu_link').next().children().filter('li.loginmenuitem'), function(i, val){
                menuContent += '<li>' + $(val).html() + '</li>';
            });
            menuContent += '</ul>'
            $('#login_menu_link').fgmenu({
                content: menuContent,
                showSpeed: 50,
                fixedPosition: true,
            });
        });
        </script>
        <a href="#" class="fg-button fg-button-icon-right ui-widget ui-state-default ui-corner-all" id="login_menu_link"><span class="ui-icon ui-icon-triangle-1-s"></span>%s</a>
        <ul style="display: none;">
        """ % login_menu_text)
        for viewer_class in authentication_method_viewer_classes_with_loginmenuitem:
            viewer2 = viewer_class()
            if viewer.request.method == 'GET':
                query_string = 'redirect=%s' % urlquote(viewer.context['full_path'])
            else:
                query_string = ''
            viewer2.init_for_div(viewer, 'loginmenuitem', None, query_string)
            html = viewer2.dispatch().content
            result.append(html)
        result.append("</ul>")
        return '\n'.join(result)

@register.tag
def login_menu(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return LoginMenu()



class DisplayDiff(template.Node):
    def __init__(self, item, reference_version_number, new_version_number, nodelist_different, nodelist_same):
        self.item = template.Variable(item)
        self.reference_version_number = template.Variable(reference_version_number)
        self.new_version_number = template.Variable(new_version_number)
        self.nodelist_different, self.nodelist_same = nodelist_different, nodelist_same

    def __repr__(self):
        return "<DisplayDiffNode>"
        
    def render(self, context):
        try:
            item = self.item.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve item variable]"
            else:
                return '' # Fail silently for invalid variables.
        try:
            reference_version_number = self.reference_version_number.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve reference_version_number variable]"
            else:
                return '' # Fail silently for invalid variables.
        try:
            new_version_number = self.new_version_number.resolve(context)
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve new_version_number variable]"
            else:
                return '' # Fail silently for invalid variables.
        # Get a list of field differences
        diff_fields = self.calculate_field_differences(context, item, reference_version_number, new_version_number)
        # Render the underlying nodelists for each field
        result = []
        for field in diff_fields:
            context.update({'field': field})
            result.append(self.nodelist_different.render(context))
            context.pop()
        if result:
            return '\n'.join(result)
        else:
            return self.nodelist_same.render(context)

    def calculate_field_differences(self, context, item, reference_version_number, new_version_number):
        reference_item = item.actual_item_type().objects.get(pk=item.pk)
        new_item = item.actual_item_type().objects.get(pk=item.pk)
        reference_item.copy_fields_from_version(reference_version_number)
        new_item.copy_fields_from_version(new_version_number)
        result = []
        for field in item._meta.fields:
            if isinstance(field, (models.OneToOneField, models.ManyToManyField)):
                continue
            model = item._meta.get_field_by_name(field.name)[1]
            if model is None:
                model = type(item)
            if not agentcan_helper(context, 'view %s.%s' % (model.__name__, field.name), item):
                continue
            reference_value = getattr(reference_item, field.name)
            new_value = getattr(new_item, field.name)
            is_html = isinstance(item, HtmlDocument) and field.name == 'body'
            difference_html = self.display_field_difference_html(context, field, reference_value, new_value, is_html)
            if difference_html:
                field_dict = {'field': field, 'reference_value': reference_value, 'new_value': new_value, 'name': field.verbose_name, 'diff': difference_html}
                result.append(field_dict)
        return result

    def display_field_difference_html(self, context, field, reference_value, new_value, is_html):
        if reference_value == new_value:
            return None
        else:
            if isinstance(field, (models.CharField, models.TextField)):
                return self.text_field_difference(context, reference_value, new_value, is_html)
            def value_to_html(x):
                if isinstance(field, models.ForeignKey):
                    return get_item_link_tag(context, x) if x else 'None'
                elif isinstance(field, models.FileField):
                    #TODO use .url
                    return '<a href="%s%s">%s</a>' % (escape(settings.MEDIA_URL), escape(x), escape(x))
                else:
                    return urlize(escape(x)).replace('\n', '<br />')
            reference_html = value_to_html(reference_value)
            new_html = value_to_html(new_value)
            return mark_safe(u'<del style="background:#ffe6e6;">%s</del> <ins style="background: #e6ffe6;">%s</ins>' % (reference_html, new_html))
        
    def text_field_difference(self, context, reference_value, new_value, is_html):
        import diff_match_patch
        if not is_html:
            encode = lambda x: urlize(escape(x)).replace('\n', '<br />')
            reference_value = encode(reference_value)
            new_value = encode(new_value)
        dmp = diff_match_patch.diff_match_patch()
        diffs = dmp.diff_main(reference_value, new_value)
        dmp.diff_cleanupSemantic(diffs)
        html = []
        def write_fragment(start_tag, end_tag, text):
            while text:
                # Find where the next lt or gt sign is
                lt_index = text.find('<')
                gt_index = text.find('>')
                if lt_index == -1: lt_index = len(text)
                if gt_index == -1: gt_index = len(text) + 1
                # Determine whether we're currently in a tag and split the text
                if lt_index == 0 or lt_index > gt_index:
                    currently_in_tag = True
                    head = text[:gt_index+1]
                    text = text[gt_index+1:]
                else:
                    currently_in_tag = False
                    head = text[:lt_index]
                    text = text[lt_index:]
                # Write out the text, surrounded by start_tag and end_tag, unless currently_in_tag
                if currently_in_tag:
                    html.append(head)
                else:
                    html.append(start_tag)
                    html.append(head)
                    html.append(end_tag)

        for (op, text) in diffs:
            if op == dmp.DIFF_INSERT:
                start_tag = u'<ins style="background: #e6ffe6;">'
                end_tag = u'</ins>'
                write_fragment(start_tag, end_tag, text)
            elif op == dmp.DIFF_DELETE:
                start_tag = u'<del style="background: #ffe6e6;">'
                end_tag = u'</del>'
                write_fragment(start_tag, end_tag, text)
            elif op == dmp.DIFF_EQUAL:
                write_fragment('', '', text)
        result = u''.join(html)
        return mark_safe(result)

@register.tag
def displaydiff(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 4:
        raise template.TemplateSyntaxError, "%r takes three arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_different = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_same = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_same = template.NodeList()
    return DisplayDiff(bits[1], bits[2], bits[3], nodelist_different, nodelist_same)


class DefaultCreateItemTypes(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def __repr__(self):
        return "<DefaultCreateItemTypesNode>"
        
    def render(self, context):
        result = []
        item_type_names_string = DemeSetting.get("cms.default_create_item_types") or ""
        item_type_names = item_type_names_string.split(",")
        item_types = [get_item_type_with_name(x.strip(), case_sensitive=False) for x in item_type_names]
        item_types = [x for x in item_types if x]
        item_types = [x for x in item_types if agentcan_global_helper(context, 'create %s' % x.__name__)]
        for create_item_type in item_types:
            context.update({
                'create_item_type': create_item_type,
                'create_item_viewer_name': create_item_type.__name__.lower()
            })
            result.append(self.nodelist.render(context))
            context.pop()
        return mark_safe(u'\n'.join(result))

@register.tag
def defaultcreateitemtypes(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist = parser.parse((end_tag,))
    token = parser.next_token()
    return DefaultCreateItemTypes(nodelist)

