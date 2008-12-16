from django.db import models
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db import connection
import datetime
from django.core.exceptions import ObjectDoesNotExist
import django.db.models.loading

from django.db.models.base import ModelBase
from copy import deepcopy
import hashlib


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
            #TODO do we preserve the db_index? should we?
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
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='item_versions_as_updater')
    updated_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False, db_index=True)

    class Meta:
        unique_together = (('current_item', 'version_number'),)
        ordering = ['version_number']
        get_latest_by = "version_number"

    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version_number, self.get_name())

    def get_name(self):
        return self.name

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
    immutable_fields = []
    item_type = models.CharField(max_length=255, default='Item', editable=False)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='items_as_updater', editable=False)
    updated_at = models.DateTimeField(editable=False)
    creator = models.ForeignKey('Agent', related_name='items_as_creator', editable=False)
    created_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False, db_index=True)

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.get_name())

    def get_name(self):
        return self.name

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
    def save_versioned(self, updater=None, first_agent=False, create_permissions=True, created_at=None, updated_at=None):
        save_time = datetime.datetime.now()
        is_new = not self.pk
        self.item_type = type(self).__name__
        if first_agent:
            self.creator = self
            self.creator_id = 1
            self.updater = self
            self.updater_id = 1
        if updater:
            self.updater = updater
            if is_new:
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
        if not is_new:
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
        #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
        #TODO we need to reference the roles by id, not name, otherwise very insecure!
        if create_permissions and latest_version_number == 0 and not issubclass(self.__class__, Permission):
            DefaultRolePermission(name="Default permission for %s" % self.name, item=self, role=Role.objects.get(name="%s Default" % self.__class__.__name__)).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)
            AgentRolePermission(name="Creator permission for %s" % self.name, agent=updater, item=self, role=Role.objects.get(name="%s Creator" % self.__class__.__name__)).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)

        #TODO really? no emails if the comment was updated (not created)?
        #TODO permissions to view name/body/etc
        #TODO bubble up to itemsets that contain this item recursively
        #TODO maybe this should happen asynchronously somehow
        if is_new and isinstance(self, Comment):
            # email everyone subscribed to items this comment is relevant for
            subscribed_persons = Person.objects.filter(subscriptions_as_person__item=self.commented_item).all()
            recipient_list = [x.email for x in subscribed_persons]
            if recipient_list:
                from django.core.mail import send_mail
                subject = '[%s] %s' % (self.commented_item.name, self.name)
                message = '%s wrote a comment in %s\n%s\n\n%s' % (self.creator.name, self.commented_item.name, 'http://deme.stanford.edu/resource/%s/%d' % (self.commented_item.item_type.lower(), self.commented_item.pk), self.body)
                from_email = '"Deme" <noreply@deme.stanford.edu>'
                send_mail(subject, message, from_email, recipient_list)


class Agent(Item):
    last_online_at = models.DateTimeField(null=True, blank=True) # it's a little sketchy how this gets set without save_versioned(), so maybe reverting to an old version will reset this to NULL


class AnonymousAgent(Agent):
    pass


class Account(Item):
    agent = models.ForeignKey(Agent, related_name='accounts_as_agent')


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


class Person(Agent):
    first_name = models.CharField(max_length=255)
    middle_names = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=320, unique=True, null=True, blank=True)
    password_question = models.CharField(max_length=255, blank=True)
    password_answer = models.CharField(max_length=255, blank=True)


class ItemSet(Item):
    pass


class Group(Agent):
    pass


class Folio(ItemSet):
    group = models.ForeignKey(Group, related_name='folios_as_group', unique=True, editable=False)


class Document(Item):
    pass


class TextDocument(Document):
    body = models.TextField(blank=True)


class DjangoTemplateDocument(TextDocument):
    layout = models.ForeignKey('DjangoTemplateDocument', related_name='djangotemplatedocuments_as_layout', null=True, blank=True)
    override_default_layout = models.BooleanField(default=False)


class HtmlDocument(TextDocument):
    pass


class FileDocument(Document):
    datafile = models.FileField(upload_to='filedocument/%Y/%m/%d', max_length=255)


class ImageDocument(FileDocument):
    #TODO eventually we'll have metadata like width, height, exif, and a pointer to a thumbfile or 2
    pass


class Comment(TextDocument):
    immutable_fields = TextDocument.immutable_fields + ['commented_item']
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')


class CommentLocation(Item):
    immutable_fields = TextDocument.immutable_fields + ['comment', 'commented_item_version_number']
    comment = models.ForeignKey(Comment, related_name='comment_locations_as_comment')
    commented_item_version_number = models.IntegerField()
    commented_item_index = models.IntegerField(null=True, blank=True)
    class Meta:
        unique_together = (('comment', 'commented_item_version_number'),)


class Relationship(Item):
    pass


class GroupMembership(Relationship):
    immutable_fields = Relationship.immutable_fields + ['agent', 'group']
    agent = models.ForeignKey(Agent, related_name='group_memberships_as_agent')
    group = models.ForeignKey(Group, related_name='group_memberships_as_group')
    class Meta:
        unique_together = (('agent', 'group'),)


class ItemSetMembership(Relationship):
    immutable_fields = Relationship.immutable_fields + ['item', 'itemset']
    item = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    itemset = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item', 'itemset'),)


class Subscription(Item):
    immutable_fields = Item.immutable_fields + ['subscriber', 'item']
    subscriber = models.ForeignKey(Person, related_name='subscriptions_as_person')
    item = models.ForeignKey(Item, related_name='subscriptions_as_item')
    comprehensive = models.BooleanField()
    class Meta:
        unique_together = (('subscriber', 'item'),)


################################################################################
# Permissions
################################################################################

POSSIBLE_ABILITIES = [
    ('view', 'View'),
    ('edit', 'Edit'),
    ('modify_permissions', 'Modify Permissions'),
    ('trash', 'Trash'),
    ('login_as', 'Login As'),
]

POSSIBLE_GLOBAL_ABILITIES = [
    ('create', 'Create'),
    ('do_something', 'Do Something'), #TODO get rid of this (probably replace with can_login which only matters at login, not on any other pages)
    ('do_everything', 'Do Everything'),
]

#TODO somehow limit ability_parameter
#TODO make role name unique maybe, or at least have a way of finding the ONE "Account Creator" role

class GlobalRole(Item):
    pass


class Role(Item):
    pass


class GlobalRoleAbility(Item):
    immutable_fields = Item.immutable_fields + ['global_role', 'ability', 'ability_parameter']
    global_role = models.ForeignKey(GlobalRole, related_name='abilities_as_global_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField()
    class Meta:
        unique_together = (('global_role', 'ability', 'ability_parameter'),)


class RoleAbility(Item):
    immutable_fields = Item.immutable_fields + ['role', 'ability', 'ability_parameter']
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(db_index=True)
    class Meta:
        unique_together = (('role', 'ability', 'ability_parameter'),)


class Permission(Item):
    pass


class GlobalPermission(Item):
    pass


class AgentGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['agent', 'ability', 'ability_parameter']
    agent = models.ForeignKey(Agent, related_name='agent_global_permissions_as_agent')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField()
    class Meta:
        unique_together = (('agent', 'ability', 'ability_parameter'),)


class GroupGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['group', 'ability', 'ability_parameter']
    group = models.ForeignKey(Group, related_name='group_global_permissions_as_group')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField()
    class Meta:
        unique_together = (('group', 'ability', 'ability_parameter'),)


class DefaultGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['ability', 'ability_parameter']
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField()
    class Meta:
        unique_together = (('ability', 'ability_parameter'),)


class AgentGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['agent', 'global_role']
    agent = models.ForeignKey(Agent, related_name='agent_global_role_permissions_as_agent')
    global_role = models.ForeignKey(GlobalRole, related_name='agent_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('agent', 'global_role'),)


class GroupGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['group', 'global_role']
    group = models.ForeignKey(Group, related_name='group_global_role_permissions_as_group')
    global_role = models.ForeignKey(GlobalRole, related_name='group_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('group', 'global_role'),)


class DefaultGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['global_role']
    global_role = models.ForeignKey(GlobalRole, related_name='default_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('global_role',),)


class AgentPermission(Permission):
    immutable_fields = Permission.immutable_fields + ['agent', 'item', 'ability', 'ability_parameter']
    agent = models.ForeignKey(Agent, related_name='agent_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(db_index=True)
    class Meta:
        unique_together = (('agent', 'item', 'ability', 'ability_parameter'),)


class GroupPermission(Permission):
    immutable_fields = Permission.immutable_fields + ['group', 'item', 'ability', 'ability_parameter']
    group = models.ForeignKey(Group, related_name='group_permissions_as_group')
    item = models.ForeignKey(Item, related_name='group_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(db_index=True)
    class Meta:
        unique_together = (('group', 'item', 'ability', 'ability_parameter'),)


class DefaultPermission(Permission):
    immutable_fields = Permission.immutable_fields + ['item', 'ability', 'ability_parameter']
    item = models.ForeignKey(Item, related_name='default_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(db_index=True)
    class Meta:
        unique_together = (('item', 'ability', 'ability_parameter'),)


class AgentRolePermission(Permission):
    immutable_fields = Permission.immutable_fields + ['agent', 'item', 'role']
    agent = models.ForeignKey(Agent, related_name='agent_role_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='agent_role_permissions_as_role')
    class Meta:
        unique_together = (('agent', 'item', 'role'),)


class GroupRolePermission(Permission):
    immutable_fields = Permission.immutable_fields + ['group', 'item', 'role']
    group = models.ForeignKey(Group, related_name='group_role_permissions_as_group')
    item = models.ForeignKey(Item, related_name='group_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='group_role_permissions_as_role')
    class Meta:
        unique_together = (('group', 'item', 'role'),)


class DefaultRolePermission(Permission):
    immutable_fields = Permission.immutable_fields + ['item', 'role']
    item = models.ForeignKey(Item, related_name='default_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='default_role_permissions_as_role')
    class Meta:
        unique_together = (('item', 'role'),)


################################################################################
# Viewer aliases
################################################################################


class ViewerRequest(Item):
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    query_string = models.CharField(max_length=1024, null=True, blank=True)
    #TODO add kwargs['format']


class Site(ViewerRequest):
    is_default_site = IsDefaultField(default=None)
    default_layout = models.ForeignKey('DjangoTemplateDocument', related_name='sites_as_default_layout', null=True, blank=True)


class SiteDomain(Item):
    immutable_fields = Item.immutable_fields + ['hostname', 'site']
    hostname = models.CharField(max_length=255)
    site = models.ForeignKey(Site, related_name='site_domains_as_site')
    class Meta:
        unique_together = (('site', 'hostname'),)
#TODO match iteratively until all subdomains are gone, so if we have deme.com, then www.deme.com matches unless already taken


#TODO we should prevent top level names like 'static' and 'resource', although not a big deal since it doesn't overwrite
class CustomUrl(ViewerRequest):
    immutable_fields = Item.immutable_fields + ['parent_url', 'path']
    parent_url = models.ForeignKey('ViewerRequest', related_name='child_urls')
    path = models.CharField(max_length=255)
    class Meta:
        unique_together = (('parent_url', 'path'),)


################################################################################
# all_models()
################################################################################

def all_models():
    result = [x for x in django.db.models.loading.get_models() if issubclass(x, Item)]
    return result

