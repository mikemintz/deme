from django.db import models, transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import SMTPConnection, EmailMessage
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from email.utils import formataddr
import datetime
import settings
import copy
import random
import hashlib

__all__ = ['Item', 'DemeSetting', 'Agent', 'AnonymousAgent', 'AuthenticationMethod', 'PasswordAuthenticationMethod', 'Person', 'Collection', 'Group', 'Folio', 'Membership', 'Document', 'TextDocument', 'Transclusion', 'DjangoTemplateDocument', 'HtmlDocument', 'FileDocument', 'ImageDocument', 'Comment', 'TextComment', 'EditComment', 'TrashComment', 'UntrashComment', 'AddMemberComment', 'RemoveMemberComment', 'Excerpt', 'TextDocumentExcerpt', 'ContactMethod', 'EmailContactMethod', 'PhoneContactMethod', 'FaxContactMethod', 'WebsiteContactMethod', 'AIMContactMethod', 'AddressContactMethod', 'Subscription', 'ViewerRequest', 'Site', 'SiteDomain', 'CustomUrl', 'GlobalRole', 'Role', 'GlobalRoleAbility', 'RoleAbility', 'Permission', 'GlobalPermission', 'AgentGlobalPermission', 'CollectionGlobalPermission', 'DefaultGlobalPermission', 'AgentGlobalRolePermission', 'CollectionGlobalRolePermission', 'DefaultGlobalRolePermission', 'AgentPermission', 'CollectionPermission', 'DefaultPermission', 'AgentRolePermission', 'CollectionRolePermission', 'DefaultRolePermission', 'RecursiveCommentMembership', 'RecursiveMembership', 'all_models', 'get_model_with_name', 'get_hexdigest', 'get_random_hash', 'POSSIBLE_GLOBAL_ABILITIES', 'POSSIBLE_ABILITIES']

###############################################################################
# Item framework
###############################################################################

class ItemMetaClass(models.base.ModelBase):
    """
    Metaclass for item types. Takes care of creating parallel versioned classes
    for every item type.
    """
    def __new__(cls, name, bases, attrs):
        # Fix up the ItemVersion and Item classes
        if name == 'ItemVersion':
            attrs['updater'].db_index = False # No point in indexing updater in versions
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            return result
        if name == 'Item':
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            result.Version = ItemVersion
            ItemVersion.NotVersion = result
            return result

        # Create the non-versioned class
        attrs_copy = copy.deepcopy(attrs)
        result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)

        # Create the versioned class
        version_name = name + "Version"
        # Versioned classes inherit from other versioned classes
        version_bases = tuple([x.Version for x in bases])
        # Set the attrs for the versioned class
        version_attrs = {'__module__': attrs_copy['__module__']}
        # Copy over mutable fields
        for key, value in attrs_copy.iteritems():
            if isinstance(value, models.Field) and value.editable and key not in result.immutable_fields:
                # We don't want to waste time indexing versions, except things
                # specified in ItemVersion like version_number and current_item
                value.db_index = False
                # Fix the related_name so we don't have conflicts with the
                # non-versioned class.
                if value.rel and value.rel.related_name:
                    value.rel.related_name = 'version_' + value.rel.related_name
                # We don't want any fields in the versioned class to be unique
                # since there will be conflicts.
                value._unique = False
                version_attrs[key] = value
        version_result = super(ItemMetaClass, cls).__new__(cls, version_name, version_bases, version_attrs)

        # Set the Version field of the class to point to the versioned class
        result.Version = version_result
        version_result.NotVersion = result
        return result


class ItemVersion(models.Model):
    """
    Versioned class for Item, and superclass of all versioned classes.
    """

    # Setup
    __metaclass__ = ItemMetaClass
    class Meta:
        unique_together = (('current_item', 'version_number'),)
        ordering = ['version_number']
        get_latest_by = 'version_number'

    # Fields
    current_item = models.ForeignKey('Item', related_name='versions')
    version_number = models.PositiveIntegerField(db_index=True)
    item_type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='version_items_updated')
    updated_at = models.DateTimeField()

    # Methods
    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.item_type, self.current_item_id, self.version_number, self.name)

    def downcast(self):
        """
        Return this item version as an instance of the actual item type.
        
        For example, if the current item is an Agent, this will return an
        AgentVersion, even though self is an ItemVersion. This method always
        makes a single database query.
        """
        item_type = get_model_with_name(self.item_type)
        return item_type.Version.objects.get(pk=self.pk)


class Item(models.Model):
    """
    Superclass of all item types.
    
    Every subclass should define the following attributes:
    - immutable_fields: a frozenset of strings representing the names of
      fields which may not be modified after creation (this differs from
      editable=False in that immutable_fields may be customized by a user upon
      creation, but uneditable fields are not to be edited in the front end)
    - relevant_abilities: a frozenset of abilities that are relevant to this
      item type
    - relevant_global_abilities: a frozenset of global abilities that are
      introduced by this item type
    """

    # Setup
    __metaclass__ = ItemMetaClass
    immutable_fields = frozenset()
    relevant_abilities = frozenset(['comment_on', 'trash', 'modify_permissions', 'view name',
                                    'view description', 'view updater', 'view creator',
                                    'view updated_at', 'view created_at', 'edit name', 'edit description'])
    relevant_global_abilities = frozenset(['do_something', 'do_everything'])
    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')

    # Fields
    version_number = models.PositiveIntegerField(_('version number'), default=1, editable=False)
    item_type      = models.CharField(_('item type'), max_length=255, editable=False)
    name           = models.CharField(_('name'), max_length=255, default='Untitled')
    description    = models.CharField(_('description'), max_length=255, blank=True)
    updater        = models.ForeignKey('Agent', related_name='items_updated', editable=False, verbose_name=_('updater'))
    creator        = models.ForeignKey('Agent', related_name='items_created', editable=False, verbose_name=_('creator'))
    updated_at     = models.DateTimeField(_('updated at'), editable=False)
    created_at     = models.DateTimeField(_('created at'), editable=False)
    trashed        = models.BooleanField(_('trashed'), default=False, editable=False, db_index=True)

    # Methods
    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.name)

    def downcast(self):
        """
        Return this item as an instance of the actual item type.
        
        For example, if the current item is an Agent, this will return an
        Agent, even though self is an Item. This method always makes a
        single database query.
        """
        item_type = get_model_with_name(self.item_type)
        return item_type.objects.get(id=self.id)

    def ancestor_collections(self, recursive_filter=None):
        """
        Return all untrashed Collections containing self directly or
        indirectly.
        
        A Collection does not indirectly contain itself by default.
        
        If a recursive_filter is specified, use it to filter which
        RecursiveMemberships can be used to infer self's membership in a
        collection. Often, one will use a permission filter so that only those
        RecursiveMemberships that the Agent is allowed to view will be used.
        """
        recursive_memberships = RecursiveMembership.objects.filter(child=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return Collection.objects.filter(trashed=False, pk__in=recursive_memberships.values('parent').query)

    def all_comments(self):
        """
        Return all untrashed Comments made directly or indirectly on self.
        """
        recursive_comment_membership = RecursiveCommentMembership.objects.filter(parent=self)
        return Comment.objects.filter(trashed=False, pk__in=recursive_comment_membership.values('child').query)

    def copy_fields_from_version(self, version_number):
        """
        Set the fields of self to what they were at the given version number.
        This method does not make any database writes.
        """
        itemversion = type(self).Version.objects.get(current_item=self, version_number=version_number)
        fields = {}
        for field in itemversion._meta.fields:
            if not field.primary_key:
                try:
                    fields[field.name] = getattr(itemversion, field.name)
                except ObjectDoesNotExist:
                    fields[field.name] = None
        for key, val in fields.iteritems():
            setattr(self, key, val)
    copy_fields_from_version.alters_data = True

    def copy_fields_to_itemversion(self, itemversion):
        """
        Sets the fields of the itemversion from self's fields. This method
        does not make any database writes.
        
        This method may use self.version_number to calculate a delta
        (although it does not currently).
        """
        itemversion.current_item_id = self.pk
        fields = {}
        for field in self._meta.fields:
            if not field.primary_key:
                try:
                    fields[field.name] = getattr(self, field.name)
                except ObjectDoesNotExist:
                    fields[field.name] = None
        for key, val in fields.iteritems():
            setattr(itemversion, key, val)
    copy_fields_to_itemversion.alters_data = True

    @transaction.commit_on_success
    def trash(self, agent):
        """
        Trash the current Item (the specified agent was responsible). This
        will call after_trash() if the item was previously untrashed.
        """
        if self.trashed:
            return
        self.trashed = True
        self.save()
        self.after_trash(agent)
    trash.alters_data = True

    @transaction.commit_on_success
    def untrash(self, agent):
        """
        Untrash the current Item (the specified agent was responsible). This
        will call after_untrash() if the item was previously trashed.
        """
        if not self.trashed:
            return
        self.trashed = False
        self.save()
        self.after_untrash(agent)
    untrash.alters_data = True

    @transaction.commit_on_success
    def save_versioned(self, updater, first_agent=False, create_permissions=True, created_at=None, updated_at=None, overwrite_latest_version=False):
        """
        Save the current item, making sure to keep track of versions.
        
        Use this method instead of save() because it will keep things
        consistent with versions and special fields. This will set updated_at
        to the current time (or the method parameter if specified), and set
        created_at to the current time (or method parameter) if this is a
        creation.
        
        If first_agent=True, then this method assumes you are creating the
        first item (which should be an Agent). It is necessary to save the
        first item as an Agent in this way so that every Item has a valid
        updater and creator pointer.
        
        If create_permissions=True, then this method will automatically create
        reasonable permissions.
        TODO: figure out what those permissions should really be
        
        If overwrite_latest_version=True and this is an update, then this
        method will not create a new version, and make it appear that the
        latest version looked like this the whole time.
        """
        updated_at = updated_at or datetime.datetime.now()
        is_new = not self.pk

        # Update the item
        self.item_type = type(self).__name__
        if first_agent:
            self.creator = self
            self.creator_id = 1
            self.updater = self
            self.updater_id = 1
        else:
            self.updater = updater
            if is_new:
                self.creator = updater
        self.updated_at = updated_at
        if is_new or overwrite_latest_version:
            self.created_at = created_at or updated_at
        if not is_new and not overwrite_latest_version:
            self.version_number = self.version_number + 1
        self.save()

        # Create the new item version
        if overwrite_latest_version and not is_new:
            new_version = type(self).Version.objects.get(current_item=self, version_number=self.version_number)
        else:
            new_version = type(self).Version()
        self.copy_fields_to_itemversion(new_version)
        new_version.save()

        # Create the permissions
        #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
        if create_permissions and is_new:
            default_role = Role.objects.get(pk=DemeSetting.get("cms.default_role.%s" % type(self).__name__))
            creator_role = Role.objects.get(pk=DemeSetting.get("cms.creator_role.%s" % type(self).__name__))
            DefaultRolePermission(item=self, role=default_role).save()
            AgentRolePermission(agent=updater, item=self, role=creator_role).save()

        # Create an EditComment if we're making an edit
        if not is_new and not overwrite_latest_version:
            edit_comment = EditComment(commented_item=self, commented_item_version_number=self.version_number)
            edit_comment.save_versioned(updater=updater)

        if is_new:
            self.after_create()
    save_versioned.alters_data = True

    def after_create(self):
        """
        This method gets called after the first version of an item is
        created via save_versioned().
        
        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self).after_create()
        """
        pass
    after_create.alters_data = True

    def after_trash(self, agent):
        """
        This method gets called after an item is trashed.
        
        Item types that want to trigger an action after trash should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self).after_trash()
        """
        # Create a TrashComment
        trash_comment = TrashComment(commented_item=self, commented_item_version_number=self.version_number)
        trash_comment.save_versioned(updater=agent)
    after_trash.alters_data = True

    def after_untrash(self, agent):
        """
        This method gets called after an item is untrashed.
        
        Item types that want to trigger an action after untrash should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self).after_untrash()
        """
        # Create an UntrashComment
        untrash_comment = UntrashComment(commented_item=self, commented_item_version_number=self.version_number)
        untrash_comment.save_versioned(updater=agent)
    after_untrash.alters_data = True


###############################################################################
# Various item types
###############################################################################

class DemeSetting(Item):
    immutable_fields = Item.immutable_fields | set(['key'])
    relevant_abilities = Item.relevant_abilities | set(['view key', 'view value', 'edit value'])
    relevant_global_abilities = frozenset()
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255, blank=True)
    @classmethod
    def get(cls, key):
        try:
            setting = cls.objects.get(key=key)
            if setting.trashed:
                return None
            return setting.value
        except ObjectDoesNotExist:
            return None
    @classmethod
    def set(cls, key, value, agent):
        try:
            setting = cls.objects.get(key=key)
        except ObjectDoesNotExist:
            setting = cls(name=key, key=key)
        if setting.value != value:
            setting.value = value
            setting.save_versioned(updater=agent)
        if setting.trashed:
            setting.untrash(agent)


class Agent(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['add_contact_method', 'add_subscription', 'add_authentication_method', 'login_as', 'view last_online_at'])
    relevant_global_abilities = frozenset(['create Agent'])
    last_online_at = models.DateTimeField(null=True, blank=True, editable=False)


class AnonymousAgent(Agent):
    immutable_fields = Agent.immutable_fields
    relevant_abilities = Agent.relevant_abilities
    relevant_global_abilities = frozenset()


class AuthenticationMethod(Item):
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['view agent'])
    relevant_global_abilities = frozenset()
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

def get_random_hash():
    return get_hexdigest('sha1', str(random.random()), str(random.random()))

class PasswordAuthenticationMethod(AuthenticationMethod):
    immutable_fields = AuthenticationMethod.immutable_fields
    relevant_abilities = AuthenticationMethod.relevant_abilities | set(['view username', 'view password', 'view password_question', 'view password_answer', 'edit username', 'edit password', 'edit password_question', 'edit password_answer'])
    relevant_global_abilities = frozenset()
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    password_question = models.CharField(max_length=255, blank=True)
    password_answer = models.CharField(max_length=255, blank=True)

    def set_password(self, raw_password):
        algo = 'sha1'
        salt = get_random_hash()[:5]
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


class Collection(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['modify_membership', 'add_self', 'remove_self'])
    relevant_global_abilities = frozenset(['create Collection'])
    def all_contained_collection_members(self, recursive_filter=None):
        recursive_memberships = RecursiveMembership.objects.filter(parent=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return Item.objects.filter(trashed=False, pk__in=recursive_memberships.values('child').query)
    def after_trash(self, agent):
        super(Collection, self).after_trash(agent)
        RecursiveMembership.recursive_remove_collection(self)
    after_trash.alters_data = True
    def after_untrash(self, agent):
        super(Collection, self).after_untrash(agent)
        RecursiveMembership.recursive_add_collection(self)
    after_untrash.alters_data = True


class Group(Collection):
    immutable_fields = Collection.immutable_fields
    relevant_abilities = Collection.relevant_abilities
    relevant_global_abilities = frozenset(['create Group'])
    def after_create(self):
        super(Group, self).after_create()
        folio = Folio(group=self)
        folio.save_versioned(updater=self.updater)
    after_create.alters_data = True


class Folio(Collection):
    immutable_fields = Collection.immutable_fields | set(['group'])
    relevant_abilities = Collection.relevant_abilities | set(['view group'])
    relevant_global_abilities = frozenset()
    group = models.ForeignKey(Group, related_name='folios_as_group', unique=True, editable=False)


class Membership(Item):
    immutable_fields = Item.immutable_fields | set(['item', 'collection'])
    relevant_abilities = (Item.relevant_abilities | set(['view item', 'view collection'])) - set(['trash'])
    relevant_global_abilities = frozenset()
    item = models.ForeignKey(Item, related_name='memberships_as_item')
    collection = models.ForeignKey(Collection, related_name='memberships_as_collection')
    class Meta:
        unique_together = (('item', 'collection'),)
    def after_create(self):
        super(Membership, self).after_create()
        RecursiveMembership.recursive_add_membership(self)
        add_member_comment = AddMemberComment(commented_item=self.collection, commented_item_version_number=self.collection.version_number, membership=self)
        add_member_comment.save_versioned(updater=self.creator)
    after_create.alters_data = True
    def after_trash(self, agent):
        super(Membership, self).after_trash(agent)
        RecursiveMembership.recursive_remove_edge(self.collection, self.item)
        remove_member_comment = RemoveMemberComment(commented_item=self.collection, commented_item_version_number=self.collection.version_number, membership=self)
        remove_member_comment.save_versioned(updater=agent)
    after_trash.alters_data = True
    def after_untrash(self, agent):
        super(Membership, self).after_untrash(agent)
        RecursiveMembership.recursive_add_membership(self)
        add_member_comment = AddMemberComment(commented_item=self.collection, commented_item_version_number=self.collection.version_number, membership=self)
        add_member_comment.save_versioned(updater=agent)
    after_untrash.alters_data = True


class Document(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset()


class TextDocument(Document):
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view body', 'edit body', 'add_transclusion'])
    relevant_global_abilities = frozenset(['create TextDocument'])
    body = models.TextField(blank=True)


class Transclusion(Item):
    immutable_fields = Item.immutable_fields | set(['from_item', 'from_item_version_number', 'to_item'])
    relevant_abilities = Item.relevant_abilities | set(['view from_item', 'view from_item_version_number', 'view from_item_index', 'view to_item', 'edit from_item_index'])
    relevant_global_abilities = frozenset()
    from_item = models.ForeignKey(TextDocument, related_name='transclusions_from_self')
    from_item_version_number = models.PositiveIntegerField()
    from_item_index = models.PositiveIntegerField()
    to_item = models.ForeignKey(Item, related_name='transclusions_to_self')


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


class Comment(Item):
    immutable_fields = Item.immutable_fields | set(['commented_item'])
    relevant_abilities = Item.relevant_abilities | set(['view commented_item', 'view commented_item_version_number'])
    relevant_global_abilities = frozenset()
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    commented_item_version_number = models.PositiveIntegerField()
    def topmost_commented_item(self):
        comment_class_names = [model.__name__ for model in all_models() if issubclass(model, Comment)]
        return Item.objects.filter(pk__in=RecursiveCommentMembership.objects.filter(child=self).values('parent').query).exclude(item_type__in=comment_class_names).get()
    def all_commented_items(self):
        return Item.objects.filter(pk__in=RecursiveCommentMembership.objects.filter(child=self).values('parent').query)
    def all_commented_items_and_collections(self, recursive_filter=None):
        parent_item_pks_query = RecursiveCommentMembership.objects.filter(child=self).values('parent').query
        parent_items = Q(pk__in=parent_item_pks_query)

        recursive_memberships = RecursiveMembership.objects.filter(child__in=parent_item_pks_query)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        parent_item_collections = Q(pk__in=recursive_memberships.values('parent').query)

        return Item.objects.filter(parent_items | parent_item_collections, trashed=False)
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
        deep_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items_and_collections().values('pk').query, deep=True, trashed=False).filter(comment_type_q)
        subscribed_email_contact_methods = EmailContactMethod.objects.filter(trashed=False).filter(Q(pk__in=direct_subscriptions.values('contact_method').query) | Q(pk__in=deep_subscriptions.values('contact_method').query))
        messages = [self.notification_email(email_contact_method) for email_contact_method in subscribed_email_contact_methods]
        messages = [x for x in messages if x is not None]
        if messages:
            smtp_connection = SMTPConnection()
            smtp_connection.send_messages(messages)
    after_create.alters_data = True
    def notification_email(self, email_contact_method):
        agent = email_contact_method.agent
        import permissions
        can_do_everything = 'do_everything' in permissions.calculate_global_abilities_for_agent(agent)

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
                visible_memberships = Membership.objects.filter(permissions.filter_items_by_permission(agent, 'view collection'), permissions.filter_items_by_permission(agent, 'view item'))
                recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
            possible_parents = self.all_commented_items_and_collections(recursive_filter)
            deep_subscriptions = Subscription.objects.filter(item__in=possible_parents.values('pk').query, deep=True, trashed=False).filter(comment_type_q)
            if not deep_subscriptions:
                return None

        # Now get the fields we are allowed to view
        commented_item = self.commented_item
        topmost_item = self.topmost_commented_item()
        commented_item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': commented_item.item_type.lower(), 'noun': commented_item.pk}))
        topmost_item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': topmost_item.item_type.lower(), 'noun': topmost_item.pk}))
        abilities_for_comment = permissions.calculate_abilities_for_agent_and_item(agent, self)
        abilities_for_commented_item = permissions.calculate_abilities_for_agent_and_item(agent, commented_item)
        abilities_for_topmost_item = permissions.calculate_abilities_for_agent_and_item(agent, topmost_item)
        abilities_for_comment_creator = permissions.calculate_abilities_for_agent_and_item(agent, self.creator)
        comment_name = self.name if can_do_everything or 'view name' in abilities_for_comment else 'PERMISSION DENIED'
        if isinstance(self, TextComment):
            comment_body = self.body if can_do_everything or 'view body' in abilities_for_comment else 'PERMISSION DENIED'
        commented_item_name = commented_item.name if can_do_everything or 'view name' in abilities_for_commented_item else 'PERMISSION DENIED'
        topmost_item_name = topmost_item.name if can_do_everything or 'view name' in abilities_for_topmost_item else 'PERMISSION DENIED'
        creator_name = self.creator.name if can_do_everything or 'view name' in abilities_for_comment_creator else 'PERMISSION DENIED'

        # Finally put together the message
        if isinstance(self, TextComment):
            subject = 'Re: [%s] %s' % (comment_name, topmost_item_name)
            body = '%s commented on %s\n%s\n\n%s' % (creator_name, topmost_item_name, topmost_item_url, comment_body)
        elif isinstance(self, EditComment):
            subject = 'Re: [Edited] %s' % (commented_item_name,)
            body = '%s edited %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, TrashComment):
            subject = 'Re: [Trashed] %s' % (commented_item_name,)
            body = '%s trashed %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, UntrashComment):
            subject = 'Re: [Untrashed] %s' % (commented_item_name,)
            body = '%s untrashed %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, AddMemberComment):
            subject = 'Re: [Member Added] %s' % (commented_item_name,)
            body = '%s added a member to %s\n%s' % (creator_name, commented_item_name, commented_item_url)
        elif isinstance(self, RemoveMemberComment):
            subject = 'Re: [Member Removed] %s' % (commented_item_name,)
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


class TextComment(TextDocument, Comment):
    immutable_fields = TextDocument.immutable_fields | Comment.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | Comment.relevant_abilities
    relevant_global_abilities = frozenset()


class EditComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()


class TrashComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()


class UntrashComment(Comment):
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()


class AddMemberComment(Comment):
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset()
    membership = models.ForeignKey(Membership, related_name="add_member_comments_as_membership")


class RemoveMemberComment(Comment):
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset()
    membership = models.ForeignKey(Membership, related_name="remove_member_comments_as_membership")


class Excerpt(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset()


class TextDocumentExcerpt(Excerpt, TextDocument):
    immutable_fields = Excerpt.immutable_fields | TextDocument.immutable_fields | set(['text_document','text_document_version_number', 'start_index', 'length', 'body'])
    relevant_abilities = (Excerpt.relevant_abilities | TextDocument.relevant_abilities | set(['view text_document', 'view text_document_version_number', 'view start_index', 'view length'])) - set(['edit body'])
    relevant_global_abilities = frozenset(['create TextDocumentExcerpt'])
    text_document = models.ForeignKey(TextDocument, related_name='text_document_excerpts_as_text_document')
    text_document_version_number = models.PositiveIntegerField()
    start_index = models.PositiveIntegerField()
    length = models.PositiveIntegerField()


class ContactMethod(Item):
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['view agent'])
    relevant_global_abilities = frozenset()
    agent = models.ForeignKey(Agent, related_name='contactmethods_as_agent')


class EmailContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view email', 'edit email'])
    relevant_global_abilities = frozenset()
    email = models.EmailField(max_length=320)


class PhoneContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view phone', 'edit phone'])
    relevant_global_abilities = frozenset()
    phone = models.CharField(max_length=20)


class FaxContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view fax', 'edit fax'])
    relevant_global_abilities = frozenset()
    fax = models.CharField(max_length=20)


class WebsiteContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view url', 'edit url'])
    relevant_global_abilities = frozenset()
    url = models.CharField(max_length=255)


class AIMContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view screen_name', 'edit screen_name'])
    relevant_global_abilities = frozenset()
    screen_name = models.CharField(max_length=255)


class AddressContactMethod(ContactMethod):
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view street1', 'view street2', 'view city', 'view state', 'view country', 'view zip', 'edit street1', 'edit street2', 'edit city', 'edit state', 'edit country', 'edit zip'])
    relevant_global_abilities = frozenset()
    street1 = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=20, blank=True)


class Subscription(Item):
    immutable_fields = Item.immutable_fields | set(['contact_method', 'item'])
    relevant_abilities = Item.relevant_abilities | set(['view contact_method', 'view item', 'view deep', 'view notify_text', 'view notify_edit', 'edit deep', 'edit notify_text', 'edit notify_edit'])
    relevant_global_abilities = frozenset()
    contact_method = models.ForeignKey(ContactMethod, related_name='subscriptions_as_contact_method')
    item = models.ForeignKey(Item, related_name='subscriptions_as_item')
    deep = models.BooleanField(default=False)
    notify_text = models.BooleanField(default=True)
    notify_edit = models.BooleanField(default=False)
    class Meta:
        unique_together = (('contact_method', 'item'),)


###############################################################################
# Viewer aliases
###############################################################################


class ViewerRequest(Item):
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['add_sub_path', 'view aliased_item', 'view viewer', 'view action', 'view query_string', 'view format', 'edit aliased_item', 'edit viewer', 'edit action', 'edit query_string', 'edit format'])
    relevant_global_abilities = frozenset()
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests_as_item', null=True, blank=True) #null should be collection
    viewer = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    query_string = models.CharField(max_length=1024, null=True, blank=True)
    format = models.CharField(max_length=255, default='html')
    def calculate_full_path(self):
        """Return a tuple (site, custom_urls) where custom_urls is a list."""
        req = self.downcast()
        if isinstance(req, Site):
            return (req, [])
        elif isinstance(req, CustomUrl):
            parent_path = req.parent_url.calculate_full_path()
            return (parent_path[0], parent_path[1] + [req])


class Site(ViewerRequest):
    immutable_fields = ViewerRequest.immutable_fields
    relevant_abilities = ViewerRequest.relevant_abilities | set(['view default_layout', 'edit default_layout'])
    relevant_global_abilities = frozenset(['create Site'])
    default_layout = models.ForeignKey(DjangoTemplateDocument, related_name='sites_as_default_layout', null=True, blank=True)


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
    relevant_global_abilities = frozenset()
    parent_url = models.ForeignKey(ViewerRequest, related_name='child_urls')
    path = models.CharField(max_length=255)
    class Meta:
        unique_together = (('parent_url', 'path'),)


###############################################################################
# Permissions
###############################################################################

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


class Permission(models.Model):
    class Meta:
        abstract = True


class GlobalPermission(models.Model):
    class Meta:
        abstract = True


class AgentGlobalPermission(GlobalPermission):
    agent = models.ForeignKey(Agent, related_name='agent_global_permissions_as_agent')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('agent', 'ability'),)


class CollectionGlobalPermission(GlobalPermission):
    collection = models.ForeignKey(Collection, related_name='collection_global_permissions_as_collection')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('collection', 'ability'),)


class DefaultGlobalPermission(GlobalPermission):
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('ability',),)


class AgentGlobalRolePermission(GlobalPermission):
    agent = models.ForeignKey(Agent, related_name='agent_global_role_permissions_as_agent')
    global_role = models.ForeignKey(GlobalRole, related_name='agent_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('agent', 'global_role'),)


class CollectionGlobalRolePermission(GlobalPermission):
    collection = models.ForeignKey(Collection, related_name='collection_global_role_permissions_as_collection')
    global_role = models.ForeignKey(GlobalRole, related_name='collection_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('collection', 'global_role'),)


class DefaultGlobalRolePermission(GlobalPermission):
    global_role = models.ForeignKey(GlobalRole, related_name='default_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('global_role',),)


class AgentPermission(Permission):
    agent = models.ForeignKey(Agent, related_name='agent_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('agent', 'item', 'ability'),)


class CollectionPermission(Permission):
    collection = models.ForeignKey(Collection, related_name='collection_permissions_as_collection')
    item = models.ForeignKey(Item, related_name='collection_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('collection', 'item', 'ability'),)


class DefaultPermission(Permission):
    item = models.ForeignKey(Item, related_name='default_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('item', 'ability'),)


class AgentRolePermission(Permission):
    agent = models.ForeignKey(Agent, related_name='agent_role_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='agent_role_permissions_as_role')
    class Meta:
        unique_together = (('agent', 'item', 'role'),)


class CollectionRolePermission(Permission):
    collection = models.ForeignKey(Collection, related_name='collection_role_permissions_as_collection')
    item = models.ForeignKey(Item, related_name='collection_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='collection_role_permissions_as_role')
    class Meta:
        unique_together = (('collection', 'item', 'role'),)


class DefaultRolePermission(Permission):
    item = models.ForeignKey(Item, related_name='default_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='default_role_permissions_as_role')
    class Meta:
        unique_together = (('item', 'role'),)


###############################################################################
# Recursive tables
###############################################################################

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


class RecursiveMembership(models.Model):
    parent = models.ForeignKey(Collection, related_name='recursive_memberships_as_parent')
    child = models.ForeignKey(Item, related_name='recursive_memberships_as_child')
    child_memberships = models.ManyToManyField(Membership)
    class Meta:
        unique_together = (('parent', 'child'),)
    @classmethod
    def recursive_add_membership(cls, membership):
        parent = membership.collection
        child = membership.item
        # first connect parent to child
        recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=parent, child=child)
        recursive_membership.child_memberships.add(membership)
        # second connect ancestors to child, via parent
        ancestor_recursive_memberships = RecursiveMembership.objects.filter(child=parent)
        for ancestor_recursive_membership in ancestor_recursive_memberships:
            recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent, child=child)
            recursive_membership.child_memberships.add(membership)
        # third connect parent and ancestors to all descendants
        descendant_recursive_memberships = RecursiveMembership.objects.filter(parent=child)
        for descendant_recursive_membership in descendant_recursive_memberships:
            child_memberships = descendant_recursive_membership.child_memberships.all()
            for ancestor_recursive_membership in ancestor_recursive_memberships:
                recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent, child=descendant_recursive_membership.child)
                for child_membership in child_memberships:
                    recursive_membership.child_memberships.add(child_membership)
            recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=parent, child=descendant_recursive_membership.child)
            for child_membership in child_memberships:
                recursive_membership.child_memberships.add(child_membership)
    @classmethod
    def recursive_remove_edge(cls, parent, child):
        ancestors = Collection.objects.filter(Q(pk__in=RecursiveMembership.objects.filter(child=parent).values('parent').query) | Q(pk=parent.pk))
        descendants = Item.objects.filter(Q(pk__in=RecursiveMembership.objects.filter(parent=child).values('child').query) | Q(pk=child.pk))
        edges = RecursiveMembership.objects.filter(parent__pk__in=ancestors.values('pk').query, child__pk__in=descendants.values('pk').query)
        # first remove all connections between ancestors and descendants
        edges.delete()
        # now add back any real connections between ancestors and descendants that aren't trashed
        memberships = Membership.objects.filter(trashed=False, collection__in=ancestors.values('pk').query, item__in=descendants.values('pk').query).exclude(collection=parent, item=child)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)
    @classmethod
    def recursive_add_collection(cls, collection):
        memberships = Membership.objects.filter(Q(collection=collection) | Q(item=collection), trashed=False)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)
    @classmethod
    def recursive_remove_collection(cls, collection):
        RecursiveMembership.recursive_remove_edge(collection, collection)


###############################################################################
# all_models()
###############################################################################

def all_models():
    result = [x for x in models.loading.get_models() if issubclass(x, Item)]
    return result

def get_model_with_name(name):
    try:
        return (x for x in all_models() if x.__name__ == name).next()
    except StopIteration:
        return None
