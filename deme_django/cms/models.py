from django.db import models
from django.db.models import Q
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db import connection
import datetime
from django.core.exceptions import ObjectDoesNotExist
import django.db.models.loading
from django.core.mail import SMTPConnection, EmailMessage
from email.utils import formataddr
from django.core.urlresolvers import reverse
import settings

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
            # No point in indexing updater in versions
            if name == 'ItemVersion':
                attrs['updater'].db_index = False
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            if name == 'Item':
                result.VERSION = eval('ItemVersion')
                eval('ItemVersion').NOTVERSION = result
            return result
        attrs_copy = deepcopy(attrs)
        result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
        version_name = "%sVersion" % name
        version_bases = tuple([x.VERSION for x in bases])
        def convert_to_version(key, value):
            if isinstance(value, models.Field):
                # We don't want to waste time indexing versions, except things specified in ItemVersion like version_number and current_item
                value.db_index = False
                if value.rel and value.rel.related_name:
                    value.rel.related_name = 'version_' + value.rel.related_name
                value._unique = False
            elif key == '__module__':
                # Just keep it the same
                pass
            else:
                raise Exception("wtf119283913: %s -> %s" % (key, value))
            return key, value
        def is_valid_in_version(key, value):
            if key == '__module__':
                return True
            if isinstance(value, models.Field) and value.editable and key not in result.immutable_fields:
                return True
            return False
        version_attrs = dict([convert_to_version(k,v) for k,v in attrs_copy.iteritems() if is_valid_in_version(k,v)])
        version_result = super(ItemMetaClass, cls).__new__(cls, version_name, version_bases, version_attrs)
        result.VERSION = version_result
        version_result.NOTVERSION = result
        return result


class ItemVersion(models.Model):
    __metaclass__ = ItemMetaClass
    current_item = models.ForeignKey('Item', related_name='versions', editable=False)
    version_number = models.PositiveIntegerField(default=1, editable=False, db_index=True)
    item_type = models.CharField(max_length=255, default='Item', editable=False)
    name = models.CharField(max_length=255, default="Untitled")
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='item_versions_as_updater')
    updated_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False)

    class Meta:
        unique_together = (('current_item', 'version_number'),)
        ordering = ['version_number']
        get_latest_by = "version_number"

    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version_number, self.name)

    def downcast(self):
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.VERSION.objects.get(id=self.id)


class Item(models.Model):
    __metaclass__ = ItemMetaClass
    immutable_fields = frozenset()
    relevant_abilities = frozenset(['trash', 'login_as', 'modify_permissions', 'view name', 'view description', 'view updater', 'view updated_at', 'view creator', 'view created_at', 'edit name', 'edit description'])
    relevant_global_abilities = frozenset(['do_something', 'do_everything', 'create Item'])
    item_type = models.CharField(max_length=255, default='Item', editable=False)
    name = models.CharField(max_length=255, default="Untitled")
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='items_as_updater', editable=False)
    updated_at = models.DateTimeField(editable=False)
    creator = models.ForeignKey('Agent', related_name='items_as_creator', editable=False)
    created_at = models.DateTimeField(editable=False)
    trashed = models.BooleanField(default=False, editable=False, db_index=True)

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.name)

    def downcast(self):
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.objects.get(id=self.id)

    def latest_untrashed_itemversion(self):
        try:
            result = type(self).VERSION.objects.filter(current_item=self, trashed=False).latest()
        except ObjectDoesNotExist:
            result = type(self).VERSION.objects.filter(current_item=self).latest()
        return result

    def all_containing_itemsets(self, recursive_filter=None):
        recursive_memberships = RecursiveItemSetMembership.objects.filter(child=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return ItemSet.objects.filter(trashed=False, pk__in=recursive_memberships.values('parent').query)

    def all_comments(self):
        return Comment.objects.filter(trashed=False, pk__in=RecursiveCommentMembership.objects.filter(parent=self).values('child').query)

    def copy_fields_from_itemversion(self, itemversion):
        fields = {}
        for field in itemversion._meta.fields:
            if field.primary_key:
                continue
            if type(field).__name__ == 'OneToOneField':
                continue
            try:
                fields[field.name] = getattr(itemversion, field.name)
            except ObjectDoesNotExist:
                fields[field.name] = None
        for key, val in fields.iteritems():
            setattr(self, key, val)
    copy_fields_from_itemversion.alters_data = True

    def copy_fields_to_itemversion(self, itemversion):
        fields = {}
        for field in self._meta.fields:
            if field.primary_key:
                continue
            if type(field).__name__ == 'OneToOneField':
                continue
            try:
                fields[field.name] = getattr(self, field.name)
            except ObjectDoesNotExist:
                fields[field.name] = None
        for key, val in fields.iteritems():
            setattr(itemversion, key, val)
    copy_fields_to_itemversion.alters_data = True

    @transaction.commit_on_success
    def trash(self, agent):
        if self.trashed:
            return
        self.copy_fields_from_itemversion(self.versions.latest().downcast())
        self.trashed = True
        self.save()
        self.versions.all().update(trashed=True)
        self.after_trash(agent)
    trash.alters_data = True

    @transaction.commit_on_success
    def untrash(self, agent):
        if not self.trashed:
            return
        self.copy_fields_from_itemversion(self.versions.latest().downcast())
        self.trashed = False
        self.save()
        self.versions.all().update(trashed=False)
        self.after_untrash(agent)
    untrash.alters_data = True

    @transaction.commit_on_success
    def save_versioned(self, updater=None, first_agent=False, create_permissions=True, created_at=None, updated_at=None, overwrite_latest_version=False):
        save_time = datetime.datetime.now()
        is_new = not self.pk

        # Update the item
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
        if is_new:
            if created_at:
                self.created_at = created_at
            else:
                self.created_at = save_time
        if updated_at:
            self.updated_at = updated_at
        else:
            self.updated_at = save_time
        self.trashed = False
        self.save()

        # Create the new item version
        latest_version_number = 0 if is_new else ItemVersion.objects.filter(current_item__pk=self.pk).order_by('-version_number')[0].version_number
        if overwrite_latest_version and not is_new:
            new_version = self.__class__.VERSION.objects.get(current_item=self, version_number=latest_version_number)
        else:
            new_version = self.__class__.VERSION()
            new_version.current_item_id = self.pk
            new_version.version_number = latest_version_number + 1
        self.copy_fields_to_itemversion(new_version)
        new_version.save()

        # Create the permissions
        #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
        if create_permissions and is_new and not issubclass(self.__class__, Permission):
            default_role = Role.objects.get(pk=DemeSetting.get("cms.default_role.%s" % self.__class__.__name__))
            creator_role = Role.objects.get(pk=DemeSetting.get("cms.creator_role.%s" % self.__class__.__name__))
            DefaultRolePermission(item=self, role=default_role).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)
            AgentRolePermission(agent=updater, item=self, role=creator_role).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)

        # Create an EditComment if we're making an edit
        if not is_new and not overwrite_latest_version:
            edit_comment = EditComment(commented_item=self)
            edit_comment.save_versioned(updater=updater)
            edit_comment_location = CommentLocation(comment=edit_comment, commented_item_version_number=new_version.version_number, commented_item_index=None)
            edit_comment_location.save_versioned(updater=updater)

        if is_new:
            self.after_create()
    save_versioned.alters_data = True

    def after_create(self):
        pass
    after_create.alters_data = True

    def after_trash(self, agent):
        # Create a TrashComment
        trash_comment = TrashComment(commented_item=self)
        trash_comment.save_versioned(updater=agent)
        trash_comment_location = CommentLocation(comment=trash_comment, commented_item_version_number=self.versions.latest().version_number, commented_item_index=None)
        trash_comment_location.save_versioned(updater=agent)
    after_trash.alters_data = True

    def after_untrash(self, agent):
        # Create an UntrashComment
        untrash_comment = UntrashComment(commented_item=self)
        untrash_comment.save_versioned(updater=agent)
        untrash_comment_location = CommentLocation(comment=untrash_comment, commented_item_version_number=self.versions.latest().version_number, commented_item_index=None)
        untrash_comment_location.save_versioned(updater=agent)
    after_untrash.alters_data = True


class DemeSetting(Item):
    immutable_fields = Item.immutable_fields | set(['key'])
    relevant_abilities = Item.relevant_abilities | set(['view key', 'view value', 'edit value'])
    relevant_global_abilities = frozenset(['create DemeSetting'])
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255, blank=True)
    @classmethod
    def get(cls, key):
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except ObjectDoesNotExist:
            return None
    @classmethod
    def set(cls, key, value):
        admin = Agent.objects.get(pk=1)
        try:
            setting = cls.objects.get(key=key)
        except ObjectDoesNotExist:
            setting = cls(name=key, key=key)
        setting.value = value
        setting.save_versioned(updater=admin)


class Agent(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['view last_online_at', 'edit last_online_at'])
    relevant_global_abilities = frozenset(['create Agent'])
    last_online_at = models.DateTimeField(null=True, blank=True) # TODO it's a little sketchy how this gets set without save_versioned(), so maybe reverting to an old version will reset this to NULL
    #TODO last_online_at should be not editable or immutable and fix the 'edit last_online_at' ability?


class AnonymousAgent(Agent):
    immutable_fields = Agent.immutable_fields
    relevant_abilities = Agent.relevant_abilities
    relevant_global_abilities = frozenset(['create AnonymousAgent'])


class AuthenticationMethod(Item):
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['view agent'])
    relevant_global_abilities = frozenset(['create AuthenticationMethod'])
    agent = models.ForeignKey(Agent, related_name='authenticationmethods_as_agent')


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
        raise ValueError('"crypt" password algorithm not supported in this version of Deme')
        # try:
        #     import crypt
        # except ImportError:
        #     raise ValueError('"crypt" password algorithm not supported in this environment')
        # return crypt.crypt(raw_password, salt)
    if algorithm == 'md5':
        raise ValueError('"md5" password algorithm not supported in this version of Deme')
        # return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    elif algorithm == 'mysql_pre41_password':
        return mysql_pre41_password(raw_password)
    raise ValueError("Got unknown password algorithm type in password.")

class PasswordAuthenticationMethod(AuthenticationMethod):
    immutable_fields = AuthenticationMethod.immutable_fields
    relevant_abilities = AuthenticationMethod.relevant_abilities | set(['view username', 'view password', 'view password_question', 'view password_answer', 'edit username', 'edit password', 'edit password_question', 'edit password_answer'])
    relevant_global_abilities = frozenset(['create PasswordAuthenticationMethod'])
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    password_question = models.CharField(max_length=255, blank=True)
    password_answer = models.CharField(max_length=255, blank=True)

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    set_password.alters_data = True

    def check_password(self, raw_password):
        algo, salt, hsh = self.password.split('$')
        return hsh == get_hexdigest(algo, salt, raw_password)

    def check_nonced_password(self, hashed_password, nonce):
        algo, salt, hsh = self.password.split('$')
        return get_hexdigest('sha1', nonce, hsh) == hashed_password

class Person(Agent):
    immutable_fields = Agent.immutable_fields
    relevant_abilities = Agent.relevant_abilities | set(['view first_name', 'view middle_names', 'view last_name', 'view suffix', 'edit first_name', 'edit middle_names', 'edit last_name', 'edit suffix'])
    relevant_global_abilities = frozenset(['create Person'])
    first_name = models.CharField(max_length=255)
    middle_names = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255, blank=True)


class ItemSet(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create ItemSet'])
    def all_contained_itemset_members(self, recursive_filter=None):
        recursive_memberships = RecursiveItemSetMembership.objects.filter(parent=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return Item.objects.filter(trashed=False, pk__in=recursive_memberships.values('child').query)
    def after_trash(self, agent):
        super(ItemSet, self).after_trash(agent)
        RecursiveItemSetMembership.recursive_remove_itemset(self)
    after_trash.alters_data = True
    def after_untrash(self, agent):
        super(ItemSet, self).after_untrash(agent)
        RecursiveItemSetMembership.recursive_add_itemset(self)
    after_untrash.alters_data = True


class Group(ItemSet):
    immutable_fields = ItemSet.immutable_fields
    relevant_abilities = ItemSet.relevant_abilities
    relevant_global_abilities = frozenset(['create Group'])
    def after_create(self):
        super(Group, self).after_create()
        folio = Folio(group=self)
        folio.save_versioned(updater=self.updater)
    after_create.alters_data = True


class Folio(ItemSet):
    immutable_fields = ItemSet.immutable_fields | set(['group'])
    relevant_abilities = ItemSet.relevant_abilities | set(['view group'])
    relevant_global_abilities = frozenset(['create Folio'])
    group = models.ForeignKey(Group, related_name='folios_as_group', unique=True, editable=False)


class ItemSetMembership(Item):
    immutable_fields = Item.immutable_fields | set(['item', 'itemset'])
    relevant_abilities = Item.relevant_abilities | set(['view item', 'view itemset'])
    relevant_global_abilities = frozenset(['create ItemSetMembership'])
    item = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    itemset = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item', 'itemset'),)
    def after_create(self):
        super(ItemSetMembership, self).after_create()
        RecursiveItemSetMembership.recursive_add_membership(self)
        add_member_comment = AddMemberComment(commented_item=self.itemset, membership=self)
        add_member_comment.save_versioned(updater=self.creator)
        add_member_comment_location = CommentLocation(comment=add_member_comment, commented_item_version_number=self.itemset.versions.latest().version_number, commented_item_index=None)
        add_member_comment_location.save_versioned(updater=self.creator)
    after_create.alters_data = True
    def after_trash(self, agent):
        super(ItemSetMembership, self).after_trash(agent)
        RecursiveItemSetMembership.recursive_remove_edge(self.itemset, self.item)
        remove_member_comment = RemoveMemberComment(commented_item=self.itemset, membership=self)
        remove_member_comment.save_versioned(updater=agent)
        remove_member_comment_location = CommentLocation(comment=remove_member_comment, commented_item_version_number=self.itemset.versions.latest().version_number, commented_item_index=None)
        remove_member_comment_location.save_versioned(updater=agent)
    after_trash.alters_data = True
    def after_untrash(self, agent):
        super(ItemSetMembership, self).after_untrash(agent)
        RecursiveItemSetMembership.recursive_add_membership(self)
        add_member_comment = AddMemberComment(commented_item=self.itemset, membership=self)
        add_member_comment.save_versioned(updater=agent)
        add_member_comment_location = CommentLocation(comment=add_member_comment, commented_item_version_number=self.itemset.versions.latest().version_number, commented_item_index=None)
        add_member_comment_location.save_versioned(updater=agent)
    after_untrash.alters_data = True


class Document(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create Document'])


class TextDocument(Document):
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view body', 'edit body'])
    relevant_global_abilities = frozenset(['create TextDocument'])
    body = models.TextField(blank=True)


class DjangoTemplateDocument(TextDocument):
    immutable_fields = TextDocument.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | set(['view layout', 'view override_default_layout', 'edit layout', 'edit override_default_layout'])
    relevant_global_abilities = frozenset(['create DjangoTemplateDocument'])
    layout = models.ForeignKey('DjangoTemplateDocument', related_name='djangotemplatedocuments_as_layout', null=True, blank=True)
    override_default_layout = models.BooleanField(default=False)


class HtmlDocument(TextDocument):
    immutable_fields = TextDocument.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities
    relevant_global_abilities = frozenset(['create HtmlDocument'])


class FileDocument(Document):
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view datafile', 'edit datafile'])
    relevant_global_abilities = frozenset(['create FileDocument'])
    datafile = models.FileField(upload_to='filedocument/%Y/%m/%d', max_length=255)


class ImageDocument(FileDocument):
    immutable_fields = FileDocument.immutable_fields
    relevant_abilities = FileDocument.relevant_abilities
    relevant_global_abilities = frozenset(['create ImageDocument'])


class Comment(Document):
    immutable_fields = Document.immutable_fields | set(['commented_item'])
    relevant_abilities = Document.relevant_abilities | set(['view commented_item'])
    relevant_global_abilities = frozenset(['create Comment'])
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    def topmost_commented_item(self):
        comment_class_names = [model.__name__ for model in all_models() if issubclass(model, Comment)]
        return Item.objects.filter(pk__in=RecursiveCommentMembership.objects.filter(child=self).values('parent').query).exclude(item_type__in=comment_class_names).get()
    def all_commented_items(self):
        return Item.objects.filter(pk__in=RecursiveCommentMembership.objects.filter(child=self).values('parent').query)
    def all_commented_items_and_itemsets(self, recursive_filter=None):
        parent_item_pks_query = RecursiveCommentMembership.objects.filter(child=self).values('parent').query
        parent_items = Q(pk__in=parent_item_pks_query)

        recursive_memberships = RecursiveItemSetMembership.objects.filter(child__in=parent_item_pks_query)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        parent_item_itemsets = Q(pk__in=recursive_memberships.values('parent').query)

        return Item.objects.filter(parent_items | parent_item_itemsets, trashed=False)
    def after_create(self):
        super(Comment, self).after_create()

        # Update RecursiveCommentMembership
        RecursiveCommentMembership.recursive_add_comment(self)

        # email everyone subscribed to items this comment is relevant for
        if isinstance(self, TextComment):
            comment_type_q = Q(notify_text=True)
        elif isinstance(self, EditComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, TrashComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, UntrashComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, AddMemberComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, RemoveMemberComment):
            comment_type_q = Q(notify_edit=True)
        else:
            comment_type_q = Q(pk__isnull=False)
        direct_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items().values('pk').query, trashed=False).filter(comment_type_q)
        deep_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items_and_itemsets().values('pk').query, deep=True, trashed=False).filter(comment_type_q)
        subscribed_email_contact_methods = EmailContactMethod.objects.filter(trashed=False).filter(Q(pk__in=direct_subscriptions.values('contact_method').query) | Q(pk__in=deep_subscriptions.values('contact_method').query))
        messages = [self.notification_email(email_contact_method) for email_contact_method in subscribed_email_contact_methods]
        messages = [x for x in messages if x is not None]
        if messages:
            smtp_connection = SMTPConnection()
            smtp_connection.send_messages(messages)
    after_create.alters_data = True
    def notification_email(self, email_contact_method):
        agent = email_contact_method.agent
        import permission_functions
        can_do_everything = 'do_everything' in permission_functions.get_global_abilities_for_agent(agent)

        # First, decide if we're allowed to get this notification at all
        if isinstance(self, TextComment):
            comment_type_q = Q(notify_text=True)
        elif isinstance(self, EditComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, TrashComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, UntrashComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, AddMemberComment):
            comment_type_q = Q(notify_edit=True)
        elif isinstance(self, RemoveMemberComment):
            comment_type_q = Q(notify_edit=True)
        else:
            comment_type_q = Q(pk__isnull=False)
        direct_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items().values('pk').query, trashed=False).filter(comment_type_q)
        if not direct_subscriptions:
            if can_do_everything:
                recursive_filter = None
            else:
                visible_memberships = ItemSetMembership.objects.filter(permission_functions.filter_for_agent_and_ability(agent, 'view itemset'), permission_functions.filter_for_agent_and_ability(agent, 'view item'))
                recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
            possible_parents = self.all_commented_items_and_itemsets(recursive_filter)
            deep_subscriptions = Subscription.objects.filter(item__in=possible_parents.values('pk').query, deep=True, trashed=False).filter(comment_type_q)
            if not deep_subscriptions:
                return None

        # Now get the fields we are allowed to view
        commented_item = self.commented_item
        topmost_item = self.topmost_commented_item()
        commented_item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': commented_item.item_type.lower(), 'noun': commented_item.pk}))
        topmost_item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': topmost_item.item_type.lower(), 'noun': topmost_item.pk}))
        abilities_for_comment = permission_functions.get_abilities_for_agent_and_item(agent, self)
        abilities_for_commented_item = permission_functions.get_abilities_for_agent_and_item(agent, commented_item)
        abilities_for_topmost_item = permission_functions.get_abilities_for_agent_and_item(agent, topmost_item)
        abilities_for_comment_creator = permission_functions.get_abilities_for_agent_and_item(agent, self.creator)
        comment_name = self.name if can_do_everything or 'view name' in abilities_for_comment else 'PERMISSION DENIED'
        if isinstance(self, TextComment):
            comment_body = self.body if can_do_everything or 'view body' in abilities_for_comment else 'PERMISSION DENIED'
        commented_item_name = commented_item.name if can_do_everything or 'view name' in abilities_for_commented_item else 'PERMISSION DENIED'
        topmost_item_name = topmost_item.name if can_do_everything or 'view name' in abilities_for_topmost_item else 'PERMISSION DENIED'
        creator_name = self.creator.name if can_do_everything or 'view name' in abilities_for_comment_creator else 'PERMISSION DENIED'

        # Finally put together the message
        if isinstance(self, TextComment):
            subject = 'Re: %s (%s)' % (topmost_item_name, comment_name)
            body = '%s commented on %s\n%s\n\n%s' % (creator_name, topmost_item_name, topmost_item_url, comment_body)
        elif isinstance(self, EditComment):
            subject = 'Re: %s (Edited)' % (commented_item_name,)
            body = '%s edited %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, TrashComment):
            subject = 'Re: %s (Trashed)' % (commented_item_name,)
            body = '%s trashed %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, UntrashComment):
            subject = 'Re: %s (Untrashed)' % (commented_item_name,)
            body = '%s untrashed %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, AddMemberComment):
            subject = 'Re: %s (Member Added)' % (commented_item_name,)
            body = '%s added a member to %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, RemoveMemberComment):
            subject = 'Re: %s (Member Removed)' % (commented_item_name,)
            body = '%s removed a member from %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        else:
            return None
        from_email_address = '%s@%s' % (self.pk, settings.NOTIFICATION_EMAIL_HOSTNAME)
        from_email = formataddr((creator_name, from_email_address))
        reply_to = formataddr((comment_name, from_email_address))
        headers = {}
        headers['Reply-To'] = reply_to
        messageid = lambda x: '<%s-%s@%s>' % (x.pk, x.created_at.strftime("%Y%m%d%H%M%S"), settings.NOTIFICATION_EMAIL_HOSTNAME)
        headers['Message-ID'] = messageid(self)
        headers['In-Reply-To'] = messageid(self.commented_item)
        headers['References'] = '%s %s' % (messageid(topmost_item), messageid(self.commented_item))
        return EmailMessage(subject=subject, body=body, from_email=from_email, to=[formataddr((agent.name, email_contact_method.email))], headers=headers)


class CommentLocation(Item):
    immutable_fields = Item.immutable_fields | set(['comment', 'commented_item_version_number'])
    relevant = Item.relevant_abilities | set(['view comment', 'view commented_item_version_number', 'view commented_item_index', 'edit commented_item_index'])
    relevant_global_abilities = frozenset(['create CommentLocation'])
    comment = models.ForeignKey(Comment, related_name='comment_locations_as_comment')
    commented_item_version_number = models.PositiveIntegerField()
    commented_item_index = models.PositiveIntegerField(null=True, blank=True)
    class Meta:
        unique_together = (('comment', 'commented_item_version_number'),)


class TextComment(TextDocument, Comment):
    immutable_fields = TextDocument.immutable_fields | Comment.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | Comment.relevant_abilities
    relevant_global_abilities = frozenset(['create TextComment'])


class EditComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset(['create EditComment'])


class TrashComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset(['create TrashComment'])


class UntrashComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset(['create UntrashComment'])


class AddMemberComment(Comment):
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset(['create AddMemberComment'])
    membership = models.ForeignKey(ItemSetMembership, related_name="add_member_comments_as_membership")


class RemoveMemberComment(Comment):
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset(['create RemoveMemberComment'])
    membership = models.ForeignKey(ItemSetMembership, related_name="remove_member_comments_as_membership")


class Excerpt(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create Excerpt'])


class TextDocumentExcerpt(Excerpt, TextDocument):
    immutable_fields = Excerpt.immutable_fields | TextDocument.immutable_fields | set(['text_document','text_document_version_number', 'start_index', 'length', 'body'])
    relevant_abilities = Excerpt.relevant_abilities | TextDocument.relevant_abilities | set(['view text_document', 'view text_document_version_number', 'view start_index', 'view length']) #TODO minus 'edit body'?
    relevant_global_abilities = frozenset(['create TextDocumentExcerpt'])
    text_document = models.ForeignKey(TextDocument, related_name='text_document_excerpts_as_text_document')
    text_document_version_number = models.PositiveIntegerField()
    start_index = models.PositiveIntegerField()
    length = models.PositiveIntegerField()


class RecursiveItemSetMembership(models.Model):
    parent = models.ForeignKey(ItemSet, related_name='recursive_itemset_memberships_as_parent')
    child = models.ForeignKey(Item, related_name='recursive_itemset_memberships_as_child')
    child_memberships = models.ManyToManyField(ItemSetMembership)
    class Meta:
        unique_together = (('parent', 'child'),)
    @classmethod
    def recursive_add_membership(cls, membership):
        parent = membership.itemset
        child = membership.item
        # first connect parent to child
        recursive_itemset_membership, created = RecursiveItemSetMembership.objects.get_or_create(parent=parent, child=child)
        recursive_itemset_membership.child_memberships.add(membership)
        # second connect ancestors to child, via parent
        ancestor_recursive_memberships = RecursiveItemSetMembership.objects.filter(child=parent)
        for ancestor_recursive_membership in ancestor_recursive_memberships:
            recursive_itemset_membership, created = RecursiveItemSetMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent, child=child)
            recursive_itemset_membership.child_memberships.add(membership)
        # third connect parent and ancestors to all descendants
        descendant_recursive_memberships = RecursiveItemSetMembership.objects.filter(parent=child)
        for descendant_recursive_membership in descendant_recursive_memberships:
            child_memberships = descendant_recursive_membership.child_memberships.all()
            for ancestor_recursive_membership in ancestor_recursive_memberships:
                recursive_itemset_membership, created = RecursiveItemSetMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent, child=descendant_recursive_membership.child)
                for child_membership in child_memberships:
                    recursive_itemset_membership.child_memberships.add(child_membership)
            recursive_itemset_membership, created = RecursiveItemSetMembership.objects.get_or_create(parent=parent, child=descendant_recursive_membership.child)
            for child_membership in child_memberships:
                recursive_itemset_membership.child_memberships.add(child_membership)
    @classmethod
    def recursive_remove_edge(cls, parent, child):
        ancestors = ItemSet.objects.filter(Q(pk__in=RecursiveItemSetMembership.objects.filter(child=parent).values('parent').query) | Q(pk=parent.pk))
        descendants = Item.objects.filter(Q(pk__in=RecursiveItemSetMembership.objects.filter(parent=child).values('child').query) | Q(pk=child.pk))
        edges = RecursiveItemSetMembership.objects.filter(parent__pk__in=ancestors.values('pk').query, child__pk__in=descendants.values('pk').query)
        # first remove all connections between ancestors and descendants
        edges.delete()
        # now add back any real connections between ancestors and descendants that aren't trashed
        memberships = ItemSetMembership.objects.filter(trashed=False, itemset__in=ancestors.values('pk').query, item__in=descendants.values('pk').query).exclude(itemset=parent, item=child)
        for membership in memberships:
            RecursiveItemSetMembership.recursive_add_membership(membership)
    @classmethod
    def recursive_add_itemset(cls, itemset):
        memberships = ItemSetMembership.objects.filter(Q(itemset=itemset) | Q(item=itemset), trashed=False)
        for membership in memberships:
            RecursiveItemSetMembership.recursive_add_membership(membership)
    @classmethod
    def recursive_remove_itemset(cls, itemset):
        RecursiveItemSetMembership.recursive_remove_edge(itemset, itemset)


class RecursiveCommentMembership(models.Model):
    parent = models.ForeignKey(Item, related_name='recursive_comment_memberships_as_parent')
    child = models.ForeignKey(Comment, related_name='recursive_comment_memberships_as_child')
    class Meta:
        unique_together = (('parent', 'child'),)
    @classmethod
    def recursive_add_comment(cls, comment):
        parent = comment.commented_item
        ancestors = Item.objects.filter(Q(pk__in=RecursiveCommentMembership.objects.filter(child=parent).values('parent').query) | Q(pk=parent.pk))
        for ancestor in ancestors:
            recursive_comment_membership = RecursiveCommentMembership(parent=ancestor, child=comment)
            recursive_comment_membership.save()


class ContactMethod(Item):
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['view agent'])
    relevant_global_abilities = frozenset(['create ContactMethod'])
    agent = models.ForeignKey(Agent, related_name='contactmethods_as_agent')


class EmailContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view email', 'edit email'])
    relevant_global_abilities = frozenset(['create EmailContactMethod'])
    email = models.EmailField(max_length=320)


class PhoneContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view phone', 'edit phone'])
    relevant_global_abilities = frozenset(['create PhoneContactMethod'])
    phone = models.CharField(max_length=20)


class FaxContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view fax', 'edit fax'])
    relevant_global_abilities = frozenset(['create FaxContactMethod'])
    fax = models.CharField(max_length=20)


class WebsiteContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view url', 'edit url'])
    relevant_global_abilities = frozenset(['create WebsiteContactMethod'])
    url = models.CharField(max_length=255)


class AIMContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view screen_name', 'edit screen_name'])
    relevant_global_abilities = frozenset(['create AIMContactMethod'])
    screen_name = models.CharField(max_length=255)


class AddressContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view street1', 'view street2', 'view city', 'view state', 'view country', 'view zip', 'edit street1', 'edit street2', 'edit city', 'edit state', 'edit country', 'edit zip'])
    relevant_global_abilities = frozenset(['create AddressContactMethod'])
    street1 = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=20, blank=True)


class Subscription(Item):
    immutable_fields = Item.immutable_fields | set(['contact_method', 'item'])
    relevant_abilities = Item.relevant_abilities | set(['view contact_method', 'view item', 'view deep', 'view notify_text', 'view notify_edit', 'edit deep', 'edit notify_text', 'edit notify_edit'])
    relevant_global_abilities = frozenset(['create Subscription'])
    contact_method = models.ForeignKey(ContactMethod, related_name='subscriptions_as_contact_method')
    item = models.ForeignKey(Item, related_name='subscriptions_as_item')
    deep = models.BooleanField(default=False)
    notify_text = models.BooleanField(default=True)
    notify_edit = models.BooleanField(default=False)
    class Meta:
        unique_together = (('contact_method', 'item'),)


################################################################################
# Viewer aliases
################################################################################


class ViewerRequest(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['view aliased_item', 'view viewer', 'view action', 'view query_string', 'view format', 'edit aliased_item', 'edit viewer', 'edit action', 'edit query_string', 'edit format'])
    relevant_global_abilities = frozenset(['create ViewerRequest'])
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    query_string = models.CharField(max_length=1024, null=True, blank=True)
    format = models.CharField(max_length=255, default='html')


class Site(ViewerRequest):
    immutable_fields = ViewerRequest.immutable_fields
    relevant_abilities = ViewerRequest.relevant_abilities | set(['view is_default_site', 'view default_layout', 'edit is_default_site', 'edit default_layout'])
    relevant_global_abilities = frozenset(['create Site'])
    is_default_site = IsDefaultField(default=None)
    default_layout = models.ForeignKey('DjangoTemplateDocument', related_name='sites_as_default_layout', null=True, blank=True)


class SiteDomain(Item):
    immutable_fields = Item.immutable_fields | set(['hostname', 'site'])
    relevant_abilities = Item.relevant_abilities | set(['view hostname', 'view site'])
    relevant_global_abilities = frozenset(['create SiteDomain'])
    hostname = models.CharField(max_length=255)
    site = models.ForeignKey(Site, related_name='site_domains_as_site')
    class Meta:
        unique_together = (('site', 'hostname'),)


class CustomUrl(ViewerRequest):
    immutable_fields = ViewerRequest.immutable_fields | set(['parent_url', 'path'])
    relevant_abilities = ViewerRequest.relevant_abilities | set(['view parent_url', 'view path'])
    relevant_global_abilities = frozenset(['create CustomUrl'])
    parent_url = models.ForeignKey('ViewerRequest', related_name='child_urls')
    path = models.CharField(max_length=255)
    class Meta:
        unique_together = (('parent_url', 'path'),)


################################################################################
# Permissions
################################################################################

class POSSIBLE_ABILITIES_ITER(object):
    def __iter__(self):
        choices = set()
        for model in all_models():
            choices = choices | set([(x,x) for x in model.relevant_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

class POSSIBLE_GLOBAL_ABILITIES_ITER(object):
    def __iter__(self):
        choices = set()
        for model in all_models():
            choices = choices | set([(x,x) for x in model.relevant_global_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

POSSIBLE_ABILITIES = POSSIBLE_ABILITIES_ITER()
POSSIBLE_GLOBAL_ABILITIES = POSSIBLE_GLOBAL_ABILITIES_ITER()


class GlobalRole(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create GlobalRole'])


class Role(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create Role'])


class GlobalRoleAbility(Item):
    immutable_fields = Item.immutable_fields | set(['global_role', 'ability'])
    relevant_abilities = Item.relevant_abilities | set(['view global_role', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create GlobalRoleAbility'])
    global_role = models.ForeignKey(GlobalRole, related_name='abilities_as_global_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('global_role', 'ability'),)


class RoleAbility(Item):
    immutable_fields = Item.immutable_fields | set(['role', 'ability'])
    relevant_abilities = Item.relevant_abilities | set(['view role', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create RoleAbility'])
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('role', 'ability'),)


class Permission(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create Permission'])


class GlobalPermission(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create GlobalPermission'])


class AgentGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['agent', 'ability'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view agent', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create AgentGlobalPermission'])
    agent = models.ForeignKey(Agent, related_name='agent_global_permissions_as_agent')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('agent', 'ability'),)


class ItemSetGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['itemset', 'ability'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view itemset', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create ItemSetGlobalPermission'])
    itemset = models.ForeignKey(ItemSet, related_name='itemset_global_permissions_as_itemset')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('itemset', 'ability'),)


class DefaultGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['ability'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create DefaultGlobalPermission'])
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('ability',),)


class AgentGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['agent', 'global_role'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view agent', 'view global_role'])
    relevant_global_abilities = frozenset(['create AgentGlobalRolePermission'])
    agent = models.ForeignKey(Agent, related_name='agent_global_role_permissions_as_agent')
    global_role = models.ForeignKey(GlobalRole, related_name='agent_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('agent', 'global_role'),)


class ItemSetGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['itemset', 'global_role'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view itemset', 'view global_role'])
    relevant_global_abilities = frozenset(['create ItemSetGlobalRolePermission'])
    itemset = models.ForeignKey(ItemSet, related_name='itemset_global_role_permissions_as_itemset')
    global_role = models.ForeignKey(GlobalRole, related_name='itemset_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('itemset', 'global_role'),)


class DefaultGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields | set(['global_role'])
    relevant_abilities = GlobalPermission.relevant_abilities | set(['view global_role'])
    relevant_global_abilities = frozenset(['create DefaultGlobalRolePermission'])
    global_role = models.ForeignKey(GlobalRole, related_name='default_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('global_role',),)


class AgentPermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['agent', 'item', 'ability'])
    relevant_abilities = Permission.relevant_abilities | set(['view agent', 'view item', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create AgentPermission'])
    agent = models.ForeignKey(Agent, related_name='agent_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('agent', 'item', 'ability'),)


class ItemSetPermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['itemset', 'item', 'ability'])
    relevant_abilities = Permission.relevant_abilities | set(['view itemset', 'view item', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create ItemSetPermission'])
    itemset = models.ForeignKey(ItemSet, related_name='itemset_permissions_as_itemset')
    item = models.ForeignKey(Item, related_name='itemset_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('itemset', 'item', 'ability'),)


class DefaultPermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['item', 'ability'])
    relevant_abilities = Permission.relevant_abilities | set(['view item', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create DefaultPermission'])
    item = models.ForeignKey(Item, related_name='default_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('item', 'ability'),)


class AgentRolePermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['agent', 'item', 'role'])
    relevant_abilities = Permission.relevant_abilities | set(['view agent', 'view item', 'view role'])
    relevant_global_abilities = frozenset(['create AgentRolePermission'])
    agent = models.ForeignKey(Agent, related_name='agent_role_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='agent_role_permissions_as_role')
    class Meta:
        unique_together = (('agent', 'item', 'role'),)


class ItemSetRolePermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['itemset', 'item', 'role'])
    relevant_abilities = Permission.relevant_abilities | set(['view itemset', 'view item', 'view role'])
    relevant_global_abilities = frozenset(['create ItemSetRolePermission'])
    itemset = models.ForeignKey(ItemSet, related_name='itemset_role_permissions_as_itemset')
    item = models.ForeignKey(Item, related_name='itemset_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='itemset_role_permissions_as_role')
    class Meta:
        unique_together = (('itemset', 'item', 'role'),)


class DefaultRolePermission(Permission):
    immutable_fields = Permission.immutable_fields | set(['item', 'role'])
    relevant_abilities = Permission.relevant_abilities | set(['view item', 'view role'])
    relevant_global_abilities = frozenset(['create DefaultRolePermission'])
    item = models.ForeignKey(Item, related_name='default_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='default_role_permissions_as_role')
    class Meta:
        unique_together = (('item', 'role'),)


################################################################################
# all_models()
################################################################################

def all_models():
    result = [x for x in django.db.models.loading.get_models() if issubclass(x, Item)]
    return result

