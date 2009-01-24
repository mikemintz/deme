"""
This module creates the item type framework, and defines the core item types.
"""

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

__all__ = ['AIMContactMethod', 'AddMemberComment', 'AddressContactMethod', 'Agent', 'AgentGlobalPermission', 'AgentGlobalRolePermission', 'AgentPermission', 'AgentRolePermission', 'AnonymousAgent', 'AuthenticationMethod', 'Collection', 'CollectionGlobalPermission', 'CollectionGlobalRolePermission', 'CollectionPermission', 'CollectionRolePermission', 'Comment', 'ContactMethod', 'CustomUrl', 'DefaultGlobalPermission', 'DefaultGlobalRolePermission', 'DefaultPermission', 'DefaultRolePermission', 'DemeSetting', 'DjangoTemplateDocument', 'Document', 'EditComment', 'EmailContactMethod', 'Excerpt', 'FaxContactMethod', 'FileDocument', 'Folio', 'GlobalPermission', 'GlobalRole', 'GlobalRoleAbility', 'Group', 'HtmlDocument', 'ImageDocument', 'Item', 'Membership', 'POSSIBLE_ABILITIES', 'POSSIBLE_GLOBAL_ABILITIES', 'PasswordAuthenticationMethod', 'Permission', 'Person', 'PhoneContactMethod', 'RecursiveComment', 'RecursiveMembership', 'RemoveMemberComment', 'Role', 'RoleAbility', 'Site', 'SiteDomain', 'Subscription', 'TextComment', 'TextDocument', 'TextDocumentExcerpt', 'Transclusion', 'TrashComment', 'UntrashComment', 'ViewerRequest', 'WebsiteContactMethod', 'all_item_types', 'get_item_type_with_name']

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
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    updater = models.ForeignKey('Agent', related_name='version_items_updated')
    updated_at = models.DateTimeField()

    def __unicode__(self):
        return u'%s[%s.%s] "%s"' % (self.current_item.item_type, self.current_item_id, self.version_number, self.name)


class Item(models.Model):
    """
    Superclass of all item types.
    
    Since everything is an item, this item type provides a unique id across
    all items. This item type also defines some important common structure to
    all items, such as name, description, and details about its creation and
    last update.
    
    Every subclass should define the following attributes:
    
    * immutable_fields: a frozenset of strings representing the names of
      fields which may not be modified after creation (this differs from
      editable=False in that immutable_fields may be customized by a user upon
      creation, but uneditable fields are not to be edited in the front end)
    * relevant_abilities: a frozenset of abilities that are relevant to this
      item type
    * relevant_global_abilities: a frozenset of global abilities that are
      introduced by this item type
    """

    # Setup
    __metaclass__ = ItemMetaClass
    immutable_fields = frozenset()
    relevant_abilities = frozenset(['do_everything', 'comment_on', 'trash', 'view name',
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

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('resource_entry', (), {'viewer': self.item_type.lower(), 'noun': self.pk})

    def downcast(self):
        """
        Return this item as an instance of the actual item type.
        
        For example, if the current item is an Agent, this will return an
        Agent, even though self is an Item. This method always makes a
        single database query.
        """
        item_type = get_item_type_with_name(self.item_type)
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
        recursive_comment_membership = RecursiveComment.objects.filter(parent=self)
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
        will call _after_trash() if the item was previously untrashed.
        """
        if self.trashed:
            return
        self.trashed = True
        self.save()
        self._after_trash(agent)
    trash.alters_data = True

    @transaction.commit_on_success
    def untrash(self, agent):
        """
        Untrash the current Item (the specified agent was responsible). This
        will call _after_untrash() if the item was previously trashed.
        """
        if not self.trashed:
            return
        self.trashed = False
        self.save()
        self._after_untrash(agent)
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
        if not is_new:
            latest_version_number = Item.objects.get(pk=self.pk).version_number
            if overwrite_latest_version:
                self.version_number = latest_version_number
            else:
                self.version_number = latest_version_number + 1
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
            DefaultRolePermission(item=self, role=default_role).save()
            AgentPermission(agent=updater, item=self, ability='do_everything', is_allowed=True).save()

        # Create an EditComment if we're making an edit
        if not is_new and not overwrite_latest_version:
            edit_comment = EditComment(item=self, item_version_number=self.version_number)
            edit_comment.save_versioned(updater=updater)

        if is_new:
            self._after_create()
    save_versioned.alters_data = True

    def _after_create(self):
        """
        This method gets called after the first version of an item is
        created via save_versioned().
        
        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self)._after_create()
        """
        pass
    _after_create.alters_data = True

    def _after_trash(self, agent):
        """
        This method gets called after an item is trashed.
        
        Item types that want to trigger an action after trash should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self)._after_trash()
        """
        # Create a TrashComment
        trash_comment = TrashComment(item=self, item_version_number=self.version_number)
        trash_comment.save_versioned(updater=agent)
    _after_trash.alters_data = True

    def _after_untrash(self, agent):
        """
        This method gets called after an item is untrashed.
        
        Item types that want to trigger an action after untrash should
        override this method, making sure to put a call to super at the top,
        like super(Membership, self)._after_untrash()
        """
        # Create an UntrashComment
        untrash_comment = UntrashComment(item=self, item_version_number=self.version_number)
        untrash_comment.save_versioned(updater=agent)
    _after_untrash.alters_data = True


###############################################################################
# Agents and related item types
###############################################################################

class Agent(Item):
    """
    This item type represents an agent that can "do" things. Often this will
    be a person (see the Person subclass), but actions can also be performed by
    other agents, such as bots and anonymous agents.
    
    Agents are unique in the following ways:
    
    * Agents can be assigned permissions
    * Agents show up in the creator and updater fields of other items
    * Agents can authenticate with Deme using AuthenticationMethods
    * Agents can be contacted via their ContactMethods
    * Agents can subscribe to other items with Subscriptions
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['add_contact_method', 'add_authentication_method', 'login_as', 'view last_online_at'])
    relevant_global_abilities = frozenset(['create Agent'])
    class Meta:
        verbose_name = _('agent')
        verbose_name_plural = _('agents')

    # Fields
    last_online_at = models.DateTimeField(_('last online at'), null=True, blank=True, editable=False)


class AnonymousAgent(Agent):
    """
    This item type is the agent that users of Deme authenticate as by default.
    
    Because every action must be associated with a responsible Agent (e.g.,
    updating an item), we require that users are authenticated as some Agent
    at all times. So if a user never bothers logging in at the website, they
    will automatically be logged in as an AnonymousAgent, even if the website
    says "not logged in".
    
    There should be exactly one AnonymousAgent at all times.
    """

    # Setup
    immutable_fields = Agent.immutable_fields
    relevant_abilities = Agent.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('anonymous agent')
        verbose_name_plural = _('anonymous agents')


class AuthenticationMethod(Item):
    """
    This item type represents an Agent's credentials to login.
    
    For example, there might be a AuthenticationMethod representing my Facebook
    account, a AuthenticationMethod representing my WebAuth account, and a
    AuthenticationMethod representing my OpenID account. Rather than storing
    the login credentials directly in a particular Agent, we allow agents to
    have multiple authentication methods, so that they can login different
    ways. In theory, AuthenticationMethods can also be used to sync profile
    information through APIs. There are subclasses of AuthenticationMethod for
    each different way of authenticating.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['view agent'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('authentication method')
        verbose_name_plural = _('authentication methods')

    # Fields
    agent = models.ForeignKey(Agent, related_name='authentication_methods', verbose_name=_('agent'))


class PasswordAuthenticationMethod(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with a
    username and a password.
    
    The username must be unique across the entire Deme installation. The
    password field is formatted the same as in the User model of the Django
    admin app (algo$salt$hash), and is thus not stored in plain text.
    """

    # Setup
    immutable_fields = AuthenticationMethod.immutable_fields
    relevant_abilities = AuthenticationMethod.relevant_abilities | set(['view username', 'view password', 'view password_question', 'view password_answer', 'edit username', 'edit password', 'edit password_question', 'edit password_answer'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('password authentication method')
        verbose_name_plural = _('password authentication methods')

    # Fields
    username          = models.CharField(_('username'), max_length=255, unique=True)
    password          = models.CharField(_('password'), max_length=128)
    password_question = models.CharField(_('password question'), max_length=255, blank=True)
    password_answer   = models.CharField(_('password answer'), max_length=255, blank=True)

    def set_password(self, raw_password):
        """
        Set the password field by generating a salt and hashing the raw
        password. This method does not make any database writes.
        """
        algo = 'sha1'
        salt = PasswordAuthenticationMethod.get_random_hash()[:5]
        hsh = PasswordAuthenticationMethod.get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)
    set_password.alters_data = True

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        algo, salt, hsh = self.password.split('$')
        return hsh == PasswordAuthenticationMethod.get_hexdigest(algo, salt, raw_password)

    def check_nonced_password(self, hashed_password, nonce):
        """
        Return True if the specified nonced password matches the password field.
        
        This method is here to allow a browser to login over an insecure
        connection. The browser is given the algorithm, the salt, and a random
        nonce, and is supposed to generate the following string, which this
        method generates and compares against:
        
            sha1(nonce, algo(salt, raw_password))
        """
        algo, salt, hsh = self.password.split('$')
        return PasswordAuthenticationMethod.get_hexdigest('sha1', nonce, hsh) == hashed_password

    @classmethod
    def mysql_pre41_password(cls, raw_password):
        """
        Encrypt a password using the same algorithm MySQL used for PASSWORD()
        prior to 4.1.
        
        This method is here to support migrations of account/password data
        from websites that encrypted passwords this way.
        """
        # ported to python from http://packages.debian.org/lenny/libcrypt-mysql-perl
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

    @classmethod
    def get_hexdigest(cls, algorithm, salt, raw_password):
        """
        Return a string of the hexdigest of the given plaintext password and salt
        using the given algorithm ('sha1' or 'mysql_pre41_password').
        """
        from django.utils.encoding import smart_str
        raw_password, salt = smart_str(raw_password), smart_str(salt)
        if algorithm == 'sha1':
            return hashlib.sha1(salt + raw_password).hexdigest()
        elif algorithm == 'mysql_pre41_password':
            return PasswordAuthenticationMethod.mysql_pre41_password(raw_password)
        raise ValueError("Got unknown password algorithm type in password.")

    @classmethod
    def get_random_hash(cls):
        """Return a random 40-digit hexadecimal string. """
        return PasswordAuthenticationMethod.get_hexdigest('sha1', str(random.random()), str(random.random()))


class Person(Agent):
    """
    A Person is an Agent that represents a person in real life.
    """

    # Setup
    immutable_fields = Agent.immutable_fields
    relevant_abilities = Agent.relevant_abilities | set(['view first_name', 'view middle_names', 'view last_name', 'view suffix',
                                                         'edit first_name', 'edit middle_names', 'edit last_name', 'edit suffix'])
    relevant_global_abilities = frozenset(['create Person'])
    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    # Fields
    first_name   = models.CharField(_('first name'), max_length=255)
    middle_names = models.CharField(_('middle names'), max_length=255, blank=True)
    last_name    = models.CharField(_('last name'), max_length=255)
    suffix       = models.CharField(_('suffix'), max_length=255, blank=True)


class ContactMethod(Item):
    """
    A ContactMethod belongs to an Agent and contains details on how to contact
    them. Like Document, ContactMethod is meant to be abstract, so users should
    always create subclasses rather than creating raw ContactMethods.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['agent'])
    relevant_abilities = Item.relevant_abilities | set(['add_subscription', 'view agent'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('contact method')
        verbose_name_plural = _('contact methods')

    # Fields
    agent = models.ForeignKey(Agent, related_name='contact_methods', verbose_name=_('agent'))


class EmailContactMethod(ContactMethod):
    """
    An EmailContactMethod is a ContactMethod that specifies an email address.
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view email', 'edit email'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('email contact method')
        verbose_name_plural = _('email contact methods')

    # Fields
    email = models.EmailField(_('email address'), max_length=320)


class PhoneContactMethod(ContactMethod):
    """
    A PhoneContactMethod is a ContactMethod that specifies a phone number.
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view phone', 'edit phone'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('phone contact method')
        verbose_name_plural = _('phone contact methods')

    # Fields
    phone = models.CharField(_('phone number'), max_length=20)


class FaxContactMethod(ContactMethod):
    """
    A FaxContactMethod is a ContactMethod that specifies a fax number.
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view fax', 'edit fax'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('fax contact method')
        verbose_name_plural = _('fax contact methods')

    # Fields
    fax = models.CharField(_('fax number'), max_length=20)


class WebsiteContactMethod(ContactMethod):
    """
    A WebsiteContactMethod is a ContactMethod that specifies a website URL.
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view url', 'edit url'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('website contact method')
        verbose_name_plural = _('website contact methods')

    # Fields
    url = models.CharField(_('website URL'), max_length=255)


class AIMContactMethod(ContactMethod):
    """
    An AIMContactMethod is a ContactMethod that specifies an AIM screen name.
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view screen_name', 'edit screen_name'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('AIM contact method')
        verbose_name_plural = _('AIM contact methods')

    # Fields
    screen_name = models.CharField(_('AIM screen name'), max_length=255)


class AddressContactMethod(ContactMethod):
    """
    An AddressContactMethod is a ContactMethod that specifies a physical
    address (or mailing address).
    """

    # Setup
    immutable_fields = ContactMethod.immutable_fields
    relevant_abilities = ContactMethod.relevant_abilities | set(['view street1', 'view street2', 'view city', 'view state',
                                                                 'view country', 'view zip', 'edit street1', 'edit street2',
                                                                 'edit city', 'edit state', 'edit country', 'edit zip'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('address contact method')
        verbose_name_plural = _('address contact methods')

    # Fields
    street1 = models.CharField(_('street 1'), max_length=255, blank=True)
    street2 = models.CharField(_('street 2'), max_length=255, blank=True)
    city    = models.CharField(_('city'), max_length=255, blank=True)
    state   = models.CharField(_('state'), max_length=255, blank=True)
    country = models.CharField(_('country'), max_length=255, blank=True)
    zip     = models.CharField(_('zip code'), max_length=20, blank=True)


class Subscription(Item):
    """
    A Subscription is a relationship between an Item and a ContactMethod,
    indicating that all comments on the item should be sent to the contact
    method as notifications.
    
    If deep=True and the item is a Collection, then comments on all items in
    the collection (direct or indirect) will be sent in addition to comments on
    the collection itself.
    
    If notify_text=True, TextComments will be included.
    
    If notify_edit=True, EditComments, TrashComments, UntrashComments,
    AddMemberComments, and RemoveMemberComments will be included.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['contact_method', 'item'])
    relevant_abilities = Item.relevant_abilities | set(['view contact_method', 'view item', 'view deep', 'view notify_text',
                                                        'view notify_edit', 'edit deep', 'edit notify_text', 'edit notify_edit'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        unique_together = (('contact_method', 'item'),)

    # Fields
    contact_method = models.ForeignKey(ContactMethod, related_name='subscriptions', verbose_name=_('contact method'))
    item           = models.ForeignKey(Item, related_name='subscriptions_to', verbose_name=_('item'))
    deep           = models.BooleanField('deep subscription', default=False)
    notify_text    = models.BooleanField('notify about text comments', default=True)
    notify_edit    = models.BooleanField('notify about edits', default=False)


###############################################################################
# Collections and related item types
###############################################################################

class Collection(Item):
    """
    A Collection is an Item that represents an unordered set of other items.
    
    Collections just use pointers from Memberships to represent their contents,
    so multiple Collections can point to the same contained items.
    
    Collections "directly" contain items via Memberships, but they also
    "indirectly" contain items via chained Memberships (see the
    RecursiveMembership model). If Collection 1 directly contains Collection 2
    which directly contains Item 3, then Collection 1 indirectly contains
    Item 3.
    
    It is possible for there to be circular memberships. Collection 1 might
    contain Collection 2 and Collection 2 might contain Collection 1. This
    will not cause any errors: it simply means that Collection 1 indirectly
    contains itself.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['modify_membership', 'add_self', 'remove_self'])
    relevant_global_abilities = frozenset(['create Collection'])
    class Meta:
        verbose_name = _('collection')
        verbose_name_plural = _('collections')

    def all_contained_collection_members(self, recursive_filter=None):
        """
        Return a QuerySet for all items that are either directly or indirectly
        contained by self (using RecursiveMembership).

        If a recursive_filter is specified, use it to filter which
        RecursiveMemberships can be used to infer an item's membership in this
        collection. Often, one will use a permission filter so that only those
        RecursiveMemberships that the Agent is allowed to view will be used.
        """
        recursive_memberships = RecursiveMembership.objects.filter(parent=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return Item.objects.filter(pk__in=recursive_memberships.values('child').query)

    def _after_trash(self, agent):
        super(Collection, self)._after_trash(agent)
        # Update the RecursiveMembership to indicate this Collection is gone
        RecursiveMembership.recursive_remove_collection(self)
    _after_trash.alters_data = True

    def _after_untrash(self, agent):
        super(Collection, self)._after_untrash(agent)
        # Update the RecursiveMembership to indicate this Collection exists
        RecursiveMembership.recursive_add_collection(self)
    _after_untrash.alters_data = True


class Group(Collection):
    """
    A group is a collection of Agents.
    
    A group has a folio that is used for collaboration among members.
    """

    # Setup
    immutable_fields = Collection.immutable_fields
    relevant_abilities = Collection.relevant_abilities
    relevant_global_abilities = frozenset(['create Group'])
    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def _after_create(self):
        super(Group, self)._after_create()
        # Create a folio for this group
        folio = Folio(group=self)
        folio.save_versioned(updater=self.updater)
    _after_create.alters_data = True


class Folio(Collection):
    """
    A folio is a special collection that belongs to a group.
    """

    # Setup
    immutable_fields = Collection.immutable_fields | set(['group'])
    relevant_abilities = Collection.relevant_abilities | set(['view group'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('folio')
        verbose_name_plural = _('folios')

    # Fields
    group = models.ForeignKey(Group, related_name='folios', unique=True, editable=False, verbose_name=_('group'))


class Membership(Item):
    """
    A Membership is a relationship between a collection and one of its items.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['item', 'collection'])
    relevant_abilities = (Item.relevant_abilities | set(['view item', 'view collection'])) - set(['trash'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('membership')
        verbose_name_plural = _('memberships')
        unique_together = (('item', 'collection'),)

    # Fields
    item       = models.ForeignKey(Item, related_name='memberships', verbose_name=_('item'))
    collection = models.ForeignKey(Collection, related_name='child_memberships', verbose_name=_('collection'))

    def _after_create(self):
        super(Membership, self)._after_create()
        # Update the RecursiveMembership to indicate this Membership exists
        RecursiveMembership.recursive_add_membership(self)
        # Create an AddMemberComment to indicate a member was added to the collection
        add_member_comment = AddMemberComment(item=self.collection, item_version_number=self.collection.version_number, membership=self)
        add_member_comment.save_versioned(updater=self.creator)
    _after_create.alters_data = True

    def _after_trash(self, agent):
        super(Membership, self)._after_trash(agent)
        # Update the RecursiveMembership to indicate this Membership is gone
        RecursiveMembership.recursive_remove_edge(self.collection, self.item)
        # Create a RemoveMemberComment to indicate a member was removed from the collection
        remove_member_comment = RemoveMemberComment(item=self.collection, item_version_number=self.collection.version_number, membership=self)
        remove_member_comment.save_versioned(updater=agent)
    _after_trash.alters_data = True

    def _after_untrash(self, agent):
        super(Membership, self)._after_untrash(agent)
        # Update the RecursiveMembership to indicate this Membership exists
        RecursiveMembership.recursive_add_membership(self)
        # Create an AddMemberComment to indicate a member was added to the collection
        add_member_comment = AddMemberComment(item=self.collection, item_version_number=self.collection.version_number, membership=self)
        add_member_comment.save_versioned(updater=agent)
    _after_untrash.alters_data = True


###############################################################################
# Documents
###############################################################################

class Document(Item):
    """
    A Document is an Item that is meant can be a unit of collaborative work.
    
    Document is meant to be abstract, so users should always create subclasses
    rather than creating raw Documents.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')


class TextDocument(Document):
    """
    A TextDocument is a Document that has a body that stores arbitrary text.
    """

    # Setup
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view body', 'edit body', 'add_transclusion'])
    relevant_global_abilities = frozenset(['create TextDocument'])
    class Meta:
        verbose_name = _('text document')
        verbose_name_plural = _('text documents')

    # Fields
    body = models.TextField(_('body'), blank=True)


class DjangoTemplateDocument(TextDocument):
    """
    This item type is a TextDocument that stores Django template code. It can
    display a fully customized page on Deme. This is primarily useful for
    customizing the layout of some or all pages, but it can also be used to
    make pages that can display content not possible in other Documents.
    """

    # Setup
    immutable_fields = TextDocument.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | set(['view layout', 'view override_default_layout',
                                                                'edit layout', 'edit override_default_layout'])
    relevant_global_abilities = frozenset(['create DjangoTemplateDocument'])
    class Meta:
        verbose_name = _('Django template document')
        verbose_name_plural = _('Django template documents')

    # Fields
    layout = models.ForeignKey('DjangoTemplateDocument', related_name='django_template_documents_with_layout', null=True, blank=True, verbose_name=_('layout'))
    override_default_layout = models.BooleanField(_('override default layout'), default=False)


class HtmlDocument(TextDocument):
    """
    An HtmlDocument is a TextDocument that renders its body as HTML.
    """

    # Setup
    immutable_fields = TextDocument.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities
    relevant_global_abilities = frozenset(['create HtmlDocument'])
    class Meta:
        verbose_name = _('HTML document')
        verbose_name_plural = _('HTML documents')


class FileDocument(Document):
    """
    A FileDocument is a Document that stores a file on the filesystem (could be
    an MP3 or a Microsoft Word Document). It is intended for all binary data,
    which does not belong in a TextDocument (even though it is technically
    possible).
    
    Subclasses of FileDocument may be able to understand various
    file formats and add metadata and extra functionality.
    """

    # Setup
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view datafile', 'edit datafile'])
    relevant_global_abilities = frozenset(['create FileDocument'])
    class Meta:
        verbose_name = _('file document')
        verbose_name_plural = _('file documents')

    # Fields
    datafile = models.FileField(_('data file'), upload_to='filedocument/%Y/%m/%d', max_length=255)


class ImageDocument(FileDocument):
    """
    An ImageDocument is a FileDocument that stores an image.
    
    Right now, the only difference is that viewers know the file can be
    displayed as an image. In the future, this may add metadata like EXIF data
    and thumbnails.
    """

    # Setup
    immutable_fields = FileDocument.immutable_fields
    relevant_abilities = FileDocument.relevant_abilities
    relevant_global_abilities = frozenset(['create ImageDocument'])
    class Meta:
        verbose_name = _('image document')
        verbose_name_plural = _('image documents')


###############################################################################
# Annotations (Transclusions, Comments, and Excerpts)
###############################################################################

class Transclusion(Item):
    """
    A Transclusion is an embedded reference from a location in a specific
    version of a TextDocument to another Item.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['from_item', 'from_item_version_number', 'to_item'])
    relevant_abilities = Item.relevant_abilities | set(['view from_item', 'view from_item_version_number',
                                                        'view from_item_index', 'view to_item', 'edit from_item_index'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('transclusion')
        verbose_name_plural = _('transclusions')

    # Fields
    from_item                = models.ForeignKey(TextDocument, related_name='transclusions_from', verbose_name=_('from item'))
    from_item_version_number = models.PositiveIntegerField(_('from item version number'))
    from_item_index          = models.PositiveIntegerField(_('from item index'))
    to_item                  = models.ForeignKey(Item, related_name='transclusions_to', verbose_name=_('to item'))


class Comment(Item):
    """
    A Comment is a unit of discussion about an Item.
    
    Each comment specifies the commented item and version number. Like
    Document, Comment is meant to be abstract, so users should always create
    subclasses rather than creating raw Comments.
    
    Currently, users can only create TextComments. All other Comment types are
    automatically generated by Deme in response to certain actions (such as
    edits and trashings).
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['item'])
    relevant_abilities = Item.relevant_abilities | set(['view item', 'view item_version_number'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    # Fields
    item                = models.ForeignKey(Item, related_name='comments', verbose_name=_('item'))
    item_version_number = models.PositiveIntegerField(_('item version number'))

    def original_item(self):
        """
        Return the original item that was commented on in this thread.
        
        For example, if this is a reply to a reply to a comment on X, this
        method will return X. This method uses the RecursiveComment table.
        """
        parent_pks_query = RecursiveComment.objects.filter(child=self).values('parent').query
        comment_pks_query = Comment.objects.all().values('pk').query
        return Item.objects.exclude(pk__in=comment_pks_query).get(pk__in=parent_pks_query)

    def all_parents_in_thread(self, include_parent_collections=False, recursive_filter=None):
        """
        Return a QuerySet of all direct and indirect parents in this thread.
        
        If include_parent_collections=True, also include all Collections
        containing self or parents in this thread, either through direct or
        indirect membership. If a recursive_filter is specified, use it to
        filter which RecursiveMemberships can be used to infer an item's
        membership in this collection. Often, one will use a permission filter
        so that only those RecursiveMemberships that the Agent is allowed to
        view will be used.
        """
        thread_parent_pks_query = RecursiveComment.objects.filter(child=self).values('parent').query
        thread_parent_filter = Q(pk__in=thread_parent_pks_query)
        if not include_parent_collections:
            return Item.objects.filter(thread_parent_filter)

        recursive_memberships = RecursiveMembership.objects.filter(child__in=thread_parent_pks_query)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        collection_filter = Q(pk__in=recursive_memberships.values('parent').query)

        return Item.objects.filter(thread_parent_filter | collection_filter)

    def subscription_filter_for_comment_type(self):
        """
        Return a filter (Q node) for Subscriptions that are supposed to be
        notified about this comment type. Only the item type is considered
        (e.g., whether it's a TextComment or and EditComment).
        """
        if isinstance(self, TextComment):
            return Q(notify_text=True)
        elif isinstance(self, EditComment):
            return Q(notify_edit=True)
        elif isinstance(self, TrashComment):
            return Q(notify_edit=True)
        elif isinstance(self, UntrashComment):
            return Q(notify_edit=True)
        elif isinstance(self, AddMemberComment):
            return Q(notify_edit=True)
        elif isinstance(self, RemoveMemberComment):
            return Q(notify_edit=True)
        else:
            return Q(pk__isnull=False)

    def notification_email(self, email_contact_method):
        """
        Return an EmailMessage with the notification that should be sent to the
        specified EmailContactMethod. If there is no Subscription, or the Agent
        with the subscription is not allowed to receive the notification,
        return None.
        """
        agent = email_contact_method.agent
        import permissions
        permission_cache = permissions.PermissionCache()

        # First, decide if we're allowed to get this notification at all
        comment_type_q = self.subscription_filter_for_comment_type()
        def direct_subscriptions():
            parent_pks_query = self.all_parents_in_thread().filter(trashed=False).values('pk').query
            return Subscription.objects.filter(comment_type_q, item__in=parent_pks_query, trashed=False)
        def deep_subscriptions():
            if permission_cache.agent_can_global(agent, 'do_everything'):
                recursive_filter = None
            else:
                visible_memberships = Membership.objects.filter(permission_cache.filter_items(agent, 'view item'))
                recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
            parent_pks_query = self.all_parents_in_thread(True, recursive_filter).filter(trashed=False).values('pk').query
            return Subscription.objects.filter(comment_type_q, item__in=parent_pks_query, deep=True, trashed=False)
        if not direct_subscriptions() and not deep_subscriptions():
            return None

        # Now get the fields we are allowed to view
        item = self.item
        topmost_item = self.original_item()
        item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': item.item_type.lower(), 'noun': item.pk}))
        topmost_item_url = 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('resource_entry', kwargs={'viewer': topmost_item.item_type.lower(), 'noun': topmost_item.pk}))
        comment_name = self.name if permission_cache.agent_can(agent, 'view name', self) else 'PERMISSION DENIED'
        if isinstance(self, TextComment):
            comment_body = self.body if permission_cache.agent_can(agent, 'view body', self) else 'PERMISSION DENIED'
        item_name = item.name if permission_cache.agent_can(agent, 'view name', item) else 'PERMISSION DENIED'
        topmost_item_name = topmost_item.name if permission_cache.agent_can(agent, 'view name', topmost_item) else 'PERMISSION DENIED'
        creator_name = self.creator.name if permission_cache.agent_can(agent, 'view name', self.creator) else 'PERMISSION DENIED'

        # Generate the subject and body
        if isinstance(self, TextComment):
            subject = 'Re: [%s] %s' % (comment_name, topmost_item_name)
            body = '%s commented on %s\n%s\n\n%s' % (creator_name, topmost_item_name, topmost_item_url, comment_body)
        elif isinstance(self, EditComment):
            subject = 'Re: [Edited] %s' % (item_name,)
            body = '%s edited %s\n%s' % (creator_name, item_name, item_url)
        elif isinstance(self, TrashComment):
            subject = 'Re: [Trashed] %s' % (item_name,)
            body = '%s trashed %s\n%s' % (creator_name, item_name, item_url)
        elif isinstance(self, UntrashComment):
            subject = 'Re: [Untrashed] %s' % (item_name,)
            body = '%s untrashed %s\n%s' % (creator_name, item_name, item_url)
        elif isinstance(self, AddMemberComment):
            subject = 'Re: [Member Added] %s' % (item_name,)
            body = '%s added a member to %s\n%s' % (creator_name, item_name, item_url)
        elif isinstance(self, RemoveMemberComment):
            subject = 'Re: [Member Removed] %s' % (item_name,)
            body = '%s removed a member from %s\n%s' % (creator_name, item_name, item_url)
        else:
            return None

        # Finally, put together the EmailMessage
        from_email_address = '%s@%s' % (self.pk, settings.NOTIFICATION_EMAIL_HOSTNAME)
        from_email = formataddr((creator_name, from_email_address))
        reply_to_email = formataddr((comment_name, from_email_address))
        to_email = formataddr((agent.name, email_contact_method.email))
        headers = {}
        headers['Reply-To'] = reply_to_email
        messageid = lambda x: '<%s-%s@%s>' % (x.pk, x.created_at.strftime("%Y%m%d%H%M%S"), settings.NOTIFICATION_EMAIL_HOSTNAME)
        headers['Message-ID'] = messageid(self)
        headers['In-Reply-To'] = messageid(self.item)
        headers['References'] = '%s %s' % (messageid(topmost_item), messageid(self.item))
        return EmailMessage(subject=subject, body=body, from_email=from_email, to=[to_email], headers=headers)

    def _after_create(self):
        super(Comment, self)._after_create()

        # Update the RecursiveComment to indicate this Comment exists
        RecursiveComment.recursive_add_comment(self)

        # Email everyone subscribed to items this comment is relevant for
        comment_type_q = self.subscription_filter_for_comment_type()
        direct_subscriptions = Subscription.objects.filter(comment_type_q,
                                                           item__in=self.all_parents_in_thread().filter(trashed=False).values('pk').query,
                                                           trashed=False)
        deep_subscriptions = Subscription.objects.filter(comment_type_q,
                                                         item__in=self.all_parents_in_thread(True).filter(trashed=False).values('pk').query,
                                                         deep=True,
                                                         trashed=False)
        direct_q = Q(pk__in=direct_subscriptions.values('contact_method').query)
        deep_q = Q(pk__in=deep_subscriptions.values('contact_method').query)
        email_contact_methods = EmailContactMethod.objects.filter(direct_q | deep_q, trashed=False)
        messages = [self.notification_email(email_contact_method) for email_contact_method in email_contact_methods]
        messages = [x for x in messages if x is not None]
        if messages:
            smtp_connection = SMTPConnection()
            smtp_connection.send_messages(messages)
    _after_create.alters_data = True


class TextComment(TextDocument, Comment):
    """
    A TextComment is a Comment and a TextDocument combined. It is currently the
    only form of user-generated comments.
    """

    # Setup
    immutable_fields = TextDocument.immutable_fields | Comment.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | Comment.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('text comment')
        verbose_name_plural = _('text comments')


class EditComment(Comment):
    """
    An EditComment is a Comment that is automatically generated whenever
    an agent edits an item. The commented item is the item that was edited,
    and the commented item version number is the new version that was just
    generated (as opposed to the previous version number).
    """

    # Setup
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('edit comment')
        verbose_name_plural = _('edit comments')


class TrashComment(Comment):
    """
    A TrashComment is a Comment that is automatically generated whenever
    an agent trashes an item. The commented item is the item that was trashed,
    and the commented item version number is the latest version number at the
    time of the trashing.
    """

    # Setup
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('trash comment')
        verbose_name_plural = _('trash comments')


class UntrashComment(Comment):
    """
    An UntrashComment is a Comment that is automatically generated whenever
    an agent untrashes an item. The commented item is the item that was
    trashed, and the commented item version number is the latest version number
    at the time of the untrashing.
    """

    # Setup
    immutable_fields = Comment.immutable_fields
    relevant_abilities = Comment.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('untrash comment')
        verbose_name_plural = _('untrash comments')


class AddMemberComment(Comment):
    """
    An AddMemberComment is a Comment that is automatically generated whenever
    an item is added to a collection. The commented item is the collection, and
    the commented item version number is the latest version number at the time
    of the add. The membership field points to the new Membership.
    
    This comment is generated when Memberships are created and untrashed.
    """

    # Setup
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('add member comment')
        verbose_name_plural = _('add member comments')

    # Fields
    membership = models.ForeignKey(Membership, related_name="add_member_comments", verbose_name=_('membership'))


class RemoveMemberComment(Comment):
    """
    A RemoveMemberComment is a Comment that is automatically generated whenever
    an item is removed from a collection. The commented item is the collection,
    and the commented item version number is the latest version number at the
    time of the remove. The membership field points to the old Membership.
    
    This comment is generated when Memberships are trashed.
    """

    # Setup
    immutable_fields = Comment.immutable_fields | set(['membership'])
    relevant_abilities = Comment.relevant_abilities | set(['view membership'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('remove member comment')
        verbose_name_plural = _('remove member comments')

    # Fields
    membership = models.ForeignKey(Membership, related_name="remove_member_comments", verbose_name=_('membership'))


class Excerpt(Item):
    """
    An Excerpt is an Item that refers to a portion of another Item (or an
    external resource, such as a webpage).
    
    Excerpt is meant to be abstract, so users should always create subclasses
    rather than creating raw Excerpts.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('excerpt')
        verbose_name_plural = _('excerpts')


class TextDocumentExcerpt(Excerpt, TextDocument):
    """
    A TextDocumentExcerpt refers to a contiguous region of text in a version of
    another TextDocument in Deme.
    
    The body field contains the excerpted region, and the start_index and
    length identify the character position of this region within the specified
    TextDocument.
    """

    # Setup
    immutable_fields = Excerpt.immutable_fields \
                     | TextDocument.immutable_fields \
                     | set(['text_document','text_document_version_number', 'start_index', 'length', 'body'])
    relevant_abilities = Excerpt.relevant_abilities \
                       | (TextDocument.relevant_abilities - set(['edit body'])) \
                       | set(['view text_document', 'view text_document_version_number', 'view start_index', 'view length']) 
    relevant_global_abilities = frozenset(['create TextDocumentExcerpt'])
    class Meta:
        verbose_name = _('text document excerpt')
        verbose_name_plural = _('text document excerpts')

    # Fields
    text_document                = models.ForeignKey(TextDocument, related_name='text_document_excerpts', verbose_name=_('text document'))
    text_document_version_number = models.PositiveIntegerField(_('text document version number'))
    start_index                  = models.PositiveIntegerField(_('start index'))
    length                       = models.PositiveIntegerField(_('length'))


###############################################################################
# Viewer aliases
###############################################################################


class ViewerRequest(Item):
    """
    A ViewerRequest is represents a particular action at a particular viewer
    (basically a URL, although its stored more explicitly). It specifies a
    viewer (just a string, since viewers are not Items), an action (like "view"
    or "edit"), an item that is referred to (or null for collection-wide
    actions), a query_string if you want to pass parameters to the viewer, and
    a format.
    
    A ViewerRequest is supposed to be abstract, so users can only create Sites
    and CustomUrls.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities | set(['add_sub_path', 'view aliased_item', 'view viewer', 'view action',
                                                        'view query_string', 'view format', 'edit aliased_item', 'edit viewer',
                                                        'edit action', 'edit query_string', 'edit format'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('viewer request')
        verbose_name_plural = _('viewer requests')

    # Fields
    viewer       = models.CharField(_('viewer'), max_length=255)
    action       = models.CharField(_('action'), max_length=255)
    # If aliased_item is null, it is a collection action
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests', null=True, blank=True, verbose_name=_('aliased item'))
    query_string = models.CharField(_('query string'), max_length=1024, null=True, blank=True)
    format       = models.CharField(_('format'), max_length=255, default='html')

    def calculate_full_path(self):
        """Return a tuple (site, custom_urls) where custom_urls is a list."""
        req = self.downcast()
        if isinstance(req, Site):
            return (req, [])
        elif isinstance(req, CustomUrl):
            parent_path = req.parent_url.calculate_full_path()
            return (parent_path[0], parent_path[1] + [req])


class Site(ViewerRequest):
    """
    A Site is a ViewerRequest that represents a logical website with URLs.
    
    A Site can have multiple SiteDomains, but ordinarily it would just have one
    (multiple domains are useful if you want to enable www.example.com and
    example.com). Multiple Sites on the same Deme installation share the same
    Items with the same unique ids, but they resolve URLs differently so each
    Site can have a different page for /mike. If you go to the base URL of a
    site (like http://example.com/), you see the ViewerRequest that this Site
    inherits from.
    """

    # Setup
    immutable_fields = ViewerRequest.immutable_fields
    relevant_abilities = ViewerRequest.relevant_abilities | set(['view default_layout', 'edit default_layout'])
    relevant_global_abilities = frozenset(['create Site'])
    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')

    # Fields
    default_layout = models.ForeignKey(DjangoTemplateDocument, related_name='sites_with_layout', null=True, blank=True, verbose_name=_('default layout'))


class SiteDomain(Item):
    """
    A SiteDomain represents a hostname for a Site.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['hostname', 'site'])
    relevant_abilities = Item.relevant_abilities | set(['view hostname', 'view site'])
    relevant_global_abilities = frozenset(['create SiteDomain'])
    class Meta:
        verbose_name = _('site domain')
        verbose_name_plural = _('site domains')
        unique_together = (('site', 'hostname'),)

    # Fields
    hostname = models.CharField(_('hostname'), max_length=255)
    site     = models.ForeignKey(Site, related_name='site_domains', verbose_name=_('site'))


class CustomUrl(ViewerRequest):
    """
    A CustomUrl is a ViewerRequest that represents a specific path.
    
    Each CustomUrl has a parent ViewerRequest (it will be the Site if this
    CustomUrl is the first path component) and a string for the path component.
    So when a user visits http://example.com/abc/def/ghi, Deme looks for a
    CustomUrl with name "ghi" with a parent with name "def" with a parent with
    name "abc" with a parent Site with a SiteDomain "example.com".
    """

    # Setup
    immutable_fields = ViewerRequest.immutable_fields | set(['parent_url', 'path'])
    relevant_abilities = ViewerRequest.relevant_abilities | set(['view parent_url', 'view path'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('custom URL')
        verbose_name_plural = _('custom URLs')
        unique_together = (('parent_url', 'path'),)

    # Fields
    parent_url = models.ForeignKey(ViewerRequest, related_name='child_urls', verbose_name=_('parent URL'))
    path       = models.CharField(_('path'), max_length=255)


###############################################################################
# Misc item types
###############################################################################

class DemeSetting(Item):
    """
    This item type stores global settings for the Deme installation.
    
    Each DemeSetting has a unique key and an arbitrary value. Since values are
    strings of limited size, settings that involve a lot of text (e.g., a
    default layout) should have a value pointing to an item that contains the
    data (e.g., the id of a document).
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['key'])
    relevant_abilities = Item.relevant_abilities | set(['view key', 'view value', 'edit value'])
    relevant_global_abilities = frozenset()
    class Meta:
        verbose_name = _('Deme setting')
        verbose_name_plural = _('Deme settings')

    # Fields
    key   = models.CharField(_('key'), max_length=255, unique=True)
    value = models.CharField(_('value'), max_length=255, blank=True)

    @classmethod
    def get(cls, key):
        """
        Return the value of the DemeSetting with the specified key, or None if
        it is trashed or no such DemeSetting exists.
        """
        try:
            setting = cls.objects.get(key=key)
            if setting.trashed:
                return None
            return setting.value
        except ObjectDoesNotExist:
            return None

    @classmethod
    def set(cls, key, value, agent):
        """
        Set the DemeSetting with the specified key to the specified value,
        such that the agent is the creator/updater. This may result in
        creating a new DemeSetting, updating an existing DemeSetting, or
        untrashing a trashed DemeSetting.
        """
        try:
            setting = cls.objects.get(key=key)
        except ObjectDoesNotExist:
            setting = cls(name=key, key=key)
        if setting.value != value:
            setting.value = value
            setting.save_versioned(updater=agent)
        if setting.trashed:
            setting.untrash(agent)


###############################################################################
# Permissions
###############################################################################

class POSSIBLE_ABILITIES_ITER(object):
    def __iter__(self):
        choices = set()
        for item_type in all_item_types():
            choices = choices | set([(x,x) for x in item_type.relevant_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

class POSSIBLE_GLOBAL_ABILITIES_ITER(object):
    def __iter__(self):
        choices = set()
        for item_type in all_item_types():
            choices = choices | set([(x,x) for x in item_type.relevant_global_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

POSSIBLE_ABILITIES = POSSIBLE_ABILITIES_ITER()
POSSIBLE_GLOBAL_ABILITIES = POSSIBLE_GLOBAL_ABILITIES_ITER()


class Role(Item):
    """
    A Role is a list of abilities (encapsulated in RoleAbilities).
    
    Roles do not refer to specific items, but just specific abilities. One
    example might be a "department admin" Role which has every ability for
    department-related items turned on. Roles are not necessary for the
    permission system, but they prevent users from having to manually configure
    each ability they want to assign between an agent and an item.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create Role'])
    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')


class GlobalRole(Item):
    """
    A GlobalRole is the same as a Role but for global permissions instead of
    item permissions.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    relevant_abilities = Item.relevant_abilities
    relevant_global_abilities = frozenset(['create GlobalRole'])
    class Meta:
        verbose_name = _('global role')
        verbose_name_plural = _('global roles')


class RoleAbility(Item):
    """
    A RoleAbility belongs to a Role and specifies an ability string, as well as
    a boolean for whether this ability is granted or denied.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['role', 'ability'])
    relevant_abilities = Item.relevant_abilities | set(['view role', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create RoleAbility'])
    class Meta:
        verbose_name = _('role ability')
        verbose_name_plural = _('role abilities')
        unique_together = (('role', 'ability'),)

    # Fields
    role       = models.ForeignKey(Role, related_name='role_abilities', verbose_name=_('role'))
    ability    = models.CharField(_('ability'), max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(_('is allowed'), default=True, db_index=True)


class GlobalRoleAbility(Item):
    """
    A GlobalRoleAbility is the same as a RoleAbility but for global permissions
    instead of item permissions.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['global_role', 'ability'])
    relevant_abilities = Item.relevant_abilities | set(['view global_role', 'view ability', 'view is_allowed', 'edit is_allowed'])
    relevant_global_abilities = frozenset(['create GlobalRoleAbility'])
    class Meta:
        verbose_name = _('global role ability')
        verbose_name_plural = _('global role abilities')
        unique_together = (('global_role', 'ability'),)

    # Fields
    global_role = models.ForeignKey(GlobalRole, related_name='role_abilities', verbose_name=_('global role'))
    ability     = models.CharField(_('ability'), max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed  = models.BooleanField(_('is allowed'), default=True, db_index=True)


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

class RecursiveComment(models.Model):
    """
    This table contains all pairs (item, comment) such that comment is
    directly or indirectly a comment on item.
    
    For example if A is an Item, B is a Comment on A, and C is a comment on B,
    then this table will contain (A,B) (B,C) and (A,C).
    """
    parent = models.ForeignKey(Item, related_name='recursive_comments_as_parent', verbose_name=_('parent'))
    child  = models.ForeignKey(Comment, related_name='recursive_comments_as_child', verbose_name=_('child'))
    class Meta:
        unique_together = (('parent', 'child'),)

    @classmethod
    def recursive_add_comment(cls, comment):
        """
        Update the table to reflect that the given comment was created.
        """
        parent = comment.item
        ancestors = Item.objects.filter(Q(pk__in=RecursiveComment.objects.filter(child=parent).values('parent').query)
                                        | Q(pk=parent.pk))
        for ancestor in ancestors:
            RecursiveComment(parent=ancestor, child=comment).save()


class RecursiveMembership(models.Model):
    """
    This table contains all pairs (collection, item) such that item is directly
    or indirectly a member of collection.
    
    Each RecursiveMembership row also contains a many-to-many set of
    Memberships (child_memberships) such that there exists an path of
    memberships from the child to the parent where the first membership in the
    path is in child_memberships.
    
    When Collections or Memberships are trashed, this table is updated as if
    the Collection or Membership did not exist.
    
    For example if A is a Collection, and B is a Collection (which is a member
    of A), and C is an Item (which is a member of B), and D is an Item (which
    is a member of A and B), then the table will contain:
    
    (A,B) child_memberships={(A,B)}
    (B,C) child_memberships={(B,C)}
    (A,C) child_memberships={(B,C)}
    (A,D) child_memberships={(A,D),(B,D))}
    (B,D) child_memberships={(B,D)}
    """
    parent            = models.ForeignKey(Collection, related_name='recursive_memberships_as_parent', verbose_name=_('parent'))
    child             = models.ForeignKey(Item, related_name='recursive_memberships_as_child', verbose_name=_('child'))
    child_memberships = models.ManyToManyField(Membership, verbose_name=_('child memberships'))
    class Meta:
        unique_together = (('parent', 'child'),)

    @classmethod
    def recursive_add_membership(cls, membership):
        """
        Update the table to reflect that the given membership was created (or
        untrashed).
        """
        parent = membership.collection
        child = membership.item
        # Connect parent to child
        recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=parent, child=child)
        recursive_membership.child_memberships.add(membership)
        # Connect ancestors to child, via parent
        ancestor_recursive_memberships = RecursiveMembership.objects.filter(child=parent)
        for ancestor_recursive_membership in ancestor_recursive_memberships:
            recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent, child=child)
            recursive_membership.child_memberships.add(membership)
        # Connect parent and ancestors to all descendants
        descendant_recursive_memberships = RecursiveMembership.objects.filter(parent=child)
        for descendant_recursive_membership in descendant_recursive_memberships:
            child_memberships = descendant_recursive_membership.child_memberships.all()
            # Indirect ancestors
            for ancestor_recursive_membership in ancestor_recursive_memberships:
                recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=ancestor_recursive_membership.parent,
                                                                                          child=descendant_recursive_membership.child)
                for child_membership in child_memberships:
                    recursive_membership.child_memberships.add(child_membership)
            # Parent
            recursive_membership, created = RecursiveMembership.objects.get_or_create(parent=parent, child=descendant_recursive_membership.child)
            for child_membership in child_memberships:
                recursive_membership.child_memberships.add(child_membership)

    @classmethod
    def recursive_remove_edge(cls, parent, child):
        """
        Update the table to reflect that child is no longer directly a member
        of parent.
        """
        ancestors = Collection.objects.filter(Q(pk__in=RecursiveMembership.objects.filter(child=parent).values('parent').query)
                                              | Q(pk=parent.pk))
        descendants = Item.objects.filter(Q(pk__in=RecursiveMembership.objects.filter(parent=child).values('child').query)
                                          | Q(pk=child.pk))
        edges = RecursiveMembership.objects.filter(parent__in=ancestors.values('pk').query, child__in=descendants.values('pk').query)
        # Remove all connections between ancestors and descendants
        edges.delete()
        # Add back any real connections between ancestors and descendants that aren't trashed
        memberships = Membership.objects.filter(trashed=False,
                                                collection__in=ancestors.values('pk').query,
                                                item__in=descendants.values('pk').query).exclude(collection=parent, item=child)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)

    @classmethod
    def recursive_add_collection(cls, collection):
        """
        Update the table to reflect that the given collection was created or
        untrashed.
        """
        memberships = Membership.objects.filter(Q(collection=collection) | Q(item=collection), trashed=False)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)

    @classmethod
    def recursive_remove_collection(cls, collection):
        """
        Update the table to reflect that the given collection was trashed.
        """
        RecursiveMembership.recursive_remove_edge(collection, collection)


###############################################################################
# all_item_types()
###############################################################################

def all_item_types():
    """
    Return a list of every item type (as a class).
    """
    result = [x for x in models.loading.get_models() if issubclass(x, Item)]
    return result

def get_item_type_with_name(name):
    """
    Return the item type class with the given name (case-sensitive), or return
    None if there is no item type with the name.
    """
    try:
        return (x for x in all_item_types() if x.__name__ == name).next()
    except StopIteration:
        return None

