from django.core.urlresolvers import reverse
from django import template
from django.db.models import Q
import cms.models
from cms import permission_functions
from django.utils.http import urlquote
from django.utils.html import escape, urlize
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

register = template.Library()

@register.simple_tag
def show_resource_url(item, version_number=None):
    if isinstance(item, cms.models.ItemVersion):
        return reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk}) + '?version=%s' % item.version_number
    elif isinstance(item, cms.models.Item):
        if version_number is not None:
            return reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk}) + '?version=%s' % version_number
        else:
            return reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk})
    else:
        return ''

@register.filter
def icon_url(item_type, size=32):
    if item_type != 'error' and isinstance(item_type, basestring):
        try:
            item_type = [x for x in cms.models.all_models() if x.__name__ == item_type][0]
        except IndexError:
            pass

    if item_type == 'error':
        icon = 'apps/error'
    elif not isinstance(item_type, type):
        return icon_url(type(item_type), size)
    elif issubclass(item_type, cms.models.Item.VERSION):
        return icon_url(item_type.NOTVERSION, size)
    elif item_type == cms.models.Agent:
        icon = 'apps/personal'
    elif item_type == cms.models.AuthenticationMethod:
        icon = 'apps/password'
    elif item_type == cms.models.ContactMethod:
        icon = 'apps/kontact'
    elif item_type == cms.models.CustomUrl:
        icon = 'mimetypes/message'
    elif item_type == cms.models.Comment:
        icon = 'apps/filetypes'
    elif item_type == cms.models.CommentLocation:
        icon = 'apps/knotes'
    elif item_type == cms.models.Document:
        icon = 'mimetypes/empty'
    elif item_type == cms.models.DjangoTemplateDocument:
        icon = 'mimetypes/html'
    elif item_type == cms.models.EmailContactMethod:
        icon = 'apps/kmail'
    elif item_type == cms.models.Excerpt:
        icon = 'mimetypes/shellscript'
    elif item_type == cms.models.FileDocument:
        icon = 'mimetypes/misc'
    elif item_type == cms.models.Folio:
        icon = 'apps/kfm'
    elif item_type == cms.models.Group:
        icon = 'apps/Login Manager'
    elif item_type == cms.models.ImageDocument:
        icon = 'mimetypes/images'
    elif item_type == cms.models.Item:
        icon = 'apps/kblackbox'
    elif item_type == cms.models.ItemSet:
        icon = 'filesystems/folder_blue'
    elif item_type == cms.models.ItemSetMembership:
        icon = 'filesystems/folder_documents'
    elif item_type == cms.models.Permission or item_type == cms.models.GlobalPermission:
        icon = 'apps/proxy'
    elif item_type == cms.models.Person:
        icon = 'apps/access'
    elif item_type == cms.models.Role or item_type == cms.models.GlobalRole:
        icon = 'apps/lassist'
    elif item_type == cms.models.RoleAbility or item_type == cms.models.GlobalRoleAbility:
        icon = 'apps/ksysv'
    elif item_type == cms.models.Site:
        icon = 'devices/nfs_unmount'
    elif item_type == cms.models.SiteDomain:
        icon = 'devices/modem'
    elif item_type == cms.models.Subscription:
        icon = 'apps/knewsticker'
    elif item_type == cms.models.TextDocument:
        icon = 'mimetypes/txt'
    elif item_type == cms.models.ViewerRequest:
        icon = 'mimetypes/message'
    elif issubclass(item_type, cms.models.Item):
        return icon_url(item_type.__base__, size)
    else:
        return icon_url(cms.models.Item, size)
    return "/static/crystal_project/%dx%d/%s.png" % (size, size, icon)

@register.simple_tag
def list_results_navigator(item_type, itemset, search_query, trashed, offset, limit, n_results, max_pages):
    if n_results <= limit:
        return ''
    url_prefix = reverse('resource_collection', kwargs={'viewer': item_type.lower()}) + '?limit=%s&' % limit
    if search_query:
        url_prefix += 'q=%s&' % search_query
    if trashed:
        url_prefix += 'trashed=1&'
    if itemset:
        url_prefix += 'itemset=%s&' % itemset.pk
    result = []
    if offset > 0:
        new_offset = max(0, offset - limit)
        prev_button = '<a class="list_results_prev" href="%soffset=%d">&laquo; Prev</a>' % (url_prefix, new_offset)
        result.append(prev_button)
    for new_offset in xrange(max(0, offset - limit * max_pages), min(n_results - 1, offset + limit * max_pages), limit):
        if new_offset == offset:
            step_button = '<span class="list_results_highlighted">%d</span>' % (1 + new_offset / limit,)
        else:
            step_button = '<a class="list_results_step" href="%soffset=%d">%d</a>' % (url_prefix, new_offset, 1 + new_offset / limit)
        result.append(step_button)
    if offset < n_results - limit:
        new_offset = offset + limit
        next_button = '<a class="list_results_next" href="%soffset=%d">Next &raquo;</a>' % (url_prefix, new_offset)
        result.append(next_button)
    return ''.join(result)

def agentcan_global_helper(context, ability, ability_parameter):
    agent = context['cur_agent']
    global_abilities = context['_global_ability_cache'].get(agent.pk)
    if global_abilities is None:
        global_abilities = permission_functions.get_global_abilities_for_agent(agent)
        context['_global_ability_cache'][agent.pk] = global_abilities
    if ('do_everything', 'Item') in global_abilities:
        return True
    if ability_parameter is None:
        if any(x[0] == ability for x in global_abilities):
            return True
    else:
        if (ability, ability_parameter) in global_abilities:
            return True
    return False

def agentcan_helper(context, ability, ability_parameter, item):
    agent = context['cur_agent']
    if agentcan_global_helper(context, 'do_everything', 'Item'):
        return True
    if isinstance(item, cms.models.Permission) and hasattr(item, 'item') and not isinstance(item.item, cms.models.Permission) and agentcan_helper(context, 'modify_permissions', 'id', item.item):
        return True
    abilities_for_item = context['_item_ability_cache'].get((agent.pk, item.pk))
    if abilities_for_item is None:
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(agent, item)
        context['_item_ability_cache'][(agent.pk, item.pk)] = abilities_for_item
    if ability_parameter is None:
        if any(x[0] == ability for x in abilities_for_item):
            return True
    else:
        if (ability, ability_parameter) in abilities_for_item:
            return True
    return False

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
        if agentcan_helper(context, ability, ability_parameter, item):
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
        if agentcan_global_helper(context, ability, ability_parameter):
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

# remember this includes trashed comments, which should be displayed differently after calling this
def comment_dicts_for_item(item, version_number, context, include_recursive_itemset_comments):
    comment_subclasses = [cms.models.TextComment, cms.models.EditComment, cms.models.AddMemberComment, cms.models.RemoveMemberComment]
    comments = []
    if include_recursive_itemset_comments:
        if agentcan_global_helper(context, 'do_everything', 'Item'):
            recursive_filter = None
        else:
            visible_memberships = cms.models.ItemSetMembership.objects.filter(permission_functions.filter_for_agent_and_ability(context['cur_agent'], 'view', 'itemset'), permission_functions.filter_for_agent_and_ability(context['cur_agent'], 'view', 'item'))
            recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
        members_and_me_pks_query = cms.models.Item.objects.filter(Q(pk=item.pk) | Q(pk__in=item.all_contained_itemset_members(recursive_filter).values('pk').query)).values('pk').query
        for comment_subclass in comment_subclasses:
            comments.extend(comment_subclass.objects.filter(pk__in=cms.models.RecursiveCommentMembership.objects.filter(parent__in=members_and_me_pks_query).values('child').query))
    else:
        for comment_subclass in comment_subclasses:
            comments.extend(comment_subclass.objects.filter(pk__in=cms.models.RecursiveCommentMembership.objects.filter(parent=item).values('child').query))
    comments.sort(key=lambda x: x.created_at)
    pk_to_comment_info = {}
    for comment in comments:
        comment_info = {'comment': comment, 'subcomments': []}
        try:
            comment_info['comment_location'] = comment.comment_locations_as_comment.get(commented_item_version_number=version_number)
        except ObjectDoesNotExist:
            comment_info['comment_location'] = None
        pk_to_comment_info[comment.pk] = comment_info
    result = []
    for comment in comments:
        child = pk_to_comment_info[comment.pk]
        parent = pk_to_comment_info.get(comment.commented_item.pk)
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
        item_type_inheritance = context['item_type_inheritance']

        result = []

        relationships_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'relationships'}) + '?version=%s' % version_number
        permissions_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'permissions'})
        edit_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'edit'}) + '?version=%s' % version_number
        copy_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'copy'}) + '?version=%s' % version_number
        trash_version_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'trash'}) + '?version=%s' % version_number
        untrash_version_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'untrash'}) + '?version=%s' % version_number
        trash_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'trash'})
        untrash_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': 'untrash'})

        result.append('<div class="crumbs">')
        result.append('<div style="float: right;">')
        result.append('<a href="%s">Relationships</a>' % relationships_url)
        if agentcan_helper(context, 'modify_permissions', 'id', item):
            result.append('<a href="%s">Permissions</a>' % permissions_url)
        if agentcan_helper(context, 'edit', None, item):
            result.append('<a href="%s">Edit</a>' % edit_url)
        if agentcan_global_helper(context, 'create', item.item_type):
            result.append('<a href="%s">Copy</a>' % copy_url)
        if agentcan_helper(context, 'trash', 'id', item):
            if item.trashed:
                result.append('<a href="%s">Untrash</a>' % untrash_url)
            else:
                result.append('<a href="%s">Trash</a>' % trash_url)
            if item.version_trashed:
                result.append('<a href="%s">Untrash Version</a>' % untrash_version_url)
            else:
                result.append('<a href="%s">Trash Version</a>' % trash_version_url)
        result.append('</div>')
        for inherited_item_type in item_type_inheritance:
            result.append('<a href="%s">%ss</a> &raquo;' % (reverse('resource_collection', kwargs={'viewer': inherited_item_type.lower()}), inherited_item_type))
        if agentcan_helper(context, 'view', 'name', item):
            result.append('<a href="%s">%s</a>' % (show_resource_url(item), escape(item.name)))
        else:
            result.append('<a href="%s">[PERMISSION DENIED]</a>' % show_resource_url(item))
        result.append('&raquo; ')
        result.append('<select id="id_item_type" name="item_type" onchange="window.location = this.value;">')
        for other_itemversion in item.versions.all():
            version_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'entry_action': context['action']}) + '?version=%s' % other_itemversion.version_number
            result.append('<option value="%s"%s>Version %s</option>' % (version_url, ' selected="selected"' if other_itemversion.version_number == version_number else '', other_itemversion.version_number))
        result.append('</select>')
        if page_name is not None:
            result.append('&raquo; ')
            result.append(page_name)

        result.append('</div>')

        if agentcan_helper(context, 'view', 'created_at', item):
            created_at_text = item.created_at.strftime("%Y-%m-%d %H:%m")
        else:
            created_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'updated_at', item):
            updated_at_text = item.updated_at.strftime("%Y-%m-%d %H:%m")
        else:
            updated_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'creator', item):
            if agentcan_helper(context, 'view', 'name', item.creator):
                creator_text = '<a href="%s">%s</a>' % (show_resource_url(item.creator), escape(item.creator.name))
            else:
                creator_text = '<a href="%s">%s</a>' % (show_resource_url(item.creator), '[PERMISSION DENIED]')
        else:
            creator_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'updater', item):
            if agentcan_helper(context, 'view', 'name', item.updater):
                updater_text = '<a href="%s">%s</a>' % (show_resource_url(item.updater), escape(item.updater.name))
            else:
                updater_text = '<a href="%s">%s</a>' % (show_resource_url(item.updater), '[PERMISSION DENIED]')
        else:
            updater_text = '[PERMISSION DENIED]'
        result.append('<div style="font-size: 8pt;">')
        result.append('<div style="float: left;">')
        result.append('Originally created by %s on %s' % (creator_text, created_at_text))
        result.append('</div>')
        result.append('<div style="float: right;">')
        result.append('Version %s updated by %s on %s' % (version_number, updater_text, updated_at_text))
        result.append('</div>')
        result.append('<div style="clear: both;">')
        result.append('</div>')
        result.append('</div>')

        result.append('<div style="font-size: 8pt; color: #aaa; margin-bottom: 10px;">')
        if agentcan_helper(context, 'view', 'description', item):
            result.append('Description: %s' % escape(item.description))
        else:
            result.append('Description: [PERMISSION DENIED]')
        result.append('</div>')

        if item.trashed:
            result.append('<div style="color: #c00; font-weight: bold; font-size: larger;">This item is trashed</div>')
        elif item.version_trashed:
            result.append('<div style="color: #c00; font-weight: bold; font-size: larger;">This version is trashed</div>')

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


@register.simple_tag
def display_body_with_inline_comments(item, is_html):
    #TODO permissions? you should be able to see any CommentLocation, but maybe not the id of the comment it refers to
    #TODO don't insert these in bad places, like inside a tag <img <a href="....> />
    #TODO when you insert a comment in the middle of a tag like <b>hi <COMMENT></b> then it gets the style, this is bad
    if is_html:
        format = lambda text: text
    else:
        format = lambda text: urlize(escape(text)).replace('\n', '<br />')
    comment_locations = cms.models.CommentLocation.objects.filter(comment__commented_item=item, commented_item_version_number=item.version_number, commented_item_index__isnull=False, trashed=False, comment__trashed=False).order_by('-commented_item_index')
    result = []
    last_i = None
    for comment_location in comment_locations:
        i = comment_location.commented_item_index
        result.insert(0, format(item.body[i:last_i]))
        result.insert(0, '<a href="%s" class="commentref">%s</a>' % (show_resource_url(comment_location.comment), escape(comment_location.comment.name)))
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
        result.append("""<div class="comment_box_header"><a href="%s?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Add Comment</a></div>""" % (reverse('resource_collection', kwargs={'viewer': 'textcomment', 'collection_action': 'new'}), item.pk, version_number, urlquote(full_path)))
        def add_comments_to_div(comments, nesting_level=0):
            for comment_info in comments:
                comment = comment_info['comment']
                comment_location = comment_info['comment_location']
                if not agentcan_helper(context, 'view', 'commented_item', comment):
                    continue
                result.append("""<div class="comment_outer%s">""" % (' comment_outer_toplevel' if nesting_level == 0 else '',))
                result.append("""<div class="comment_header">""")
                result.append("""<div style="float: right;"><a href="%s?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Reply</a></div>""" % (reverse('resource_collection', kwargs={'viewer': 'textcomment', 'collection_action': 'new'}), comment.pk, comment.versions.latest().version_number, urlquote(full_path)))
                if agentcan_helper(context, 'view', 'name', comment):
                    result.append("""<a href="%s">%s</a>""" % (show_resource_url(comment), escape(comment.name)))
                else:
                    result.append('[PERMISSION DENIED]')
                if agentcan_helper(context, 'view', 'creator', comment):
                    if agentcan_helper(context, 'view', 'name', comment.creator):
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), escape(comment.creator.name)))
                    else:
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), 'PERMISSION DENIED'))
                else:
                    result.append('by [PERMISSION DENIED]')
                if item.pk != comment.commented_item.pk and nesting_level == 0:
                    if agentcan_helper(context, 'view', 'name', comment.commented_item):
                        result.append('for <a href="%s">%s</a>' % (show_resource_url(comment.commented_item), escape(comment.commented_item.name)))
                    else:
                        result.append('for <a href="%s">[PERMISSION DENIED]</a>' % (show_resource_url(comment.commented_item)))
                if item.pk == comment.commented_item.pk and not comment_location:
                    result.append("[INACTIVE]")
                result.append("</div>")
                if comment.trashed:
                    result.append("""<div class="comment_body">""")
                    result.append("[TRASHED]")
                    result.append("</div>")
                else:
                    result.append("""<div class="comment_description">""")
                    if agentcan_helper(context, 'view', 'description', comment):
                        result.append(escape(comment.description))
                    else:
                        result.append('[PERMISSION DENIED]')
                    result.append("</div>")
                    result.append("""<div class="comment_body">""")
                    if isinstance(comment, cms.models.TextComment):
                        if agentcan_helper(context, 'view', 'body', comment):
                            result.append(escape(comment.body).replace('\n', '<br />'))
                        else:
                            result.append('[PERMISSION DENIED]')
                    elif isinstance(comment, cms.models.EditComment):
                        result.append('Edited')
                    elif isinstance(comment, cms.models.AddMemberComment):
                        result.append('Added Member')
                    elif isinstance(comment, cms.models.RemoveMemberComment):
                        result.append('Removed Member')
                    result.append("</div>")
                add_comments_to_div(comment_info['subcomments'], nesting_level + 1)
                result.append("</div>")
        add_comments_to_div(comment_dicts_for_item(item, version_number, context, isinstance(item, cms.models.ItemSet)))
        result.append("</div>")
        return '\n'.join(result)

@register.tag
def commentbox(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CommentBox()


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
                item = cms.models.Item.objects.get(pk=item)
            except ObjectDoesNotExist:
                item = None
        if not isinstance(item, cms.models.Item):
            return ''
        item = item.downcast()
        item = get_versioned_item(item, None)
        viewer = viewer_class()
        viewer.init_from_div(context['request'], 'show', item.item_type.lower(), item, context['cur_agent'])
        return """<div style="padding: 10px; border: thick solid #aaa;">%s</div>""" % viewer.dispatch().content


@register.tag
def embed(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise template.TemplateSyntaxError, "%r takes two arguments" % bits[0]
    return EmbeddedItem(bits[1], bits[2])

