from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db import connection
import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.base import ModelBase
from copy import deepcopy


class Enemy(models.Model):
    pass

class Troop(models.Model):
    pass

class Soldier(models.Model):
    troop = models.ForeignKey(Troop)

class TroopKill(models.Model):
    enemy = models.ForeignKey(Enemy)
    troop = models.ForeignKey(Troop)

class SoldierKill(models.Model):
    enemy = models.ForeignKey(Enemy)
    soldier = models.ForeignKey(Soldier)
    grenade = models.BooleanField()



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
            if isinstance(value, models.Field) and value.editable:
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
    item_type = models.CharField(max_length=255, default='Item', editable=False)
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='item_versions_as_updater')
    updated_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False)

    class Meta:
        unique_together = (('current_item', 'version_number'),)
        ordering = ['version_number']
        get_latest_by = "version_number"

    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version_number, self.get_name())

    def get_name(self):
        return 'Generic Item'

    def downcast(self):
        #TODO make more efficient
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.VERSION.objects.get(id=self.id)

    @transaction.commit_on_success
    def trash(self):
        try:
            latest_untrashed_version = self.current_item.versions.filter(trashed=False).latest()
        except ObjectDoesNotExist:
            latest_untrashed_version = None
        self.trashed = True
        self.save()
        if latest_untrashed_version == self:
            try:
                new_latest_untrashed_version = self.current_item.versions.filter(trashed=False).latest()
            except ObjectDoesNotExist:
                new_latest_untrashed_version = None
            if new_latest_untrashed_version:
                fields = {}
                for field in new_latest_untrashed_version._meta.fields:
                    if field.primary_key:
                        continue
                    if field.name in []:
                        continue
                    if type(field).__name__ == 'OneToOneField':
                        continue
                    try:
                        fields[field.name] = getattr(new_latest_untrashed_version, field.name)
                    except ObjectDoesNotExist:
                        fields[field.name] = None
                for key, val in fields.iteritems():
                    setattr(new_latest_untrashed_version.current_item, key, val)
                self.current_item.save()
            else:
                self.current_item.trashed = True
                self.current_item.save()

    @transaction.commit_on_success
    def untrash(self):
        try:
            latest_untrashed_version = self.current_item.versions.filter(trashed=False).latest()
        except ObjectDoesNotExist:
            latest_untrashed_version = None
        self.trashed = False
        self.save()
        if not latest_untrashed_version or self.version_number > latest_untrashed_version.version_number:
            self.current_item.trashed = True
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
            for key, val in fields.iteritems():
                setattr(self.current_item, key, val)
            self.current_item.save()


class Item(models.Model):
    __metaclass__ = ItemMetaClass
    item_type = models.CharField(max_length=255, default='Item', editable=False)
    description = models.TextField(blank=True)
    updater = models.ForeignKey('Agent', related_name='items_as_updater', editable=False)
    updated_at = models.DateTimeField(editable=False)
    creator = models.ForeignKey('Agent', related_name='items_as_creator', editable=False)
    created_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.get_name())

    def get_name(self):
        return 'Generic Item'

    def downcast(self):
        #TODO make more efficient
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.objects.get(id=self.id)

    @transaction.commit_on_success
    def trash(self):
        self.trashed = True
        self.save()
        self.versions.all().update(trashed=True)

    @transaction.commit_on_success
    def untrash(self):
        self.trashed = False
        self.save()
        self.versions.all().update(trashed=False)

    @transaction.commit_on_success
    def save_versioned(self, updater=None, first_agent=False, created_at=None, updated_at=None):
        save_time = datetime.datetime.now()
        self.item_type = type(self).__name__
        if first_agent:
            self.creator = self
            self.creator_id = 1
            self.updater = self
            self.updater_id = 1
        if updater:
            self.updater = updater
            if not self.pk:
                self.creator = updater
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
        if first_agent:
            new_version.updater = self
            new_version.updater_id = 1
        for key, val in fields.iteritems():
            setattr(new_version, key, val)
        if self.pk:
            latest_version_number = ItemVersion.objects.filter(current_item__pk=self.pk).order_by('-version_number')[0].version_number
        else:
            latest_version_number = 0
            if created_at:
                self.created_at = created_at
            else:
                self.created_at = save_time
        if updated_at:
            self.updated_at = updated_at
        else:
            self.updated_at = save_time
        new_version.updated_at = self.updated_at
        new_version.version_number = latest_version_number + 1
        if first_agent:
            new_version.updater_id = 1
        self.save()
        new_version.current_item_id = self.pk
        new_version.save()


class Agent(Item):
    last_online_at = models.DateTimeField(null=True, blank=True) #TODO make this get set in the viewer
    def get_name(self):
        return 'Generic Agent'


class Account(Item):
    agent = models.ForeignKey(Agent, related_name='accounts_as_agent')
    def get_name(self):
        return 'Generic Account'


# ported to python from http://packages.debian.org/lenny/libcrypt-mysql-perl
def mysql_pre41_password(raw_password):
    nr = 1345345333L
    add = 7
    nr2 = 0x12345671L
    for ch in raw_password:
        if ch == ' ' or ch == '\t':
            continue # skip spaces in raw_password
        tmp = ord(ch)
        nr ^= (((nr & 63) + add) * tmp) + (nr << 8)
        nr2 += (nr2 << 8) ^ nr
        add += tmp
    result1 = nr & ((1L << 31) - 1L) # Don't use sign bit (str2int)
    result2 = nr2 & ((1L << 31) - 1L)
    return "%08lx%08lx" % (result1, result2)

def get_hexdigest(algorithm, salt, raw_password):
    from django.utils.encoding import smart_str
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)
    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    elif algorithm == 'mysql_pre41_password':
        return mysql_pre41_password(raw_password)
    raise ValueError("Got unknown password algorithm type in password.")


class PasswordAccount(Account):
    password = models.CharField(max_length=128)

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)

    def check_password(self, raw_password):
        algo, salt, hsh = self.password.split('$')
        return hsh == get_hexdigest(algo, salt, raw_password)
    
    def get_name(self):
        return 'Password Account'


class AnonymousAccount(Account):
    def get_name(self):
        return 'Anonymous Account'


class Person(Agent):
    first_name = models.CharField(max_length=255)
    middle_names = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=320)
    password_question = models.CharField(max_length=255, blank=True)
    password_answer = models.CharField(max_length=255, blank=True)
    def get_name(self):
        return '%s %s' % (self.first_name, self.last_name)


class ItemSet(Item):
    name = models.CharField(max_length=255)
    def get_name(self):
        return self.name


class Folio(ItemSet):
    pass


class Group(Agent):
    #folio = models.OneToOneField(Item, related_name='group_as_folio')
    # can't be onetoone because lots of versions pointing to folio
    folio = models.ForeignKey(Folio, related_name='groups_as_folio', unique=True, editable=False)
    name = models.CharField(max_length=255)
    def get_name(self):
        return self.name


class Document(Item):
    name = models.CharField(max_length=255)
    def get_name(self):
        return self.name


class TextDocument(Document):
    body = models.TextField()


class DjangoTemplateDocument(TextDocument):
    pass


class HtmlDocument(TextDocument):
    pass


class FileDocument(Document):
    datafile = models.FileField(upload_to='filedocument/%Y/%m/%d', max_length=255)


class Comment(TextDocument):
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    commented_item_version = models.ForeignKey(Item.VERSION, related_name='comments_as_item_version')
    name = models.CharField(max_length=255)
    def get_name(self):
        return self.name


class Relationship(Item):
    def get_name(self):
        return 'Generic Relationship'


class GroupMembership(Relationship):
    agent = models.ForeignKey(Agent, related_name='group_memberships_as_agent')
    group = models.ForeignKey(Group, related_name='group_memberships_as_group')
    class Meta:
        unique_together = (('agent', 'group'),)
    def get_name(self):
        return 'Membership of %s in %s' % (self.agent.downcast().get_name(), self.group.downcast().get_name())


class ItemSetMembership(Relationship):
    item = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    itemset = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item', 'itemset'),)
    def get_name(self):
        return 'Membership of %s in %s' % (self.item.downcast().get_name(), self.itemset.downcast().get_name())


class Role(Item):
    name = models.CharField(max_length=255)
    def get_name(self):
        return self.name


class RoleAbility(Item):
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=255, choices=[('this', 'do this'), ('that', 'do that')])
    is_allowed = models.BooleanField()
    class Meta:
        unique_together = (('role', 'ability'),)
    def get_name(self):
        return 'Ability to %s %s for %s' % ('do' if self.is_allowed else 'not do', self.ability, self.role.downcast().get_name())


class AgentPermission(Relationship):
    agent = models.ForeignKey(Agent, related_name='agent_permissions_as_agent', null=True, blank=True)
    item = models.ForeignKey(Item, related_name='agent_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='agent_permissions_as_role')
    class Meta:
        unique_together = (('agent', 'item', 'role'),)
    def get_name(self):
        if self.agent:
            agent_name = self.agent.downcast().get_name()
        else:
            agent_name = 'Default Agent'
        if self.item:
            return '%s Role for %s with %s' % (self.role.downcast().get_name(), agent_name, self.item.downcast().get_name())
        else:
            return '%s Role for %s' % (self.role.downcast().get_name(), agent_name)


class GroupPermission(Relationship):
    group = models.ForeignKey(Group, related_name='group_permissions_as_group', null=True, blank=True)
    item = models.ForeignKey(Item, related_name='group_permissions_as_item', null=True, blank=True)
    role = models.ForeignKey(Role, related_name='group_permissions_as_role')
    class Meta:
        unique_together = (('group', 'item', 'role'),)
    def get_name(self):
        if self.item:
            return '%s Role for %s with %s' % (self.role.downcast().get_name(), self.group.downcast().get_name(), self.item.downcast().get_name())
        else:
            return '%s Role for %s' % (self.role.downcast().get_name(), self.group.downcast().get_name())


class ViewerRequest(Item):
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=255, choices=[('item', 'Item'), ('group', 'Group'), ('itemset', 'ItemSet'), ('textdocument', 'TextDocument'), ('djangotemplatedocument', 'DjangoTemplateDocument')])
    action = models.CharField(max_length=256)
    query_string = models.CharField(max_length=1024, null=True, blank=True)
    def get_name(self):
        if self.aliased_item:
            return 'View %s in %s.%s' % (self.aliased_item.downcast().get_name(), self.viewer, self.action)
        else:
            return 'View %s.%s' % (self.viewer, self.action)


class Site(ViewerRequest):
    is_default_site = IsDefaultField(default=None)
    name = models.CharField(max_length=255)
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


def all_models():
    import django.db.models.loading
    result = [x for x in django.db.models.loading.get_models() if issubclass(x, Item)]
    return result

