from django import template
import cms.models
from cms import permission_functions

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
    if isinstance(item_type, basestring):
        item_type = getattr(cms.models, item_type, None)
    if not isinstance(item_type, type):
        return icon_url(type(item_type), size)
    if issubclass(item_type, cms.models.Item.VERSION):
        return icon_url(item_type.NOTVERSION, size)
    elif item_type == cms.models.Account:
        icon = 'apps/password'
    elif item_type == cms.models.Agent:
        icon = 'apps/personal'
    elif item_type == cms.models.AgentRolePermission:
        icon = 'apps/proxy'
    elif item_type == cms.models.GroupMembership:
        icon = 'apps/katomic'
    elif item_type == cms.models.CustomUrl:
        icon = 'mimetypes/message'
    elif item_type == cms.models.Relationship:
        icon = 'apps/proxy'
    elif item_type == cms.models.Comment:
        icon = 'apps/filetypes'
    elif item_type == cms.models.DefaultRolePermission:
        icon = 'apps/proxy'
    elif item_type == cms.models.Document:
        icon = 'mimetypes/empty'
    elif item_type == cms.models.DjangoTemplateDocument:
        icon = 'mimetypes/html'
    elif item_type == cms.models.Folio:
        icon = 'apps/kfm'
    elif item_type == cms.models.Group:
        icon = 'apps/Login Manager'
    elif item_type == cms.models.GroupRolePermission:
        icon = 'apps/proxy'
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
    elif item_type == cms.models.Person:
        icon = 'apps/access'
    elif item_type == cms.models.Role:
        icon = 'apps/lassist'
    elif item_type == cms.models.RoleAbility:
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
def list_results_navigator(item_type, search_query, trashed, offset, limit, n_results, max_pages):
    result = []
    if offset > 0:
        new_offset = max(0, offset - limit)
        prev_button = '<a class="list_results_prev" href="/resource/%s/list?q=%s&trashed=%s&&offset=%d&limit=%d">&laquo; Prev</a>' % (item_type.lower(), search_query, '1' if trashed else '0', new_offset, limit)
        result.append(prev_button)
    for new_offset in xrange(max(0, offset - limit * max_pages), min(n_results - 1, offset + limit * max_pages), limit):
        if new_offset == offset:
            step_button = '<span class="list_results_highlighted">%d</span>' % (1 + new_offset / limit,)
        else:
            step_button = '<a class="list_results_step" href="/resource/%s/list?q=%s&trashed=%s&&offset=%d&limit=%d">%d</a>' % (item_type.lower(), search_query, '1' if trashed else '0', new_offset, limit, 1 + new_offset / limit)
        result.append(step_button)
    if offset < n_results - limit:
        new_offset = offset + limit
        next_button = '<a class="list_results_next" href="/resource/%s/list?q=%s&trashed=%s&offset=%d&limit=%d">Next &raquo;</a>' % (item_type.lower(), search_query, '1' if trashed else '0', new_offset, limit)
        result.append(next_button)
    return ''.join(result)




#TODO make this more efficient (i.e. cache it in a consistent place)
class IfAgentCan(template.Node):
    def __init__(self, agent, ability, ability_parameter, item, nodelist_true, nodelist_false):
        self.agent = template.Variable(agent)
        self.ability = template.Variable(ability)
        self.ability_parameter = template.Variable(ability_parameter)
        self.item = template.Variable(item)
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false

    def __repr__(self):
        return "<IfAgentCanNode>"

    def render(self, context):
        try:
            agent = self.agent.resolve(context)
        except template.VariableDoesNotExist:
            agent = None
        try:
            item = self.item.resolve(context)
        except template.VariableDoesNotExist:
            item = None
        try:
            ability = self.ability.resolve(context)
        except template.VariableDoesNotExist:
            ability = None
        try:
            ability_parameter = self.ability_parameter.resolve(context)
        except template.VariableDoesNotExist:
            ability_parameter = None
        if agent == None or item == None or ability == None or ability_parameter == None:
            return 'invalid 13409120491824' # TODO what should i do here?
        global_abilities = context['_global_ability_cache'].get(agent.pk)
        if global_abilities is None:
            global_abilities = permission_functions.get_global_abilities_for_agent(agent)
            context['_global_ability_cache'][agent.pk] = global_abilities
        if ('do_everything', 'Item') in global_abilities:
            return self.nodelist_true.render(context)
        abilities_for_item = context['_item_ability_cache'].get((agent.pk, item.pk))
        if abilities_for_item is None:
            abilities_for_item = permission_functions.get_abilities_for_agent_and_item(agent, item)
            context['_item_ability_cache'][(agent.pk, item.pk)] = abilities_for_item
        if (ability, ability_parameter) in abilities_for_item:
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


def do_ifagentcan(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 5:
        raise template.TemplateSyntaxError, "%r takes four arguments" % bits[0]
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfAgentCan(bits[1], bits[2], bits[3], bits[4], nodelist_true, nodelist_false)

@register.tag
def ifagentcan(parser, token):
    return do_ifagentcan(parser, token)

