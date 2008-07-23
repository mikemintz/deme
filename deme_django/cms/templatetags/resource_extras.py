from django import template
import cms.models

register = template.Library()

@register.simple_tag
def show_resource_url(item):
    if isinstance(item, cms.models.ItemRev):
        return '/resource/%s/%s?version=%s' % (item.item_type.lower(), item.current_item_id, item.version)
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
    if issubclass(item_type, cms.models.Item.REV):
        return icon_url(item_type.NOTREV, size)
    elif item_type == cms.models.Account:
        icon = 'apps/password'
    elif item_type == cms.models.Agent:
        icon = 'apps/personal'
    elif item_type == cms.models.AgentItemRoleRelationship:
        icon = 'apps/proxy'
    elif item_type == cms.models.AgentToGroupRelationship:
        icon = 'apps/katomic'
    elif item_type == cms.models.AliasUrl:
        icon = 'mimetypes/message'
    elif item_type == cms.models.BinaryRelationship:
        icon = 'apps/proxy'
    elif item_type == cms.models.Comment:
        icon = 'apps/filetypes'
    elif item_type == cms.models.Document:
        icon = 'mimetypes/empty'
    elif item_type == cms.models.DynamicPage:
        icon = 'mimetypes/html'
    elif item_type == cms.models.Folio:
        icon = 'apps/kfm'
    elif item_type == cms.models.Group:
        icon = 'apps/Login Manager'
    elif item_type == cms.models.GroupItemRoleRelationship:
        icon = 'apps/proxy'
    elif item_type == cms.models.Item:
        icon = 'apps/kblackbox'
    elif item_type == cms.models.ItemSet:
        icon = 'filesystems/folder_blue'
    elif item_type == cms.models.ItemToItemSetRelationship:
        icon = 'filesystems/folder_documents'
    elif item_type == cms.models.LocalUrl:
        icon = 'mimetypes/message'
    elif item_type == cms.models.MediaDocument:
        icon = 'mimetypes/misc'
    elif item_type == cms.models.Person:
        icon = 'apps/access'
    elif item_type == cms.models.Role:
        icon = 'apps/lassist'
    elif item_type == cms.models.RolePermission:
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

