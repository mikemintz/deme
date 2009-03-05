"""
This module creates the item type framework, and defines the core item types.
"""

from django.db import models, transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import SMTPConnection, EmailMessage
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from email.utils import formataddr
import datetime
import settings
import copy
import random
import hashlib

__all__ = ['AIMContactMethod', 'AddressContactMethod', 'Agent', 'AgentGlobalPermission', 'AgentItemPermission', 'AnonymousAgent', 'AuthenticationMethod', 'Collection', 'CollectionGlobalPermission', 'CollectionItemPermission', 'Comment', 'ContactMethod', 'CustomUrl', 'EveryoneGlobalPermission', 'EveryoneItemPermission', 'DemeSetting', 'DjangoTemplateDocument', 'Document', 'EmailContactMethod', 'Excerpt', 'FaxContactMethod', 'FileDocument', 'Folio', 'GlobalPermission', 'Group', 'GroupAgent', 'HtmlDocument', 'ImageDocument', 'Item', 'Membership', 'OpenidAuthenticationMethod', 'POSSIBLE_ITEM_ABILITIES', 'POSSIBLE_GLOBAL_ABILITIES', 'PasswordAuthenticationMethod', 'ItemPermission', 'Person', 'PhoneContactMethod', 'RecursiveComment', 'RecursiveMembership', 'Site', 'Subscription', 'TextComment', 'TextDocument', 'TextDocumentExcerpt', 'Transclusion', 'ViewerRequest', 'WebauthAuthenticationMethod', 'WebsiteContactMethod', 'all_item_types', 'get_item_type_with_name', 'ActionNotice', 'RelationActionNotice', 'DeactivateActionNotice', 'ReactivateActionNotice', 'DestroyActionNotice', 'CreateActionNotice', 'EditActionNotice']

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
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            return result
        if name == 'Item':
            result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)
            result.Version = ItemVersion
            ItemVersion.NotVersion = result
            return result

        # Create the non-versioned class
        for key, value in attrs.iteritems():
            if isinstance(value, models.Field):
                # We must be able to nullify this field if we destroy the item
                value.null = True
                if not value.has_default():
                    if isinstance(value, models.DateTimeField):
                        value.default = datetime.datetime.utcfromtimestamp(0)
                    elif isinstance(value, models.BooleanField):
                        value.default = False
                    elif isinstance(value, models.IntegerField):
                        value.default = 1
                    else:
                        value.default = ''
                #TODO we need to prevent fields from normally being null now :(
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
    name = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

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
    * introduced_abilities: a frozenset of abilities that are relevant to this
      item type
    * introduced_global_abilities: a frozenset of global abilities that are
      introduced by this item type
    """

    # Setup
    __metaclass__ = ItemMetaClass
    immutable_fields = frozenset()
    introduced_abilities = frozenset(['do_anything', 'comment_on', 'view_action_notices', 'delete', 'view name',
                                      'view description', 'view creator', 'view created_at', 'edit name', 'edit description'])
    introduced_global_abilities = frozenset(['do_anything'])
    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')

    # Fields
    version_number = models.PositiveIntegerField(_('version number'), default=1, editable=False)
    item_type      = models.CharField(_('item type'), max_length=255, editable=False)
    active         = models.BooleanField(_('active'), default=True, editable=False, db_index=True)
    destroyed      = models.BooleanField(_('destroyed'), default=False, editable=False)
    creator        = models.ForeignKey('Agent', related_name='items_created', default='', editable=False, verbose_name=_('creator'), null=True)
    created_at     = models.DateTimeField(_('created at'), default=datetime.datetime.utcfromtimestamp(0), editable=False, null=True)
    name           = models.CharField(_('name'), max_length=255, default='Untitled', null=True)
    description    = models.CharField(_('description'), max_length=255, default='', blank=True, null=True)

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type, self.pk, self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('item_url', (), {'viewer': self.item_type.lower(), 'noun': self.pk})

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
        Return all active Collections containing self directly or indirectly.
        
        A Collection does not indirectly contain itself by default.
        
        If a recursive_filter is specified, use it to filter which
        RecursiveMemberships can be used to infer self's membership in a
        collection. Often, one will use a permission filter so that only those
        RecursiveMemberships that the Agent is allowed to view will be used.
        """
        recursive_memberships = RecursiveMembership.objects.filter(child=self)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        return Collection.objects.filter(active=True, pk__in=recursive_memberships.values('parent').query)

    def all_comments(self):
        """
        Return all active Comments made directly or indirectly on self.
        """
        recursive_comment_membership = RecursiveComment.objects.filter(parent=self)
        return Comment.objects.filter(active=True, pk__in=recursive_comment_membership.values('child').query)

    def all_parents_in_thread(self, include_parent_collections=False, recursive_filter=None):
        """
        Return a QuerySet including self and all direct and indirect parents in
        this thread. If self is a Comment, this will return self, the parent,
        the grandparent, so on up to (and including) the original item. If self
        is not a Comment, this should only self (unless
        include_parent_collections is True as explained below).
        
        If include_parent_collections=True, also include all Collections
        containing self or parents in this thread, either through direct or
        indirect membership. If a recursive_filter is specified, use it to
        filter which RecursiveMemberships can be used to infer an item's
        membership in this collection. Often, one will use a permission filter
        so that only those RecursiveMemberships that the Agent is allowed to
        view will be used.
        """
        thread_items = Item.objects.filter(Q(pk=self.pk) | Q(pk__in=RecursiveComment.objects.filter(child=self).values('parent').query))
        if not include_parent_collections:
            return thread_items

        recursive_memberships = RecursiveMembership.objects.filter(child__in=thread_items.values('pk').query)
        if recursive_filter is not None:
            recursive_memberships = recursive_memberships.filter(recursive_filter)
        collection_filter = Q(pk__in=recursive_memberships.values('parent').query)

        return Item.objects.filter(Q(pk__in=thread_items.values('pk').query) | collection_filter)

    def original_item_in_thread(self):
        """
        Return the original item that was commented on in this thread. If this
        is not a Comment, just return self.
        
        For example, if this is a reply to a reply to a comment on X, this
        method will return X. This method uses the RecursiveComment table.
        """
        parent_pks_query = RecursiveComment.objects.filter(child=self).values('parent').query
        comment_pks_query = Comment.objects.all().values('pk').query
        try:
            return Item.objects.exclude(pk__in=comment_pks_query).get(pk__in=parent_pks_query)
        except ObjectDoesNotExist:
            return self

    def copy_fields_from_version(self, version_number):
        """
        Set the fields of self to what they were at the given version number.
        This method does not make any database writes.
        """
        if self.destroyed:
            self.version_number = int(version_number)
            return
        itemversion = type(self).Version.objects.get(current_item=self, version_number=version_number)
        fields = {}
        for field in itemversion._meta.fields:
            if not (field.primary_key or isinstance(field, models.OneToOneField)):
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
            if not (field.primary_key or isinstance(field, models.OneToOneField)):
                try:
                    fields[field.name] = getattr(self, field.name)
                except ObjectDoesNotExist:
                    fields[field.name] = None
        for key, val in fields.iteritems():
            setattr(itemversion, key, val)
    copy_fields_to_itemversion.alters_data = True

    @transaction.commit_on_success
    def deactivate(self, action_agent, action_summary='', action_time=None):
        """
        Deactivate the current Item (the specified agent was responsible with
        the given summary at the given time). This will call _after_deactivate
        if the item was previously active.
        """
        action_time = action_time or datetime.datetime.now()
        if not self.active:
            return
        self.active = False
        self.save()
        # Execute callbacks
        self._after_deactivate(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        DeactivateActionNotice(item=self, item_version_number=self.version_number, creator=action_agent, created_at=action_time, description=action_summary).save()
        old_item = self
        new_item = None
        RelationActionNotice.create_notices(action_agent, action_summary, action_time, item=self, existed_before=True, existed_after=False)
    deactivate.alters_data = True

    @transaction.commit_on_success
    def reactivate(self, action_agent, action_summary='', action_time=None):
        """
        Reactivate the current Item (the specified agent was responsible with
        the given summary at the given time). This will call _after_reactivate
        if the item was previously inactive.
        """
        action_time = action_time or datetime.datetime.now()
        if self.active:
            return
        self.active = True
        self.save()
        # Execute callbacks
        self._after_reactivate(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        ReactivateActionNotice(item=self, item_version_number=self.version_number, creator=action_agent, created_at=action_time, description=action_summary).save()
        old_item = None
        new_item = self
        RelationActionNotice.create_notices(action_agent, action_summary, action_time, item=self, existed_before=False, existed_after=True)
    reactivate.alters_data = True

    @transaction.commit_on_success
    def destroy(self, action_agent, action_summary='', action_time=None):
        """
        Nullify the fields of this item (the specified agent was responsible
        with the given summary at the given time) and delete all versions.
        The item must already be inactive and cannot have already been
        destroyed. This will call _after_destroy.
        """
        action_time = action_time or datetime.datetime.now()
        if self.destroyed or self.active:
            return
        # Set all non-special fields to null
        self.destroyed = True
        for field in self._meta.fields:
            if field.primary_key or isinstance(field, models.OneToOneField):
                continue
            elif field.name in ('version_number', 'item_type', 'active', 'destroyed'):
                continue
            elif field.null:
                setattr(self, field.name, None)
            else:
                raise Exception("un-nullable field tried to be destroyed: %s" % field.name) #TODO what to do?
        self.save()
        # Remove all versions
        type(self).Version.objects.filter(current_item=self).delete()
        # Remove all existing action notices
        self.action_notices.all().delete()
        # Remove all permissions on this item
        self.agent_item_permissions_as_item.all().delete()
        self.collection_item_permissions_as_item.all().delete()
        self.everyone_item_permissions_as_item.all().delete()
        AgentItemPermission.objects.filter(agent=self).delete()
        CollectionItemPermission.objects.filter(collection=self).delete()
        AgentGlobalPermission.objects.filter(agent=self).delete()
        CollectionGlobalPermission.objects.filter(collection=self).delete()
        # Execute callbacks
        self._after_destroy(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        DestroyActionNotice(item=self, item_version_number=self.version_number, creator=action_agent, created_at=action_time, description=action_summary).save()
    destroy.alters_data = True

    @transaction.commit_on_success
    def save_versioned(self, action_agent, action_summary='', action_time=None, first_agent=False, create_permissions=True):
        """
        Save the current item (the specified agent was responsible with the
        given summary at the given time), making sure to keep track of versions.
        
        Use this method instead of save() because it will keep things
        consistent with versions and special fields. This will set
        created_at to the current time (or action_time parameter) if this is a
        creation.
        
        If first_agent=True, then this method assumes you are creating the
        first item (which should be an Agent). It is necessary to save the
        first item as an Agent in this way so that every Item has a valid
        creator pointer.
        
        If create_permissions=True, then this method will automatically create
        reasonable permissions.
        TODO: figure out what those permissions should really be
        
        This will call _after_create or _after_edit, depending on whether the
        item already existed.
        """
        action_time = action_time or datetime.datetime.now()
        is_new = not self.pk

        # Update the item
        self.item_type = type(self).__name__
        if first_agent:
            action_agent = self
        if is_new:
            self.creator = action_agent
            self.created_at = action_time
        else:
            latest_version_number = Item.objects.get(pk=self.pk).version_number
            self.version_number = latest_version_number + 1
        if first_agent:
            self.creator_id = 1
        self.save()

        # Create the new item version
        new_version = type(self).Version()
        self.copy_fields_to_itemversion(new_version)
        new_version.save()

        # Create the permissions
        if create_permissions and is_new:
            AgentItemPermission(agent=action_agent, item=self, ability='do_anything', is_allowed=True).save()

        # Execute callbacks
        if is_new:
            self._after_create(action_agent, action_summary, action_time)
        else:
            self._after_edit(action_agent, action_summary, action_time)

        # Create relevant ActionNotices
        if is_new:
            CreateActionNotice(item=self, item_version_number=self.version_number, creator=action_agent, created_at=action_time, description=action_summary).save()
            if self.active:
                RelationActionNotice.create_notices(action_agent, action_summary, action_time, item=self, existed_before=False, existed_after=True)
        else:
            EditActionNotice(item=self, item_version_number=self.version_number, creator=action_agent, created_at=action_time, description=action_summary).save()
            if self.active:
                RelationActionNotice.create_notices(action_agent, action_summary, action_time, item=self, existed_before=True, existed_after=True)
    save_versioned.alters_data = True

    def _after_create(self, action_agent, action_summary, action_time):
        """
        This method gets called after the first version of an item is
        created via save_versioned().
        
        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_create(action_agent, action_summary, action_time)
        """
        pass
    _after_create.alters_data = True

    def _after_edit(self, action_agent, action_summary, action_time):
        """
        This method gets called after an existing item is edited via
        save_versioned().
        
        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_edit(action_agent, action_summary, action_time)
        """
        pass
    _after_edit.alters_data = True

    def _after_deactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called after an item is deactivated.
        
        Item types that want to trigger an action after deactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_deactivate(action_agent, action_summary, action_time)
        """
        pass
    _after_deactivate.alters_data = True

    def _after_reactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called after an item is reactivated.
        
        Item types that want to trigger an action after reactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_reactivate(action_agent, action_summary, action_time)
        """
        pass
    _after_reactivate.alters_data = True

    def _after_destroy(self, action_agent, action_summary, action_time):
        """
        This method gets called after an item is destroyed.
        
        Item types that want to trigger an action after destroy should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_destroy(action_agent, action_summary, action_time)
        """
        pass
    _after_destroy.alters_data = True


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
    * Agents show up in the creator fields of other items
    * Agents can authenticate with Deme using AuthenticationMethods
    * Agents can be contacted via their ContactMethods
    * Agents can subscribe to other items with Subscriptions
    """

    # Setup
    immutable_fields = Item.immutable_fields
    introduced_abilities = frozenset(['add_contact_method', 'add_authentication_method', 'login_as', 'view last_online_at'])
    introduced_global_abilities = frozenset(['create Agent'])
    class Meta:
        verbose_name = _('agent')
        verbose_name_plural = _('agents')

    # Fields
    last_online_at = models.DateTimeField(_('last online at'), null=True, blank=True, default=None, editable=False) #TODO resolve issue where NULL doesn't imply destroyed item


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
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('anonymous agent')
        verbose_name_plural = _('anonymous agents')


class GroupAgent(Agent):
    """
    This item type is an Agent that acts on behalf of an entire group. It can't
    do anything that other agents can't do. It's significance is just symbolic:
    by being associated with a group, the actions taken by the group agent are
    seen as collective action of the group members. In general, permission to
    login_as the group agent will be limited to powerful members of the group.
    
    There should be exactly one GroupAgent for every group.
    """

    # Setup
    immutable_fields = Agent.immutable_fields | set(['group'])
    introduced_abilities = frozenset(['view group'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('group agent')
        verbose_name_plural = _('group agents')

    # Fields
    group = models.ForeignKey('Group', related_name='group_agents', unique=True, editable=False, verbose_name=_('group'))


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
    introduced_abilities = frozenset(['view agent'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('authentication method')
        verbose_name_plural = _('authentication methods')

    # Fields
    agent = models.ForeignKey(Agent, related_name='authentication_methods', verbose_name=_('agent'))


class OpenidAuthenticationMethod(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with an
    OpenID.
    
    The openid url must be unique across the entire Deme installation.
    """

    # Setup
    immutable_fields = AuthenticationMethod.immutable_fields | set(['openid_url'])
    introduced_abilities = frozenset(['view openid_url'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('OpenID authentication method')
        verbose_name_plural = _('OpenID authentication methods')

    # Fields
    openid_url = models.CharField(_('OpenID URL'), max_length=2047, unique=True)


class WebauthAuthenticationMethod(AuthenticationMethod):
    """
    This is an AuthenticationMethod that allows a user to log on with
    Stanford's WebAuth system.
    
    The username must be unique across the entire Deme installation.
    """

    # Setup
    immutable_fields = AuthenticationMethod.immutable_fields | set(['username'])
    introduced_abilities = frozenset(['view username'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('WebAuth authentication method')
        verbose_name_plural = _('WebAuth authentication methods')

    # Fields
    username = models.CharField(_('username'), max_length=255, unique=True)


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
    introduced_abilities = frozenset(['view username', 'view password', 'view password_question', 'view password_answer',
                                      'edit username', 'edit password', 'edit password_question', 'edit password_answer'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view first_name', 'view middle_names', 'view last_name', 'view suffix',
                                      'edit first_name', 'edit middle_names', 'edit last_name', 'edit suffix'])
    introduced_global_abilities = frozenset(['create Person'])
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
    them. ContactMethod is meant to be abstract, so developers should always
    create subclasses rather than creating raw ContactMethods.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['agent'])
    introduced_abilities = frozenset(['add_subscription', 'view agent'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view email', 'edit email'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view phone', 'edit phone'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view fax', 'edit fax'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view url', 'edit url'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view screen_name', 'edit screen_name'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view street1', 'view street2', 'view city', 'view state',
                                      'view country', 'view zip', 'edit street1', 'edit street2',
                                      'edit city', 'edit state', 'edit country', 'edit zip'])
    introduced_global_abilities = frozenset()
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
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['contact_method', 'item'])
    introduced_abilities = frozenset(['view contact_method', 'view item', 'view deep', 'edit deep'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        unique_together = (('contact_method', 'item'),)

    # Fields
    contact_method = models.ForeignKey(ContactMethod, related_name='subscriptions', verbose_name=_('contact method'))
    item           = models.ForeignKey(Item, related_name='subscriptions_to', verbose_name=_('item'))
    deep           = models.BooleanField('deep subscription', default=False)


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
    introduced_abilities = frozenset(['modify_membership', 'add_self', 'remove_self'])
    introduced_global_abilities = frozenset(['create Collection'])
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

    def _after_deactivate(self, action_agent, action_summary, action_time):
        super(Collection, self)._after_deactivate(action_agent, action_summary, action_time)
        # Update the RecursiveMembership to indicate this Collection is gone
        RecursiveMembership.recursive_remove_collection(self)
    _after_deactivate.alters_data = True

    def _after_reactivate(self, action_agent, action_summary, action_time):
        super(Collection, self)._after_reactivate(action_agent, action_summary, action_time)
        # Update the RecursiveMembership to indicate this Collection exists
        RecursiveMembership.recursive_add_collection(self)
    _after_reactivate.alters_data = True


class Group(Collection):
    """
    A group is a collection of Agents.
    
    A group has a folio that is used for collaboration among members.
    """

    # Setup
    immutable_fields = Collection.immutable_fields
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Group'])
    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def _after_create(self, action_agent, action_summary, action_time):
        super(Group, self)._after_create(action_agent, action_summary, action_time)
        # Create a folio for this group
        folio = Folio(group=self, name='%s folio' % self.name)
        folio.save_versioned(action_agent, action_summary, action_time)
        # Create a group agent for this group
        group_agent = GroupAgent(group=self, name='%s agent' % self.name)
        group_agent.save_versioned(action_agent, action_summary, action_time)
    _after_create.alters_data = True


class Folio(Collection):
    """
    A folio is a special collection that belongs to a group.
    """

    # Setup
    immutable_fields = Collection.immutable_fields | set(['group'])
    introduced_abilities = frozenset(['view group'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view item', 'view collection'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('membership')
        verbose_name_plural = _('memberships')
        unique_together = (('item', 'collection'),)

    # Fields
    item       = models.ForeignKey(Item, related_name='memberships', verbose_name=_('item'))
    collection = models.ForeignKey(Collection, related_name='child_memberships', verbose_name=_('collection'))

    def _after_create(self, action_agent, action_summary, action_time):
        super(Membership, self)._after_create(action_agent, action_summary, action_time)
        if self.collection.active:
            # Update the RecursiveMembership to indicate this Membership exists
            RecursiveMembership.recursive_add_membership(self)
    _after_create.alters_data = True

    def _after_deactivate(self, action_agent, action_summary, action_time):
        super(Membership, self)._after_deactivate(action_agent, action_summary, action_time)
        # Update the RecursiveMembership to indicate this Membership is gone
        RecursiveMembership.recursive_remove_edge(self.collection, self.item)
    _after_deactivate.alters_data = True

    def _after_reactivate(self, action_agent, action_summary, action_time):
        super(Membership, self)._after_reactivate(action_agent, action_summary, action_time)
        if self.collection.active:
            # Update the RecursiveMembership to indicate this Membership exists
            RecursiveMembership.recursive_add_membership(self)
    _after_reactivate.alters_data = True


###############################################################################
# Documents
###############################################################################

class Document(Item):
    """
    A Document is an Item that is meant can be a unit of collaborative work.
    
    Document is meant to be abstract, so developers should always create
    subclasses rather than creating raw Documents.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')


class TextDocument(Document):
    """
    A TextDocument is a Document that has a body that stores arbitrary text.
    """

    # Setup
    immutable_fields = Document.immutable_fields
    introduced_abilities = frozenset(['view body', 'edit body', 'add_transclusion'])
    introduced_global_abilities = frozenset(['create TextDocument'])
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
    introduced_abilities = frozenset(['view layout', 'view override_default_layout',
                                    'edit layout', 'edit override_default_layout'])
    introduced_global_abilities = frozenset(['create DjangoTemplateDocument'])
    class Meta:
        verbose_name = _('Django template document')
        verbose_name_plural = _('Django template documents')

    # Fields
    layout = models.ForeignKey('DjangoTemplateDocument', related_name='django_template_documents_with_layout', null=True, blank=True, default=None, verbose_name=_('layout')) #TODO resolve issue where NULL doesn't imply destroyed item
    override_default_layout = models.BooleanField(_('override default layout'), default=False)


class HtmlDocument(TextDocument):
    """
    An HtmlDocument is a TextDocument that renders its body as HTML.
    """

    # Setup
    immutable_fields = TextDocument.immutable_fields
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HtmlDocument'])
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
    introduced_abilities = frozenset(['view datafile', 'edit datafile'])
    introduced_global_abilities = frozenset(['create FileDocument'])
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
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create ImageDocument'])
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
    introduced_abilities = frozenset(['view from_item', 'view from_item_version_number',
                                      'view from_item_index', 'view to_item', 'edit from_item_index'])
    introduced_global_abilities = frozenset()
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
    Document, Comment is meant to be abstract, so developers should always
    create subclasses rather than creating raw Comments.
    
    Currently, users can only create TextComments.
    """

    # Setup
    immutable_fields = Item.immutable_fields | set(['item'])
    introduced_abilities = frozenset(['view item', 'view item_version_number'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    # Fields
    item                = models.ForeignKey(Item, related_name='comments', verbose_name=_('item'))
    item_version_number = models.PositiveIntegerField(_('item version number'))

    def _after_create(self, action_agent, action_summary, action_time):
        super(Comment, self)._after_create(action_agent, action_summary, action_time)
        # Update the RecursiveComment to indicate this Comment exists
        RecursiveComment.recursive_add_comment(self)
    _after_create.alters_data = True

    def _after_destroy(self, action_agent, action_summary, action_time):
        super(Comment, self)._after_destroy(action_agent, action_summary, action_time)
        # Update the RecursiveComment to indicate this Comment is gone
        RecursiveComment.recursive_remove_comment(self)
    _after_destroy.alters_data = True



class TextComment(TextDocument, Comment):
    """
    A TextComment is a Comment and a TextDocument combined. It is currently the
    only form of user-generated comments.
    """

    # Setup
    immutable_fields = TextDocument.immutable_fields | Comment.immutable_fields
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('text comment')
        verbose_name_plural = _('text comments')


class Excerpt(Item):
    """
    An Excerpt is an Item that refers to a portion of another Item (or an
    external resource, such as a webpage).
    
    Excerpt is meant to be abstract, so developers should always create
    subclasses rather than creating raw Excerpts.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
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
    immutable_fields = Excerpt.immutable_fields | TextDocument.immutable_fields  | set(['text_document'])
    introduced_abilities = frozenset(['view text_document', 'view text_document_version_number', 'view start_index', 'view length',
                                      'edit text_document_version_number', 'edit start_index', 'edit length']) 
    introduced_global_abilities = frozenset(['create TextDocumentExcerpt'])
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
    A ViewerRequest represents a particular action at a particular viewer
    (basically a URL, although its stored more explicitly). It specifies a
    viewer (just a string, since viewers are not Items), an action (like "view"
    or "edit"), an item that is referred to (or null for collection-wide
    actions), a query_string if you want to pass parameters to the viewer, and
    a format.
    
    A ViewerRequest is supposed to be abstract, so users can only create
    Sites and CustomUrls.
    """

    # Setup
    immutable_fields = Item.immutable_fields
    introduced_abilities = frozenset(['add_sub_path', 'view aliased_item', 'view viewer', 'view action',
                                      'view query_string', 'view format', 'edit aliased_item', 'edit viewer',
                                      'edit action', 'edit query_string', 'edit format'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('viewer request')
        verbose_name_plural = _('viewer requests')

    # Fields
    viewer       = models.CharField(_('viewer'), max_length=255)
    action       = models.CharField(_('action'), max_length=255)
    # If aliased_item is null, it is a collection action
    aliased_item = models.ForeignKey(Item, related_name='viewer_requests', null=True, blank=True, default=None, verbose_name=_('aliased item')) #TODO resolve issue where NULL doesn't imply destroyed item
    query_string = models.CharField(_('query string'), max_length=1024, blank=True)
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
    
    Multiple Sites on the same Deme installation share the same Items with the
    same unique ids, but they resolve URLs differently so each Site can have a
    different page for /mike. If you go to the base URL of a site (like
    http://example.com/), you see the ViewerRequest that this Site inherits
    from.
    """

    # Setup
    immutable_fields = ViewerRequest.immutable_fields
    introduced_abilities = frozenset(['view hostname', 'edit hostname', 'view default_layout', 'edit default_layout'])
    introduced_global_abilities = frozenset(['create Site'])
    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')

    # Fields
    hostname = models.CharField(_('hostname'), max_length=255, unique=True)
    default_layout = models.ForeignKey(DjangoTemplateDocument, related_name='sites_with_layout', null=True, blank=True, default=None, verbose_name=_('default layout')) #TODO resolve issue where NULL doesn't imply destroyed item


class CustomUrl(ViewerRequest):
    """
    A CustomUrl is a ViewerRequest that represents a specific path.
    
    Each CustomUrl has a parent ViewerRequest (it will be the Site if this
    CustomUrl is the first path component) and a string for the path component.
    So when a user visits http://example.com/abc/def/ghi, Deme looks for a
    CustomUrl with name "ghi" with a parent with name "def" with a parent with
    name "abc" with a parent Site with hostname "example.com".
    """

    # Setup
    immutable_fields = ViewerRequest.immutable_fields | set(['parent_url', 'path'])
    introduced_abilities = frozenset(['view parent_url', 'view path'])
    introduced_global_abilities = frozenset()
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
    introduced_abilities = frozenset(['view key', 'view value', 'edit value'])
    introduced_global_abilities = frozenset()
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
        it is inactive or no such DemeSetting exists.
        """
        try:
            setting = cls.objects.get(key=key)
            if not setting.active:
                return None
            return setting.value
        except ObjectDoesNotExist:
            return None

    @classmethod
    def set(cls, key, value, action_agent):
        """
        Set the DemeSetting with the specified key to the specified value,
        such that the agent is the creator. This may result in creating a new
        DemeSetting, updating an existing DemeSetting, or reactivating an
        inactive DemeSetting.
        """
        try:
            setting = cls.objects.get(key=key)
        except ObjectDoesNotExist:
            setting = cls(name=key, key=key)
        if setting.value != value:
            setting.value = value
            setting.save_versioned(action_agent=action_agent)
        if not setting.active:
            setting.reactivate(action_agent=action_agent)


###############################################################################
# Action notices
###############################################################################

class ActionNotice(models.Model):
    item                = models.ForeignKey(Item, related_name='action_notices', verbose_name=_('item'))
    item_version_number = models.PositiveIntegerField(_('item version number'))
    creator             = models.ForeignKey(Agent, related_name='action_notices_created', verbose_name=_('creator'))
    created_at          = models.DateTimeField(_('created at'))
    description         = models.CharField(_('description'), max_length=255, blank=True)

    def notification_reply_item(self):
        """
        Return the item that comments created about this notice (via replying
        to a notification email for this notice) are replies to.
        """
        return self.item

    def notification_email(self, email_contact_method):
        """
        Return an EmailMessage with the notification that should be sent to the
        specified EmailContactMethod. If there is no Subscription, or the Agent
        with the subscription is not allowed to receive the notification,
        return None.
        """
        agent = email_contact_method.agent
        from permissions import PermissionCache
        permission_cache = PermissionCache()

        #TODO this code looks funny.. why doesn't it check the agent in the subscription?
        # First, decide if we're allowed to get this notification at all
        def direct_subscriptions():
            item_parent_pks_query = self.item.all_parents_in_thread().values('pk').query
            creator_parent_pks_query = self.creator.all_parents_in_thread().values('pk').query
            return Subscription.objects.filter(Q(item__in=item_parent_pks_query) | Q(item__in=creator_parent_pks_query), active=True)
        def deep_subscriptions():
            if permission_cache.agent_can_global(agent, 'do_anything'):
                recursive_filter = None
            else:
                visible_memberships = permission_cache.filter_items(agent, 'view item', Membership.objects)
                recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
            item_parent_pks_query = self.item.all_parents_in_thread(True, recursive_filter).values('pk').query
            creator_parent_pks_query = self.creator.all_parents_in_thread(True, recursive_filter).values('pk').query
            return Subscription.objects.filter(Q(item__in=item_parent_pks_query) | Q(item__in=creator_parent_pks_query), deep=True, active=True)
        if not permission_cache.agent_can(agent, 'view_action_notices', self.item):
            return None
        if isinstance(self, RelationActionNotice):
            if not permission_cache.agent_can(agent, 'view %s' % self.from_field_name, self.from_item):
                return None
        if not direct_subscriptions() and not deep_subscriptions():
            return None

        # Now get the fields we are allowed to view
        item = self.item
        reply_item = self.notification_reply_item()
        topmost_item = item.original_item_in_thread()
        def get_url(x):
            return 'http://%s%s' % (settings.DEFAULT_HOSTNAME, reverse('item_url', kwargs={'viewer': x.item_type.lower(), 'noun': x.pk}))
        item_name = item.name if permission_cache.agent_can(agent, 'view name', item) else u'%s %d' % (item.item_type, item.pk)
        reply_item_name = reply_item.name if permission_cache.agent_can(agent, 'view name', reply_item) else u'%s %d' % (reply_item.item_type, reply_item.pk)
        topmost_item_name = topmost_item.name if permission_cache.agent_can(agent, 'view name', topmost_item) else u'%s %d' % (topmost_item.item_type, topmost_item.pk)
        creator_name = self.creator.name if permission_cache.agent_can(agent, 'view name', self.creator) else u'%s %d' % (self.creator.item_type, self.creator.pk)

        # Generate the subject and body
        if isinstance(self, RelationActionNotice):
            from_item_name = self.from_item.name if permission_cache.agent_can(agent, 'view name', self.from_item) else u'%s %d' % (self.from_item.item_type, self.from_item.pk)
            if self.relation_added:
                subject = 'Re: [Relation Added] %s' % (item_name,)
            else:
                subject = 'Re: [Relation Removed] %s' % (item_name,)
            body = 'Thanks to %s, the %s.%s field of %s %s points to %s\n%s\n%s' % (creator_name, self.from_field_model, self.from_field_name, from_item_name, 'now' if self.relation_added else 'no longer', item_name, self.description, get_url(self.from_item))
        elif isinstance(self, DeactivateActionNotice):
            subject = 'Re: [Deactivated] %s' % (item_name,)
            body = '%s deactivated %s\n%s\n%s' % (creator_name, item_name, self.description, get_url(item))
        elif isinstance(self, ReactivateActionNotice):
            subject = 'Re: [Reactivated] %s' % (item_name,)
            body = '%s reactivated %s\n%s\n%s' % (creator_name, item_name, self.description, get_url(item))
        elif isinstance(self, DestroyActionNotice):
            subject = 'Re: [Destroyed] %s' % (item_name,)
            body = '%s destroyed %s\n%s\n%s' % (creator_name, item_name, self.description, get_url(item))
        elif isinstance(self, CreateActionNotice):
            if issubclass(get_item_type_with_name(item.item_type), Comment):
                comment = item.downcast()
                comment_name = comment.name if permission_cache.agent_can(agent, 'view name', comment) else u'%s %d' % (comment.item_type, comment.pk)
                if isinstance(comment, TextComment):
                    comment_body = comment.body if permission_cache.agent_can(agent, 'view body', comment) else '[You do not have permission to view the body of this comment]'
                else:
                    comment_body = ''
                subject = 'Re: [%s] %s' % (comment_name, topmost_item_name)
                body = '%s commented on %s\n%s\n\n%s' % (creator_name, topmost_item_name, get_url(topmost_item), comment_body)
            else:
                subject = 'Re: [Created] %s' % (item_name,)
                body = '%s created %s\n%s\n%s' % (creator_name, item_name, self.description, get_url(item))
        elif isinstance(self, EditActionNotice):
            subject = 'Re: [Edited] %s' % (item_name,)
            body = '%s edited %s\n%s\n%s' % (creator_name, item_name, self.description, get_url(item))
        else:
            return None

        # Finally, put together the EmailMessage
        from_email_address = '%s@%s' % (reply_item.pk, settings.NOTIFICATION_EMAIL_HOSTNAME)
        from_email = formataddr((creator_name, from_email_address))
        reply_to_email = formataddr((reply_item_name, from_email_address))
        to_email = formataddr((agent.name, email_contact_method.email))
        headers = {}
        headers['Reply-To'] = reply_to_email
        messageid = lambda x: '<%s-%s-%s@%s>' % ('notice' if isinstance(x, ActionNotice) else 'item', x.pk, x.created_at.strftime("%Y%m%d%H%M%S"), settings.NOTIFICATION_EMAIL_HOSTNAME)
        if reply_item == item:
            headers['Message-ID'] = messageid(self)
        else:
            headers['Message-ID'] = messageid(reply_item)
        headers['In-Reply-To'] = messageid(item)
        headers['References'] = '%s %s' % (messageid(topmost_item), messageid(item))
        return EmailMessage(subject=subject, body=body, from_email=from_email, to=[to_email], headers=headers)

def action_notice_post_save_handler(sender, **kwargs):
    action_notice = kwargs['instance']
    # Email everyone subscribed to items this notice is relevant for
    direct_subscriptions = Subscription.objects.filter(Q(item__in=action_notice.item.all_parents_in_thread().values('pk').query) |
                                                       Q(item__in=action_notice.creator.all_parents_in_thread().values('pk').query),
                                                       active=True)
    deep_subscriptions = Subscription.objects.filter(Q(item__in=action_notice.item.all_parents_in_thread(True).values('pk').query) |
                                                     Q(item__in=action_notice.creator.all_parents_in_thread(True).values('pk').query),
                                                     deep=True,
                                                     active=True)
    direct_q = Q(pk__in=direct_subscriptions.values('contact_method').query)
    deep_q = Q(pk__in=deep_subscriptions.values('contact_method').query)
    email_contact_methods = EmailContactMethod.objects.filter(direct_q | deep_q, active=True)
    messages = [action_notice.notification_email(email_contact_method) for email_contact_method in email_contact_methods]
    messages = [x for x in messages if x is not None]
    if messages:
        smtp_connection = SMTPConnection()
        smtp_connection.send_messages(messages)


class RelationActionNotice(ActionNotice):
    from_item                = models.ForeignKey(Item, related_name='relation_action_notices_from', verbose_name=_('from item'))
    from_item_version_number = models.PositiveIntegerField(_('from item version number'))
    from_field_name          = models.CharField(_('from field name'), max_length=255)
    from_field_model         = models.CharField(_('from field model'), max_length=255)
    relation_added           = models.BooleanField(_('relation added'))

    def notification_reply_item(self):
        """
        In RelationActionNotices, when someone replies to a notification, it
        should be turned into a comment on from_item, not item.
        
        For example, if we have a RelationActionNotice with from_item=membership
        and item=agent, the reply comment should go to membership, not agent.
        """
        return self.from_item

    @classmethod
    def create_notices(cls, action_agent, action_summary, action_time, item, existed_before, existed_after):
        if existed_before and existed_after:
            old_item = type(item).objects.get(pk=item.pk)
            old_item.copy_fields_from_version(item.version_number - 1)
            new_item = item
        elif existed_before:
            old_item = item
            new_item = None
        elif existed_after:
            old_item = None
            new_item = item
        # Because of multiple inheritance, we need to put the field/model pairs into a set
        fields_and_models = set(item._meta.get_fields_with_model())
        for field, model in fields_and_models:
            if isinstance(field, (models.OneToOneField, models.ManyToManyField)):
                continue
            if field.name == 'creator':
                continue # we do creator stuff separately
            if isinstance(field, models.ForeignKey):
                if model is None:
                    model = type(item)
                if old_item is None:
                    old_value = None
                else:
                    old_value = getattr(old_item, field.name)
                if new_item is None:
                    new_value = None
                else:
                    new_value = getattr(new_item, field.name)
                if new_value != old_value:
                    for value, relation_added in [(old_value, False), (new_value, True)]:
                        if value is not None:
                            action_notice = RelationActionNotice()
                            action_notice.item = value
                            action_notice.item_version_number = value.version_number
                            action_notice.creator = action_agent
                            action_notice.created_at = action_time
                            action_notice.description = action_summary
                            action_notice.from_item = item
                            action_notice.from_item_version_number = item.version_number
                            action_notice.from_field_name = field.name
                            action_notice.from_field_model = model.__name__
                            action_notice.relation_added = relation_added
                            action_notice.save()
signals.post_save.connect(action_notice_post_save_handler, sender=RelationActionNotice, dispatch_uid='RelationActionNotice post_save')
    

class DeactivateActionNotice(ActionNotice):
    pass
signals.post_save.connect(action_notice_post_save_handler, sender=DeactivateActionNotice, dispatch_uid='DeactivateActionNotice post_save')


class ReactivateActionNotice(ActionNotice):
    pass
signals.post_save.connect(action_notice_post_save_handler, sender=ReactivateActionNotice, dispatch_uid='ReactivateActionNotice post_save')


class DestroyActionNotice(ActionNotice):
    pass
signals.post_save.connect(action_notice_post_save_handler, sender=DestroyActionNotice, dispatch_uid='DestroyActionNotice post_save')


class CreateActionNotice(ActionNotice):
    pass
signals.post_save.connect(action_notice_post_save_handler, sender=CreateActionNotice, dispatch_uid='CreateActionNotice post_save')

class EditActionNotice(ActionNotice):
    pass
signals.post_save.connect(action_notice_post_save_handler, sender=EditActionNotice, dispatch_uid='EditActionNotice post_save')


###############################################################################
# Permissions
###############################################################################

class PossibleItemAbilitiesIterable(object):
    """
    Instantiated objects from this class are dynamic iterables, in that each
    time you iterate through them, you get the latest set of item abilities
    (according to the current state of introduced_abilities in the item types).
    
    Each ability is of the form (ability_name, friendly_name).
    """
    def __iter__(self):
        choices = set()
        for item_type in all_item_types():
            choices |= set([(x,x) for x in item_type.introduced_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

class PossibleGlobalAbilitiesIterable(object):
    """
    Instantiated objects from this class are dynamic iterables, in that each
    time you iterate through them, you get the latest set of global abilities
    (according to the current state of introduced_abilities in the item types).
    
    Each ability is of the form (ability_name, friendly_name).
    """
    def __iter__(self):
        choices = set()
        for item_type in all_item_types():
            choices |= set([(x,x) for x in item_type.introduced_global_abilities])
        choices = list(choices)
        choices.sort(key=lambda x: x[1])
        for x in choices:
            yield x

# Iterable of all (ability, friendly_name) item abilities
POSSIBLE_ITEM_ABILITIES = PossibleItemAbilitiesIterable()

# Iterable of all (ability, friendly_name) global abilities
POSSIBLE_GLOBAL_ABILITIES = PossibleGlobalAbilitiesIterable()


class ItemPermission(models.Model):
    """Abstract superclass of all item permissions."""
    ability = models.CharField(max_length=255, choices=POSSIBLE_ITEM_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        abstract = True


class GlobalPermission(models.Model):
    """Abstract superclass of all global permissions."""
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        abstract = True


class AgentGlobalPermission(GlobalPermission):
    """Global permissions assigned directly to agents."""
    agent = models.ForeignKey(Agent, related_name='agent_global_permissions_as_agent')
    class Meta:
        unique_together = (('agent', 'ability'),)


class CollectionGlobalPermission(GlobalPermission):
    """Global permissions assigned to all agents in a given collection."""
    collection = models.ForeignKey(Collection, related_name='collection_global_permissions_as_collection')
    class Meta:
        unique_together = (('collection', 'ability'),)


class EveryoneGlobalPermission(GlobalPermission):
    """Global permissions assigned to all agents in this installation."""
    class Meta:
        unique_together = (('ability',),)


class AgentItemPermission(ItemPermission):
    """Item permissions assigned directly to agents."""
    agent = models.ForeignKey(Agent, related_name='agent_item_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_item_permissions_as_item')
    class Meta:
        unique_together = (('agent', 'item', 'ability'),)


class CollectionItemPermission(ItemPermission):
    """Collection permissions assigned to all agents in a given collection."""
    collection = models.ForeignKey(Collection, related_name='collection_item_permissions_as_collection')
    item = models.ForeignKey(Item, related_name='collection_item_permissions_as_item')
    class Meta:
        unique_together = (('collection', 'item', 'ability'),)


class EveryoneItemPermission(ItemPermission):
    """Item permissions assigned to all agents in this installation."""
    item = models.ForeignKey(Item, related_name='everyone_item_permissions_as_item')
    class Meta:
        unique_together = (('item', 'ability'),)


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
        if comment.destroyed:
            raise Exception("Cannot call recursive_add_comment on destroyed comment") #TODO what do do here? can it happen?
        parent = comment.item
        ancestors = Item.objects.filter(Q(pk__in=RecursiveComment.objects.filter(child=parent).values('parent').query)
                                        | Q(pk=parent.pk))
        for ancestor in ancestors:
            RecursiveComment(parent=ancestor, child=comment).save()

    @classmethod
    def recursive_remove_comment(cls, comment):
        """
        Update the table to reflect that the given comment was destroyed.
        """
        proper_ancestors = Item.objects.filter(pk__in=RecursiveComment.objects.filter(child=comment).values('parent').query)
        descendants = Comment.objects.filter(Q(pk__in=RecursiveComment.objects.filter(parent=comment).values('child').query)
                                             | Q(pk=comment.pk))
        edges = RecursiveComment.objects.filter(parent__in=proper_ancestors.values('pk').query, child__in=descendants.values('pk').query)
        # Remove all connections between proper_ancestors and descendants
        edges.delete()


class RecursiveMembership(models.Model):
    """
    This table contains all pairs (collection, item) such that item is directly
    or indirectly a member of collection.
    
    Each RecursiveMembership row also contains a many-to-many set of
    Memberships (child_memberships) such that there exists an path of
    memberships from the child to the parent where the first membership in the
    path is in child_memberships.
    
    When Collections or Memberships are deactivated, this table is updated as
    if the Collection or Membership did not exist.
    
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
        reactivated).
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
        # Add back any real connections between ancestors and descendants that are active
        memberships = Membership.objects.filter(active=True,
                                                collection__in=ancestors.values('pk').query,
                                                item__in=descendants.values('pk').query).exclude(collection=parent, item=child)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)

    @classmethod
    def recursive_add_collection(cls, collection):
        """
        Update the table to reflect that the given collection was created or
        reactivated.
        """
        memberships = Membership.objects.filter(Q(collection=collection) | Q(item=collection), active=True)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)

    @classmethod
    def recursive_remove_collection(cls, collection):
        """
        Update the table to reflect that the given collection was deactivated.
        """
        RecursiveMembership.recursive_remove_edge(collection, collection)


###############################################################################
# all_item_types()
###############################################################################

def all_item_types():
    """Return a list of every item type (as a class)."""
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

