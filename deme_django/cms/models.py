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
        if name in ['Item', 'ItemRev']:
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            if name == 'Item':
                result.REV = eval('ItemRev')
                eval('ItemRev').NOTREV = result
            return result
        rev_name = "%sRev" % name
        rev_bases = tuple([x.REV for x in bases])
        def convert_to_rev(key, value):
            #TODO do we need to remove uniqueness of related_field?
            #TODO do we need to deepcopy the key?
            value = deepcopy(value)
            if isinstance(value, models.Field):
                if value.rel and value.rel.related_name:
                    value.rel.related_name = 'REV_' + value.rel.related_name
                value._unique = False
            return key, value
        def is_valid_in_rev(key, value):
            if key == '__module__':
                return True
            if isinstance(value, models.Field):
                return True
            return False
        rev_attrs = dict([convert_to_rev(k,v) for k,v in attrs.iteritems() if is_valid_in_rev(k,v)])
        rev_result = super(ItemMetaClass, cls).__new__(cls, rev_name, rev_bases, rev_attrs)
        result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
        #exec('global %s;%s = rev_result'%(rev_name, rev_name))
        #this_module = sys.modules[__name__]
        #setattr(this_module, rev_name, rev_result)
        result.REV = rev_result
        rev_result.NOTREV = result
        return result

class ItemRev(models.Model):
    __metaclass__ = ItemMetaClass
    current_item = models.ForeignKey('Item', related_name='revisions', editable=False)
    version = models.IntegerField(default=1, editable=False)
    item_type = models.CharField(max_length=100, default='Item', editable=False)
    description = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    class Meta:
        unique_together = (('current_item', 'version'),)
    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version, self.description)
    def downcast(self):
        return eval(self.item_type).REV.objects.get(id=self.id)

class Item(models.Model):
    __metaclass__ = ItemMetaClass
    item_type = models.CharField(max_length=100, default='Item', editable=False)
    description = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.description)
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
        new_rev = self.__class__.REV()
        for key, val in fields.iteritems():
            setattr(new_rev, key, val)
        if self.pk:
            latest_version = ItemRev.objects.filter(current_item__pk=self.pk).order_by('-version')[0].version
        else:
            latest_version = 0
        new_rev.version = latest_version + 1
        self.save()
        new_rev.current_item_id = self.pk
        new_rev.save()

class Agent(Item):
    pass

class Account(Item):
    agent = models.ForeignKey(Agent, related_name='accounts_as_agent')

class AnonymousAccount(Account):
    pass

class Person(Agent):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=320)

class ItemSet(Item):
    pass

class Folio(ItemSet):
    pass

class Group(Agent):
    #folio = models.OneToOneField(Item, related_name='group_as_folio')
    # can't be onetoone because lots of versions pointing to folio
    folio = models.ForeignKey(Folio, related_name='groups_as_folio', unique=True)

class Document(Item):
    last_author = models.ForeignKey(Agent, related_name='documents_as_last_author')

class TextDocument(Document):
    body = models.TextField()

class FileDocument(Document):
    datafile = models.FileField(upload_to='filedocument/%Y/%m/%d')

class Comment(Item):
    last_author = models.ForeignKey(Agent, related_name='comments_as_last_author')
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    commented_item_version = models.ForeignKey(Item.REV, related_name='comments_as_item_version')
    body = models.TextField()

class Relationship(Item):
    pass
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

class ItemSetMembership(Relationship):
    # item1 is item
    # item2 is itemset
    item1 = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    item2 = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item1', 'item2'),)

class Role(Item):
    pass

class RoleAbility(Item):
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=100, choices=[('this', 'do this'), ('that', 'do that')])
    is_allowed = models.BooleanField()
    #TODO add unique_together?

class AgentPermission(Relationship):
    # item1 is agent
    # item2 is item
    item1 = models.ForeignKey(Agent, related_name='agent_permissions_as_agent', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='agent_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='agent_permissions_as_role')
    class Meta:
        unique_together = (('item1', 'item2', 'role'),)

class GroupPermission(Relationship):
    # item1 is group
    # item2 is item
    item1 = models.ForeignKey(Group, related_name='group_permissions_as_group', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='group_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='group_permissions_as_role')
    class Meta:
        unique_together = (('item1', 'item2', 'role'),)

class ViewerRequest(Item):
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=100, choices=[('item', 'Item'), ('group', 'Group'), ('itemset', 'ItemSet'), ('textdocument', 'TextDocument'), ('dynamicpage', 'DynamicPage')])
    action = models.CharField(max_length=256)
    query_string = models.CharField(max_length=1024, null=True, blank=True)

class Site(ViewerRequest):
    is_default_site = IsDefaultField(default=None)

class SiteDomain(Item):
    hostname = models.CharField(max_length=256)
    site = models.ForeignKey(Site, related_name='site_domains_as_site')
    class Meta:
        unique_together = (('site', 'hostname'),)
#TODO match iteratively until all subdomains are gone, so if we have deme.com, then www.deme.com matches unless already taken

#TODO we should prevent top level names like 'static' and 'resource', although not a big deal since it doesn't overwrite
class CustomUrl(ViewerRequest):
    parent_url = models.ForeignKey('ViewerRequest', related_name='child_urls')
    path = models.CharField(max_length=256)
    class Meta:
        unique_together = (('parent_url', 'path'),)

class DynamicPage(Item):
    code = models.TextField()

all_models = []

for var_name in dir():
    var = eval(var_name)
    if isinstance(var, type) and issubclass(var, Item):
        all_models.append(var)

#print sorted([x.__name__ for x in all_models])

