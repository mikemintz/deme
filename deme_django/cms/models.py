from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db import connection
import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.base import ModelBase
from copy import deepcopy


class IsDefaultFormField(forms.BooleanField):
    widget = forms.CheckboxInput
    def clean(self, value):
        if value == 'False':
            return None
        if value:
            return True
        return None


class IsDefaultField(models.NullBooleanField):
    def __init__(self, *args, **kwargs):
        kwargs['unique'] = True
        models.NullBooleanField.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "NullBooleanField"

    def to_python(self, value):
        if value in (None, True): return value
        if value in (False,): return None
        if value in ('None'): return None
        if value in ('t', 'True', '1'): return True
        raise validators.ValidationError, _("This value must be either None or True.")

    def formfield(self, **kwargs):
        defaults = {'form_class': IsDefaultFormField}
        defaults.update(kwargs)
        return super(IsDefaultField, self).formfield(**defaults)


class ItemMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        if name in ['Item', 'ItemVersion']:
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            if name == 'Item':
                result.VERSION = eval('ItemVersion')
                eval('ItemVersion').NOTVERSION = result
            return result
        version_name = "%sVersion" % name
        version_bases = tuple([x.VERSION for x in bases])
        def convert_to_version(key, value):
            #TODO do we need to remove uniqueness of related_field?
            #TODO do we need to deepcopy the key?
            value = deepcopy(value)
            if isinstance(value, models.Field):
                if value.rel and value.rel.related_name:
                    value.rel.related_name = 'version_' + value.rel.related_name
                value._unique = False
            return key, value
        def is_valid_in_version(key, value):
            if key == '__module__':
                return True
            if isinstance(value, models.Field):
                return True
            return False
        version_attrs = dict([convert_to_version(k,v) for k,v in attrs.iteritems() if is_valid_in_version(k,v)])
        if 'get_name' in attrs:
            version_attrs['get_name'] = attrs['get_name']
        version_result = super(ItemMetaClass, cls).__new__(cls, version_name, version_bases, version_attrs)
        result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
        #exec('global %s;%s = version_result'%(version_name, version_name))
        #this_module = sys.modules[__name__]
        #setattr(this_module, version_name, version_result)
        result.VERSION = version_result
        version_result.NOTVERSION = result
        return result

class ItemVersion(models.Model):
    __metaclass__ = ItemMetaClass
    current_item = models.ForeignKey('Item', related_name='versions', editable=False)
    version_number = models.IntegerField(default=1, editable=False)
    item_type = models.CharField(max_length=100, default='Item', editable=False)
    description = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    class Meta:
        unique_together = (('current_item', 'version_number'),)
    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version_number, self.get_name())
    def get_name(self):
        return 'Generic Item'
    def downcast(self):
        return eval(self.item_type).VERSION.objects.get(id=self.id)

class Item(models.Model):
    __metaclass__ = ItemMetaClass
    item_type = models.CharField(max_length=100, default='Item', editable=False)
    description = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.get_name())
    def get_name(self):
        return 'Generic Item'
    def downcast(self):
        return eval(self.item_type).objects.get(id=self.id)
    @transaction.commit_on_success
    def save_versioned(self):
        self.item_type = type(self).__name__
        self.created_at = datetime.datetime.now() #TODO what is this doing here? i'm confused!
        fields = {}
        for field in self._meta.fields:
            if field.primary_key:
                continue
            if field.name in []:
                continue
            if type(field).__name__ == 'OneToOneField':
                continue
            try:
                fields[field.name] = getattr(self, field.name)
            except ObjectDoesNotExist:
                fields[field.name] = None
        new_version = self.__class__.VERSION()
        for key, val in fields.iteritems():
            setattr(new_version, key, val)
        if self.pk:
            latest_version_number = ItemVersion.objects.filter(current_item__pk=self.pk).order_by('-version_number')[0].version_number
        else:
            latest_version_number = 0
        new_version.version_number = latest_version_number + 1
        self.save()
        new_version.current_item_id = self.pk
        new_version.save()

class Agent(Item):
    def get_name(self):
        return 'Generic Agent'

class Account(Item):
    agent = models.ForeignKey(Agent, related_name='accounts_as_agent')
    def get_name(self):
        return 'Generic Account'

class AnonymousAccount(Account):
    def get_name(self):
        return 'Anonymous Account'

class Person(Agent):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=320)
    def get_name(self):
        return '%s %s' % (self.first_name, self.last_name)

class ItemSet(Item):
    name = models.CharField(max_length=100)
    def get_name(self):
        return self.name

class Folio(ItemSet):
    pass

class Group(Agent):
    #folio = models.OneToOneField(Item, related_name='group_as_folio')
    # can't be onetoone because lots of versions pointing to folio
    folio = models.ForeignKey(Folio, related_name='groups_as_folio', unique=True)
    name = models.CharField(max_length=100)
    def get_name(self):
        return self.name

class Document(Item):
    last_author = models.ForeignKey(Agent, related_name='documents_as_last_author')
    name = models.CharField(max_length=100)
    def get_name(self):
        return self.name

class TextDocument(Document):
    body = models.TextField()

class DjangoTemplateDocument(TextDocument):
    pass

class HtmlDocument(TextDocument):
    pass

class FileDocument(Document):
    datafile = models.FileField(upload_to='filedocument/%Y/%m/%d')

class Comment(TextDocument):
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    commented_item_version = models.ForeignKey(Item.VERSION, related_name='comments_as_item_version')
    name = models.CharField(max_length=100)
    def get_name(self):
        return self.name

class Relationship(Item):
    def get_name(self):
        return 'Generic Relationship'
    #TODO we can't define item1 and item2 here or else we won't be able to unique_together it in subclasses
    #item1 = models.ForeignKey(Item, related_name='relationships_as_item1', null=True, blank=True)
    #item2 = models.ForeignKey(Item, related_name='relationships_as_item2', null=True, blank=True)

class GroupMembership(Relationship):
    # item1 is agent
    # item2 is group
    item1 = models.ForeignKey(Agent, related_name='group_memberships_as_agent')
    item2 = models.ForeignKey(Group, related_name='group_memberships_as_group')
    class Meta:
        unique_together = (('item1', 'item2'),)
    def get_name(self):
        return 'Membership of %s in %s' % (self.item1.downcast().get_name(), self.item2.downcast().get_name())

class ItemSetMembership(Relationship):
    # item1 is item
    # item2 is itemset
    item1 = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    item2 = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item1', 'item2'),)
    def get_name(self):
        return 'Membership of %s in %s' % (self.item1.downcast().get_name(), self.item2.downcast().get_name())

class Role(Item):
    name = models.CharField(max_length=100)
    def get_name(self):
        return self.name

class RoleAbility(Item):
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=100, choices=[('this', 'do this'), ('that', 'do that')])
    is_allowed = models.BooleanField()
    #TODO add unique_together?
    def get_name(self):
        return 'Ability to %s %s for %s' % ('do' if self.is_allowed else 'not do', self.ability, self.role.downcast().get_name())

class AgentPermission(Relationship):
    # item1 is agent
    # item2 is item
    item1 = models.ForeignKey(Agent, related_name='agent_permissions_as_agent', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='agent_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='agent_permissions_as_role')
    class Meta:
        unique_together = (('item1', 'item2', 'role'),)
    def get_name(self):
        if self.item1:
            item1_name = self.item1.downcast().get_name()
        else:
            item1_name = 'Default Agent'
        if self.item2:
            return '%s Role for %s with %s' % (self.role.downcast().get_name(), item1_name, self.item2.downcast().get_name())
        else:
            return '%s Role for %s' % (self.role.downcast().get_name(), item1_name)

class GroupPermission(Relationship):
    # item1 is group
    # item2 is item
    item1 = models.ForeignKey(Group, related_name='group_permissions_as_group', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='group_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='group_permissions_as_role')
    class Meta:
        unique_together = (('item1', 'item2', 'role'),)
    def get_name(self):
        if self.item2:
            return '%s Role for %s with %s' % (self.role.downcast().get_name(), self.item1.downcast().get_name(), self.item2.downcast().get_name())
        else:
            return '%s Role for %s' % (self.role.downcast().get_name(), self.item1.downcast().get_name())

class ViewerRequest(Item):
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=100, choices=[('item', 'Item'), ('group', 'Group'), ('itemset', 'ItemSet'), ('textdocument', 'TextDocument'), ('djangotemplatedocument', 'DjangoTemplateDocument')])
    action = models.CharField(max_length=256)
    query_string = models.CharField(max_length=1024, null=True, blank=True)
    def get_name(self):
        if self.aliased_item:
            return 'View %s in %s.%s' % (self.aliased_item.downcast().get_name(), self.viewer, self.action)
        else:
            return 'View %s.%s' % (self.viewer, self.action)

class Site(ViewerRequest):
    is_default_site = IsDefaultField(default=None)
    name = models.CharField(max_length=100)
    def get_name(self):
        url_name = self.name
        if self.aliased_item:
            return 'View %s in %s.%s at %s' % (self.aliased_item.downcast().get_name(), self.viewer, self.action, url_name)
        else:
            return 'View %s.%s at %s' % (self.viewer, self.action, url_name)

class SiteDomain(Item):
    hostname = models.CharField(max_length=256)
    site = models.ForeignKey(Site, related_name='site_domains_as_site')
    class Meta:
        unique_together = (('site', 'hostname'),)
    def get_name(self):
        return hostname
#TODO match iteratively until all subdomains are gone, so if we have deme.com, then www.deme.com matches unless already taken

#TODO we should prevent top level names like 'static' and 'resource', although not a big deal since it doesn't overwrite
class CustomUrl(ViewerRequest):
    parent_url = models.ForeignKey('ViewerRequest', related_name='child_urls')
    path = models.CharField(max_length=256)
    class Meta:
        unique_together = (('parent_url', 'path'),)
    def get_name(self):
        url_name = ''
        cur = self
        while True:
            url_name = '/%s%s' % (cur.path, url_name)
            cur = cur.parent_url.downcast()
            if cur.item_type == 'Site':
                url_name = '%s %s' % (cur.name, url_name)
                break
        if self.aliased_item:
            return 'View %s in %s.%s at %s' % (self.aliased_item.downcast().get_name(), self.viewer, self.action, url_name)
        else:
            return 'View %s.%s at %s' % (self.viewer, self.action, url_name)

all_models = []

for var_name in dir():
    var = eval(var_name)
    if isinstance(var, type) and issubclass(var, Item):
        all_models.append(var)

#print sorted([x.__name__ for x in all_models])

