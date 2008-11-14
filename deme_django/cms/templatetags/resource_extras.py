from django import template
import cms.models
from cms import permission_functions
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.simple_tag
def show_resource_url(item):
    if isinstance(item, cms.models.ItemVersion):
        return '/resource/%s/%s?version=%s' % (item.item_type.lower(), item.current_item_id, item.version_number)
    elif isinstance(item, cms.models.Item):
        return '/resource/%s/%s' % (item.item_type.lower(), item.pk)
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
    elif item_type == cms.models.Account:
        icon = 'apps/password'
    elif item_type == cms.models.Agent:
        icon = 'apps/personal'
    elif item_type == cms.models.GroupMembership:
        icon = 'apps/katomic'
    elif item_type == cms.models.CustomUrl:
        icon = 'mimetypes/message'
    elif item_type == cms.models.Relationship:
        icon = 'apps/proxy'
    elif item_type == cms.models.Comment:
        icon = 'apps/filetypes'
    elif item_type == cms.models.Document:
        icon = 'mimetypes/empty'
    elif item_type == cms.models.DjangoTemplateDocument:
        icon = 'mimetypes/html'
    elif item_type == cms.models.Folio:
        icon = 'apps/kfm'
    elif item_type == cms.models.Group:
        icon = 'apps/Login Manager'
    elif item_type == cms.models.Item:
        icon = 'apps/kblackbox'
    elif item_type == cms.models.ItemSet:
        icon = 'filesystems/folder_blue'
    elif item_type == cms.models.ItemSetMembership:
        icon = 'filesystems/folder_documents'
    elif item_type == cms.models.ViewerRequest:
        icon = 'mimetypes/message'
    elif item_type == cms.models.FileDocument:
        icon = 'mimetypes/misc'
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
    elif item_type == cms.models.TextDocument:
        icon = 'mimetypes/txt'
    elif issubclass(item_type, cms.models.Item):
        return icon_url(item_type.__base__, size)
    else:
        return icon_url(cms.models.Item, size)
    return "/static/crystal_project/%dx%d/%s.png" % (size, size, icon)

@register.simple_tag
def list_results_navigator(item_type, itemset, search_query, trashed, offset, limit, n_results, max_pages):
    url_prefix = '/resource/%s/list?limit=%d&' % (item_type.lower(), limit)
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
            return 'invalid 232593713' # TODO what should i do here?
        try:
            ability = self.ability.resolve(context)
        except template.VariableDoesNotExist:
            return 'invalid 232593714' # TODO what should i do here?
        try:
            ability_parameter = self.ability_parameter.resolve(context)
        except template.VariableDoesNotExist:
            return 'invalid 232593715' # TODO what should i do here?
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
            return 'invalid 232593738' # TODO what should i do here?
        try:
            ability_parameter = self.ability_parameter.resolve(context)
        except template.VariableDoesNotExist:
            return 'invalid 232593752' # TODO what should i do here?
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

def comment_dicts_for_item(item, itemversion):
    comments = item.comments_as_item.order_by('updated_at')
    result = []
    for comment in comments:
        comment_info = {}
        comment_info['comment'] = comment
        try:
            comment_info['comment_location'] = comment.comment_locations_as_comment.get(commented_item_version_number=itemversion.version_number)
        except ObjectDoesNotExist:
            comment_info['comment_location'] = None
        comment_info['subcomments'] = comment_dicts_for_item(comment, comment.versions.latest())
        result.append(comment_info)
    return result

class ItemHeader(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ItemHeaderNode>"

    def render(self, context):
        item = context['item']
        itemversion = context['itemversion']
        item_type_inheritance = context['item_type_inheritance']

        result = []

        result.append("""<div class="crumbs">""")
        result.append("""<div style="float: right;">""")
        result.append("""<a href="/resource/%s/%s/relationships?version=%s">Relationships</a>""" % (item.item_type.lower(), item.pk, itemversion.version_number))
        if agentcan_helper(context, 'modify_permissions', 'id', item):
            result.append("""<a href="/resource/%s/%s/permissions">Permissions</a>""" % (item.item_type.lower(), item.pk))
        if agentcan_helper(context, 'edit', None, item):
            result.append("""<a href="/resource/%s/%s/edit?version=%s">Edit</a>""" % (item.item_type.lower(), item.pk, itemversion.version_number))
        if agentcan_global_helper(context, 'create', None):
            result.append("""<a href="/resource/%s/%s/copy?version=%s">Copy</a>""" % (item.item_type.lower(), item.pk, itemversion.version_number))
        if agentcan_helper(context, 'trash', 'id', item):
            if item.trashed:
                result.append("""<a href="/resource/%s/%s/untrash">Untrash</a>""" % (item.item_type.lower(), item.pk))
            else:
                result.append("""<a href="/resource/%s/%s/trash">Trash</a>""" % (item.item_type.lower(), item.pk))
            if itemversion.trashed:
                result.append("""<a href="/resource/%s/%s/untrash?version=%s">Untrash Version</a>""" % (item.item_type.lower(), item.pk, itemversion.version_number))
            else:
                result.append("""<a href="/resource/%s/%s/trash?version=%s">Trash Version</a>""" % (item.item_type.lower(), item.pk, itemversion.version_number))
        result.append("""</div>""")
        for inherited_item_type in item_type_inheritance:
            result.append("""<a href="/resource/%s">%ss</a> &raquo;""" % (inherited_item_type.lower(), inherited_item_type))
        if agentcan_helper(context, 'view', 'name', item):
            result.append('<a href="/resource/%s/%s">%s</a>' % (item.item_type.lower(), item.pk, item.name))
        else:
            result.append('<a href="/resource/%s/%s">[PERMISSION DENIED]</a>' % (item.item_type.lower(), item.pk))
        result.append("""&raquo; """)
        result.append("""<select id="id_item_type" name="item_type" onchange="window.location = this.value;">""")
        for other_itemversion in item.versions.all():
            result.append("""<option value="/resource/%s/%s/%s?version=%s"%s>Version %s</option>""" % (item.item_type.lower(), item.pk, context['action'], other_itemversion.version_number, ' selected="selected"' if other_itemversion.version_number == itemversion.version_number else '', other_itemversion.version_number))
        result.append("""</select>""")

        result.append("""</div>""")

        if agentcan_helper(context, 'view', 'created_at', item):
            created_at_text = item.created_at.strftime("%Y-%m-%d %H:%m")
        else:
            created_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'updated_at', item):
            updated_at_text = itemversion.updated_at.strftime("%Y-%m-%d %H:%m")
        else:
            updated_at_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'creator', item):
            if agentcan_helper(context, 'view', 'name', item.creator):
                creator_text = """<a href="%s">%s</a>""" % (show_resource_url(item.creator), item.creator.name)
            else:
                creator_text = """<a href="%s">%s</a>""" % (show_resource_url(item.creator), '[PERMISSION DENIED]')
        else:
            creator_text = '[PERMISSION DENIED]'
        if agentcan_helper(context, 'view', 'updater', item):
            if agentcan_helper(context, 'view', 'name', itemversion.updater):
                updater_text = """<a href="%s">%s</a>""" % (show_resource_url(itemversion.updater), itemversion.updater.name)
            else:
                updater_text = """<a href="%s">%s</a>""" % (show_resource_url(itemversion.updater), '[PERMISSION DENIED]')
        else:
            updater_text = '[PERMISSION DENIED]'
        result.append('<div style="font-size: 8pt;">')
        result.append('<div style="float: left;">')
        result.append("""Originally created by %s on %s""" % (creator_text, created_at_text))
        result.append('</div>')
        result.append('<div style="float: right;">')
        result.append("""Version %s updated by %s on %s""" % (itemversion.version_number, updater_text, updated_at_text))
        result.append('</div>')
        result.append('<div style="clear: both;">')
        result.append('</div>')
        result.append('</div>')

        result.append('<div style="font-size: 8pt; color: #aaa; margin-bottom: 10px;">')
        if agentcan_helper(context, 'view', 'description', item):
            result.append('Description: %s' % itemversion.description)
        else:
            result.append('Description: [PERMISSION DENIED]')
        result.append('</div>')

        if item.trashed:
            result.append("""<div style="color: #c00; font-weight: bold; font-size: larger;">This version is trashed</div>""")

        return '\n'.join(result)

@register.simple_tag
def display_body_with_inline_comments(itemversion):
    #TODO permissions? you should be able to see any CommentLocation, but maybe not the id of the comment it refers to
    #TODO don't insert these in bad places, like inside a tag <img <a href="....> />
    comment_locations = cms.models.CommentLocation.objects.filter(comment__commented_item=itemversion.current_item, commented_item_version_number=itemversion.version_number, commented_item_index__isnull=False, trashed=False, comment__trashed=False).order_by('-commented_item_index')
    body_as_list = list(itemversion.body)
    for comment_location in comment_locations:
        i = comment_location.commented_item_index
        body_as_list[i:i] = '<a href="/resource/comment/%s" class="commentref">%s</a>' % (comment_location.comment.pk, comment_location.comment.name)
    return ''.join(body_as_list)


@register.tag
def itemheader(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return ItemHeader()


class CommentBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CommentBoxNode>"

    def render(self, context):
        item = context['item']
        itemversion = context['itemversion']
        full_path = context['full_path']

        result = []
        result.append("""<div class="comment_box">""")
        result.append("""<div class="comment_box_header"><a href="/resource/comment/new?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Add Comment</a></div>""" % (itemversion.current_item.pk, itemversion.version_number, urlquote(full_path)))
        def add_comments_to_div(comments, nesting_level=0):
            for comment_info in comments:
                comment = comment_info['comment']
                comment_location = comment_info['comment_location']
                if not agentcan_helper(context, 'view', 'commented_item', comment):
                    continue
                result.append("""<div class="comment_outer%s">""" % (' comment_outer_toplevel' if nesting_level == 0 else '',))
                result.append("""<div class="comment_header">""")
                result.append("""<div style="float: right;"><a href="/resource/comment/new?commented_item=%s&commented_item_version_number=%s&redirect=%s">[+] Reply</a></div>""" % (comment.pk, comment.versions.latest().version_number, urlquote(full_path)))
                if agentcan_helper(context, 'view', 'name', comment):
                    result.append("""<a href="/resource/%s/%s">%s</a>""" % (comment.item_type.lower(), comment.pk, comment.name))
                else:
                    result.append('[PERMISSION DENIED]')
                if agentcan_helper(context, 'view', 'creator', comment):
                    if agentcan_helper(context, 'view', 'name', comment.creator):
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), comment.creator.name))
                    else:
                        result.append("""by <a href="%s">%s</a>""" % (show_resource_url(comment.creator), 'PERMISSION DENIED'))
                else:
                    result.append('by [PERMISSION DENIED]')
                if not comment_location:
                    result.append("[INACTIVE]")
                result.append("</div>")
                if comment.trashed:
                    result.append("""<div class="comment_body">""")
                    result.append("[TRASHED]")
                    result.append("</div>")
                else:
                    result.append("""<div class="comment_description">""")
                    if agentcan_helper(context, 'view', 'description', comment):
                        result.append(comment.description)
                    else:
                        result.append('[PERMISSION DENIED]')
                    result.append("</div>")
                    result.append("""<div class="comment_body">""")
                    if agentcan_helper(context, 'view', 'body', comment):
                        result.append(comment.body)
                    else:
                        result.append('[PERMISSION DENIED]')
                    result.append("</div>")
                add_comments_to_div(comment_info['subcomments'], nesting_level + 1)
                result.append("</div>")
        add_comments_to_div(comment_dicts_for_item(item, itemversion))
        result.append("</div>")
        return '\n'.join(result)

@register.tag
def commentbox(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CommentBox()


class EmbeddedItem(template.Node):
    def __init__(self, item):
        self.item = template.Variable(item)

    def __repr__(self):
        return "<EmbeddedItemNode>"

    def render(self, context):
        item = self.item.resolve(context)
        if isinstance(item, basestring):
            try:
                item = cms.models.Item.objects.get(pk=item)
            except ObjectDoesNotExist:
                item = None
        if not isinstance(item, cms.models.Item):
            return ''
        item = item.downcast()
        from cms.views import get_viewer_class_for_viewer_name
        viewer_class = get_viewer_class_for_viewer_name(item.item_type.lower())
        viewer = viewer_class()
        viewer.init_from_div(context['request'], 'show', item.item_type.lower(), item, item.versions.latest().downcast(), context['cur_agent'])
        return """<div style="padding: 10px; border: thick solid #aaa;">%s</div>""" % viewer.dispatch().content


@register.tag
def embed(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument" % bits[0]
    return EmbeddedItem(bits[1])

