from django.core.urlresolvers import reverse
from django import template
from django.db.models import Q
from cms.models import *
from cms import permissions
from django.utils.http import urlquote
from django.utils.html import escape, urlize
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

register = template.Library()

@register.simple_tag
def show_resource_url(item, version_number=None):
    if isinstance(item, Item.VERSION):
        return reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk}) + '?version=%s' % item.version_number
    elif isinstance(item, Item):
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
            item_type = [x for x in all_models() if x.__name__ == item_type][0]
        except IndexError:
            pass

    if item_type == 'error':
        icon = 'apps/error'
    elif not isinstance(item_type, type):
        return icon_url(type(item_type), size)
    elif issubclass(item_type, Item.VERSION):
        return icon_url(item_type.NOTVERSION, size)
    elif item_type == Agent:
        icon = 'apps/personal'
    elif item_type == AuthenticationMethod:
        icon = 'apps/password'
    elif item_type == ContactMethod:
        icon = 'apps/kontact'
    elif item_type == CustomUrl:
        icon = 'mimetypes/message'
    elif item_type == Comment:
        icon = 'apps/filetypes'
    elif item_type == Document:
        icon = 'mimetypes/empty'
    elif item_type == DjangoTemplateDocument:
        icon = 'mimetypes/html'
    elif item_type == EmailContactMethod:
        icon = 'apps/kmail'
    elif item_type == Excerpt:
        icon = 'mimetypes/shellscript'
    elif item_type == FileDocument:
        icon = 'mimetypes/misc'
    elif item_type == Folio:
        icon = 'apps/kfm'
    elif item_type == Group:
        icon = 'apps/Login Manager'
    elif item_type == ImageDocument:
        icon = 'mimetypes/images'
    elif item_type == Item:
        icon = 'apps/kblackbox'
    elif item_type == Collection:
        icon = 'filesystems/folder_blue'
    elif item_type == Membership:
        icon = 'filesystems/folder_documents'
    elif item_type == Permission or item_type == GlobalPermission:
        icon = 'apps/proxy'
    elif item_type == Person:
        icon = 'apps/access'
    elif item_type == Role or item_type == GlobalRole:
        icon = 'apps/lassist'
    elif item_type == RoleAbility or item_type == GlobalRoleAbility:
        icon = 'apps/ksysv'
    elif item_type == Site:
        icon = 'devices/nfs_unmount'
    elif item_type == SiteDomain:
        icon = 'devices/modem'
    elif item_type == Subscription:
        icon = 'apps/knewsticker'
    elif item_type == TextDocument:
        icon = 'mimetypes/txt'
    elif item_type == Transclusion:
        icon = 'apps/knotes'
    elif item_type == ViewerRequest:
        icon = 'mimetypes/message'
    elif issubclass(item_type, Item):
        return icon_url(item_type.__base__, size)
    else:
        return icon_url(Item, size)
    return "/static/crystal_project/%dx%d/%s.png" % (size, size, icon)

@register.simple_tag
def list_results_navigator(item_type, collection, search_query, trashed, offset, limit, n_results, max_pages):
    if n_results <= limit:
        return ''
    url_prefix = reverse('resource_collection', kwargs={'viewer': item_type.lower()}) + '?limit=%s&' % limit
    if search_query:
        url_prefix += 'q=%s&' % search_query
    if trashed:
        url_prefix += 'trashed=1&'
    if collection:
        url_prefix += 'collection=%s&' % collection.pk
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

def agentcan_global_helper(context, ability, wildcard_suffix=False):
    agent = context['cur_agent']
    permission_cache = context['_permission_cache']
    if wildcard_suffix:
        global_abilities = permission_cache.global_abilities(agent)
        return any(x.startswith(ability) for x in global_abilities)
    else:
        return permission_cache.agent_can_global(agent, ability)

def agentcan_helper(context, ability, item, wildcard_suffix=False):
    agent = context['cur_agent']
    permission_cache = context['_permission_cache']
    if wildcard_suffix:
        abilities_for_item = permission_cache.item_abilities(agent, item)
        return any(x.startswith(ability) for x in abilities_for_item)
    else:
        return permission_cache.agent_can(agent, ability, item)

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

# remember this includes trashed comments, which should be displayed differently after calling this
def comment_dicts_for_item(item, version_number, context, include_recursive_collection_comments):
    permission_cache = context['_permission_cache']
    comment_subclasses = [TextComment, EditComment, TrashComment, UntrashComment, AddMemberComment, RemoveMemberComment]
    comments = []
    if include_recursive_collection_comments:
        if agentcan_global_helper(context, 'do_everything'):
            recursive_filter = None
        else:
            visible_memberships = Membership.objects.filter(permissions.filter_items_by_permission(context['cur_agent'], 'view item'))
            recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
        members_and_me_pks_query = Item.objects.filter(Q(pk=item.pk) | Q(pk__in=item.all_contained_collection_members(recursive_filter).values('pk').query)).values('pk').query
        comment_pks = RecursiveCommentMembership.objects.filter(parent__in=members_and_me_pks_query).values_list('child', flat=True)
    else:
        comment_pks = RecursiveCommentMembership.objects.filter(parent=item).values_list('child', flat=True)
    if comment_pks:
        permission_cache.mass_learn(context['cur_agent'], 'view created_at', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.mass_learn(context['cur_agent'], 'view creator', Comment.objects.filter(pk__in=comment_pks))
        permission_cache.mass_learn(context['cur_agent'], 'view name', Agent.objects.filter(pk__in=Comment.objects.filter(pk__in=comment_pks).values('creator_id').query))
        for comment_subclass in comment_subclasses:
            new_comments = comment_subclass.objects.filter(pk__in=comment_pks)
            related_fields = ['creator']
            if include_recursive_collection_comments:
                related_fields.extend(['commented_item'])
            if new_comments:
                if comment_subclass in [AddMemberComment, RemoveMemberComment]:
                    permission_cache.mass_learn(context['cur_agent'], 'view membership', new_comments)
                    permission_cache.mass_learn(context['cur_agent'], 'view item', Membership.objects.filter(pk__in=new_comments.values('membership_id').query))
                    permission_cache.mass_learn(context['cur_agent'], 'view name', Item.objects.filter(pk__in=Membership.objects.filter(pk__in=new_comments.values('membership_id').query).values('item_id').query))
                    related_fields.extend(['membership', 'membership__item'])
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
        parent = pk_to_comment_info.get(comment.commented_item_id)
        if parent:
            parent['subcomments'].append(child)
        else:
            result.append(child)
    return result

class EntryHeader(template.Node):
    def __init__(self, page_name):
        if page_name:
            self.page_name = template.Variable(page_name)
        else:
            self.page_name = None

    def __repr__(self):
        return "<EntryHeaderNode>"

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
        item_type_inheritance = [x.__name__ for x in reversed(context['_viewer'].item_type.mro()) if issubclass(x, Item)]

        result = []

        relationships_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'relationships'}) + '?version=%s' % version_number
        permissions_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'permissions'})
        edit_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'edit'}) + '?version=%s' % version_number
        copy_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'copy'}) + '?version=%s' % version_number
        trash_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'trash'}) + '?redirect=%s' % urlquote(context['full_path'])
        untrash_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': 'untrash'}) + '?redirect=%s' % urlquote(context['full_path'])

        result.append('<div class="crumbs">')
        result.append('<div style="float: right;">')
        result.append('<a href="%s">Relationships</a>' % relationships_url)
        if agentcan_helper(context, 'modify_permissions', item):
            result.append('<a href="%s">Permissions</a>' % permissions_url)
        if agentcan_helper(context, 'edit', item, wildcard_suffix=True):
            result.append('<a href="%s">Edit</a>' % edit_url)
        if agentcan_global_helper(context, 'create %s' % item.item_type):
            result.append('<a href="%s">Copy</a>' % copy_url)
        if agentcan_helper(context, 'trash', item):
            result.append("""<form style="display: inline;" method="post" enctype="multipart/form-data" action="%s" class="item_form">""" % (untrash_url if item.trashed else trash_url))
            result.append("""<a href="#" onclick="this.parentNode.submit(); return false;">%s</a>""" % ("Untrash" if item.trashed else "Trash"))
            result.append("""</form>""")
        result.append('</div>')
        for inherited_item_type in item_type_inheritance:
            result.append('<a href="%s">%ss</a> &raquo;' % (reverse('resource_collection', kwargs={'viewer': inherited_item_type.lower()}), inherited_item_type))
        if agentcan_helper(context, 'view name', item):
            result.append('<a href="%s">%s</a>' % (show_resource_url(item), escape(item.name)))
        else:
            result.append('<a href="%s">[PERMISSION DENIED]</a>' % show_resource_url(item))
        result.append('&raquo; ')
        result.append('<select id="id_item_type" name="item_type" onchange="window.location = this.value;">')
        for other_itemversion in item.versions.all():
            version_url = reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk, 'action': context['action']}) + '?version=%s' % other_itemversion.version_number
            result.append('<option value="%s"%s>Version %s</option>' % (version_url, ' selected="selected"' if other_itemversion.version_number == version_number else '', other_itemversion.version_number))
        result.append('</select>')
        if page_name is not None:
            result.append('&raquo; ')
            result.append(page_name)

        result.append('</div>')

        if agentcan_helper(context, 'view created_at', item):
            created_at_text = item.created_at.strftime("%Y-%m-%d %H:%m")
        else:
            created_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view updated_at', item):
            updated_at_text = item.updated_at.strftime("%Y-%m-%d %H:%m")
        else:
            updated_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view creator', item):
            if agentcan_helper(context, 'view name', item.creator):
                creator_text = '<a href="%s">%s</a>' % (show_resource_url(item.creator), escape(item.creator.name))
            else:
                creator_text = '<a href="%s">%s</a>' % (show_resource_url(item.creator), '[PERMISSION DENIED]')
        else:
            creator_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view updater', item):
            if agentcan_helper(context, 'view name', item.updater):
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
        if agentcan_helper(context, 'view description', item):
            result.append('Description: %s' % escape(item.description))
        else:
            result.append('Description: [PERMISSION DENIED]')
        result.append('</div>')

        if item.trashed:
            result.append('<div style="color: #c00; font-weight: bold; font-size: larger;">This item is trashed</div>')

        return '\n'.join(result)

@register.tag
def entryheader(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 1 or len(bits) > 2:
        raise template.TemplateSyntaxError, "%r takes zero or one arguments" % bits[0]
    if len(bits) == 2:
        page_name = bits[1]
    else:
        page_name = None
    return EntryHeader(page_name)


class CollectionHeader(template.Node):
    def __init__(self, page_name):
        if page_name:
            self.page_name = template.Variable(page_name)
        else:
            self.page_name = None

    def __repr__(self):
        return "<CollectionHeaderNode>"

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

        item_type = context['item_type']
        item_type_inheritance = [x.__name__ for x in reversed(context['_viewer'].item_type.mro()) if issubclass(x, Item)]

        result = []

        new_url = reverse('resource_collection', kwargs={'viewer': item_type.lower(), 'action': "new"})

        result.append('<div class="crumbs">')
        result.append('<div style="float: right;">')
        if agentcan_global_helper(context, 'create %s' % item_type):
            result.append('<a href="%s">New %s</a>' % (new_url, item_type))
        result.append('</div>')
        for i, inherited_item_type in enumerate(item_type_inheritance):
            link = '<a href="%s">%ss</a>' % (reverse('resource_collection', kwargs={'viewer': inherited_item_type.lower()}), inherited_item_type)
            if i > 0:
                link = '&raquo; %s' % link
            result.append(link)
        if page_name is not None:
            result.append('&raquo; ')
            result.append(page_name)

        result.append('</div>')

        return '\n'.join(result)

@register.tag
def collectionheader(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 1 or len(bits) > 2:
        raise template.TemplateSyntaxError, "%r takes zero or one arguments" % bits[0]
    if len(bits) == 2:
        page_name = bits[1]
    else:
        page_name = None
    return CollectionHeader(page_name)


@register.simple_tag
def display_body_with_inline_transclusions(item, is_html):
    #TODO permissions? you should be able to see any Transclusion, but maybe not the id of the comment it refers to
    #TODO don't insert these in bad places, like inside a tag <img <a href="....> />
    #TODO when you insert a transclusion in the middle of a tag like <b>hi <COMMENT></b> then it gets the style, this is bad
    if is_html:
        format = lambda text: text
    else:
        format = lambda text: urlize(escape(text)).replace('\n', '<br />')
    transclusions = Transclusion.objects.filter(from_item=item, from_item_version_number=item.version_number, trashed=False, to_item__trashed=False).order_by('-from_item_index')
    result = []
    last_i = None
    for transclusion in transclusions:
        i = transclusion.from_item_index
        result.insert(0, format(item.body[i:last_i]))
        result.insert(0, '<a href="%s" class="commentref">%s</a>' % (show_resource_url(transclusion.to_item), escape(transclusion.to_item.name)))
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
            result.append("""<a href="%s?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Add Comment</a>""" % (reverse('resource_collection', kwargs={'viewer': 'textcomment', 'action': 'new'}), item.pk, version_number, urlquote(full_path)))
        result.append("""</div>""")
        def add_comments_to_div(comments, nesting_level=0):
            for comment_info in comments:
                comment = comment_info['comment']
                result.append("""<div class="comment_outer%s">""" % (' comment_outer_toplevel' if nesting_level == 0 else '',))
                result.append("""<div class="comment_header">""")
                result.append("""<div style="float: right;"><a href="%s?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Reply</a></div>""" % (reverse('resource_collection', kwargs={'viewer': 'textcomment', 'action': 'new'}), comment.pk, comment.version_number, urlquote(full_path)))
                if isinstance(comment, EditComment):
                    comment_name = '[Edited]'
                elif isinstance(comment, TrashComment):
                    comment_name = '[Trashed]'
                elif isinstance(comment, UntrashComment):
                    comment_name = '[Untrashed]'
                elif isinstance(comment, AddMemberComment):
                    comment_name = '[Added Member]'
                elif isinstance(comment, RemoveMemberComment):
                    comment_name = '[Removed Member]'
                else:
                    if agentcan_helper(context, 'view name', comment):
                        comment_name = escape(comment.name)
                    else:
                        comment_name = '[PERMISSION DENIED]'
                result.append("""<a href="%s">%s</a>""" % (show_resource_url(comment), comment_name))
                if agentcan_helper(context, 'view creator', comment):
                    if agentcan_helper(context, 'view name', comment.creator):
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), escape(comment.creator.name)))
                    else:
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), 'PERMISSION DENIED'))
                else:
                    result.append('by [PERMISSION DENIED]')
                if item.pk != comment.commented_item_id and nesting_level == 0:
                    if agentcan_helper(context, 'view name', comment.commented_item):
                        result.append('for <a href="%s">%s</a>' % (show_resource_url(comment.commented_item), escape(comment.commented_item.name)))
                    else:
                        result.append('for <a href="%s">[PERMISSION DENIED]</a>' % (show_resource_url(comment.commented_item)))
                if agentcan_helper(context, 'view created_at', comment):
                    from django.utils.timesince import timesince
                    result.append('%s ago' % timesince(comment.created_at))
                else:
                    result.append('at [PERMISSION DENIED]')
                result.append("</div>")
                if comment.trashed:
                    comment_description = ''
                    comment_body = '[TRASHED]'
                else:
                    if isinstance(comment, TextComment):
                        if agentcan_helper(context, 'view body', comment):
                            comment_body = escape(comment.body).replace('\n', '<br />')
                        else:
                            comment_body = '[PERMISSION DENIED]'
                        if agentcan_helper(context, 'view description', comment):
                            comment_description = escape(comment.description)
                        else:
                            comment_description = '[PERMISSION DENIED]'
                    elif isinstance(comment, EditComment):
                        comment_description = ''
                        comment_body = ''
                    elif isinstance(comment, TrashComment):
                        comment_description = ''
                        comment_body = ''
                    elif isinstance(comment, UntrashComment):
                        comment_description = ''
                        comment_body = ''
                    elif isinstance(comment, AddMemberComment):
                        comment_description = ''
                        if agentcan_helper(context, 'view membership', comment):
                            if agentcan_helper(context, 'view item', comment.membership):
                                if agentcan_helper(context, 'view name', comment.membership.item):
                                    comment_body = '<a href="%s">%s</a> with <a href="%s">Membership %s</a>' % (show_resource_url(comment.membership.item), escape(comment.membership.item.name), show_resource_url(comment.membership), comment.membership.pk)
                                else:
                                    comment_body = '<a href="%s">Item %s</a> with <a href="%s">Membership %s</a>' % (show_resource_url(comment.membership.item), comment.membership.item.pk, show_resource_url(comment.membership), comment.membership.pk)
                            else:
                                comment_body = '<a href="%s">Membership %s</a>' % (show_resource_url(comment.membership), comment.membership.pk)
                        else:
                            comment_body = ''
                    elif isinstance(comment, RemoveMemberComment):
                        comment_description = ''
                        if agentcan_helper(context, 'view membership', comment):
                            if agentcan_helper(context, 'view item', comment.membership):
                                if agentcan_helper(context, 'view name', comment.membership.item):
                                    comment_body = '<a href="%s">%s</a> with <a href="%s">Membership %s</a>' % (show_resource_url(comment.membership.item), escape(comment.membership.item.name), show_resource_url(comment.membership), comment.membership.pk)
                                else:
                                    comment_body = '<a href="%s">Item %s</a> with <a href="%s">Membership %s</a>' % (show_resource_url(comment.membership.item), comment.membership.item.pk, show_resource_url(comment.membership), comment.membership.pk)
                            else:
                                comment_body = '<a href="%s">Membership %s</a>' % (show_resource_url(comment.membership), comment.membership.pk)
                        else:
                            comment_body = ''
                    else:
                        comment_description = ''
                        comment_body = ''
                result.append("""<div class="comment_description">%s</div><div class="comment_body">%s</div>""" % (comment_description, comment_body))
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

