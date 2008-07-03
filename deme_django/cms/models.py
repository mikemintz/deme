from django.db import models
from django.db import transaction
from django.db import connection
import datetime
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.base import ModelBase
from copy import deepcopy

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
        rev_attrs = deepcopy(attrs)
        for field_name, field in rev_attrs.iteritems():
            if isinstance(field, models.Field):
                if field.rel and field.rel.related_name:
                    field.rel.related_name = 'REV_' + field.rel.related_name
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
        self.created_at = datetime.datetime.now()
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
    is_anonymous = models.BooleanField()

class Account(Item):
    agent = models.ForeignKey(Agent, related_name='accounts_as_agent')

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
    folio = models.ForeignKey(Folio, related_name='groups_as_folio')

class Document(Item):
    last_author = models.ForeignKey(Agent, related_name='documents_as_last_author')

class TextDocument(Document):
    body = models.TextField()

class MediaDocument(Document):
    datafile = models.FileField(upload_to='mediadocument/%Y/%m/%d')

class Comment(Item):
    last_author = models.ForeignKey(Agent, related_name='comments_as_last_author')
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    commented_item_version = models.ForeignKey(Item.REV, related_name='comments_as_item_version')
    body = models.TextField()

class BinaryRelationship(Item):
    item1 = models.ForeignKey(Item, related_name='relationships_as_item1', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='relationships_as_item2', null=True, blank=True)

class AgentToGroupRelationship(BinaryRelationship):
    # item1 is agent
    # item2 is group
    item1 = models.ForeignKey(Agent, related_name='group_relationships')
    item2 = models.ForeignKey(Group, related_name='agent_relationships')

class ItemToItemSetRelationship(BinaryRelationship):
    # item1 is item
    # item2 is itemset
    item1 = models.ForeignKey(Item, related_name='itemset_relationships_as_item')
    item2 = models.ForeignKey(ItemSet, related_name='itemset_relationships_as_itemset')

class Role(Item):
    pass

class RolePermission(Item):
    role = models.ForeignKey(Role, related_name='permissions_as_role')
    ability = models.CharField(max_length=100, choices=[('this', 'do this'), ('that', 'do that')])
    is_allowed = models.BooleanField()

class AgentItemRoleRelationship(BinaryRelationship):
    # item1 is agent
    # item2 is item
    item1 = models.ForeignKey(Agent, related_name='item_role_relationships_as_agent', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='agent_role_relationships_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='agent_item_relationships_as_role')

class GroupItemRoleRelationship(BinaryRelationship):
    # item1 is group
    # item2 is item
    item1 = models.ForeignKey(Group, related_name='item_role_relationships_as_group', null=True, blank=True)
    item2 = models.ForeignKey(Item, related_name='group_role_relationships_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='group_item_relationships_as_role')

class AliasUrl(Item):
    aliased_item = models.ForeignKey(Item, related_name='alias_urls_as_item')
    site = models.ForeignKey(Site)
    path = models.CharField(max_length=1024)


all_models = []

for var_name in dir():
    var = eval(var_name)
    if isinstance(var, type) and issubclass(var, Item):
        all_models.append(var)

#print sorted([x.__name__ for x in all_models])

