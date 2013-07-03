"""
This module creates the item type framework, and defines the core item types.
"""

from django.db import models, transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import SMTPConnection, EmailMessage, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst, wrap
from django.template import loader, Context
from django.db.models import signals
from django import forms
from email.utils import formataddr
import datetime
from django.conf import settings
import copy
import html2text
import re

__all__ = ['AIMContactMethod', 'AddressContactMethod', 'Agent',
        'AnonymousAgent', 'AuthenticationMethod',
        'Collection', 'Comment', 'ContactMethod',
        'CustomUrl', 'DemeSetting',
        'DjangoTemplateDocument', 'Document', 'EditLock',
        'EmailContactMethod', 'Excerpt',
        'FaxContactMethod', 'FileDocument', 'Folio',
        'Group', 'GroupAgent', 'HtmlDocument', 'ImageDocument', 'Item', 'Membership',
        'POSSIBLE_ITEM_ABILITIES', 'POSSIBLE_GLOBAL_ABILITIES',
        'POSSIBLE_ITEM_AND_GLOBAL_ABILITIES', 'Person',
        'PhoneContactMethod', 'RecursiveComment', 'RecursiveMembership',
        'Site', 'Subscription', 'TextComment', 'TextDocument',
        'TextDocumentExcerpt', 'Transclusion', 'ViewerRequest',
        'WebsiteContactMethod', 'all_item_types', 'get_item_type_with_name',
        'ActionNotice', 'RelationActionNotice', 'DeactivateActionNotice',
        'ReactivateActionNotice', 'DestroyActionNotice', 'CreateActionNotice',
        'EditActionNotice', 'FixedBooleanField', 'FixedForeignKey',
        'Permission', 'OneToOnePermission', 'OneToSomePermission',
        'OneToAllPermission', 'SomeToOnePermission', 'SomeToSomePermission',
        'SomeToAllPermission', 'AllToOnePermission', 'AllToSomePermission',
        'AllToAllPermission', 'friendly_name_for_ability', 'Webpage']


###############################################################################
# Field types
###############################################################################

class FixedBooleanField(models.NullBooleanField):
    """
    This is a modified NullBooleanField that uses a checkbox-style FormField.
    This is used to replace BooleanFields that are normally not supposed to
    have a null options, but are allowed to have null options for the purpose
    of deleting items. Because Django SVN revision r10456 made it so
    BooleanFields cannot be null, we have to use this instead.
    """

    def __init__(self, *args, **kwargs):
        super(FixedBooleanField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.BooleanField,
            'required': False,
        }
        defaults.update(kwargs)
        return super(FixedBooleanField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.NullBooleanField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)

class FixedForeignKey(models.ForeignKey):
    """
    This is a modified ForeignKey that specifies the abilities required to
    modify the field. The abilities must be had by the action agent on the
    pointee.
    """

    def __init__(self, *args, **kwargs):
        self.required_abilities = kwargs.pop('required_abilities', [])
        super(FixedForeignKey, self).__init__(*args, **kwargs)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.ForeignKey"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)


###############################################################################
# Item framework
###############################################################################

UN_NULLABLE_FIELDS = ['version_number', 'item_type_string', 'active', 'destroyed']

class PossibleViewerNamesIterable(object):
    """
    Instantiated objects from this class are dynamic iterables, in that each
    time you iterate through them, you get the latest set of viewer names.
    """
    def __iter__(self):
        from cms.base_viewer import all_viewer_classes
        choices = [(x.viewer_name, x.viewer_name) for x in all_viewer_classes()]
        choices.sort(key=lambda x: x[0])
        for x in choices:
            yield x

class ItemMetaClass(models.base.ModelBase):
    """
    Metaclass for item types. Takes care of creating parallel versioned classes
    for every item type.
    """
    def __new__(cls, name, bases, attrs):
        # Fix null/defaults so we can nullify fields of destroyed items
        for key, value in attrs.iteritems():
            if isinstance(value, models.Field):
                field = value
                if field.primary_key or isinstance(field, models.OneToOneField):
                    continue
                elif key in UN_NULLABLE_FIELDS:
                    continue
                # We must be able to nullify this field if we destroy the item
                assert not isinstance(field, models.BooleanField), "Use cms.models.FixedBooleanField instead of models.BooleanField for %s.%s" % (name, key)
                assert not (isinstance(field, models.ForeignKey) and type(field).__name__ != 'FixedForeignKey'), "Use cms.models.FixedForeignKey instead of models.ForeignKey for %s.%s" % (name, key)
                field.allowed_to_be_null_before_destroyed = field.null
                field.null = True
                if not field.has_default():
                    if isinstance(field, models.DateTimeField):
                        field.default = datetime.datetime.utcfromtimestamp(0)
                    elif isinstance(field, models.NullBooleanField):
                        field.default = False
                    elif isinstance(field, FixedBooleanField):
                        field.default = False
                    elif isinstance(field, models.IntegerField):
                        field.default = 1
                    else:
                        field.default = ''

        # Create the non-versioned class
        attrs_copy = copy.deepcopy(attrs)
        result = super(ItemMetaClass, cls).__new__(cls, name, bases, attrs)

        # Create the versioned class
        version_name = name + "Version"
        # Versioned classes inherit from other versioned classes
        if name == 'Item':
            version_bases = tuple(bases)
        else:
            version_bases = tuple([x.Version for x in bases if issubclass(x, Item)])
        # Set the attrs for the versioned class
        version_attrs = {'__module__': attrs_copy['__module__']}
        # Copy over mutable fields
        for key, value in attrs_copy.iteritems():
            if isinstance(value, models.Field):
                field = value
                if field.editable and key not in result.all_immutable_fields():
                    # We don't want to waste time indexing versions, except things
                    # specified in ItemVersion like version_number and current_item
                    field.db_index = False
                    # Fix the related_name so we don't have conflicts with the
                    # non-versioned class.
                    if field.rel and field.rel.related_name:
                        field.rel.related_name = 'version_' + field.rel.related_name
                    # We don't want any fields in the versioned class to be unique
                    # since there will be conflicts.
                    field._unique = False
                    version_attrs[key] = field
        # Set up Item.Version specially
        if name == 'Item':
            version_attrs['current_item'] = models.ForeignKey('Item', related_name='versions')
            version_attrs['version_number'] = models.PositiveIntegerField(db_index=True)
            class Meta:
                unique_together = ('current_item', 'version_number')
                ordering = ['version_number']
                get_latest_by = 'version_number'
            version_attrs['Meta'] = Meta
            version_attrs['__unicode__'] = lambda self: u'%s[%s.%s] "%s"' % (self.current_item.item_type_string, self.current_item_id, self.version_number, self.name)
            version_attrs['__doc__'] = "Versioned class for Item, and superclass of all versioned classes."
        version_result = super(ItemMetaClass, cls).__new__(cls, version_name, version_bases, version_attrs)

        # Set the Version field of the class to point to the versioned class
        result.Version = version_result
        version_result.NotVersion = result
        return result

email_local_address_re1 = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')$', re.IGNORECASE)  # domain (lack of)

# Email list address can't be of the form item-# or comment-#
email_local_address_re2 = re.compile(r"^(?!(item|comment)-[0-9]+$)", re.IGNORECASE)

class Item(models.Model):
    """
    Superclass of all item types.

    Since everything is an item, this item type provides a unique id across
    all items. This item type also defines some important common structure to
    all items, such as name, description, and details about its creation and
    last update.

    Every subclass should define the following attributes:

    * introduced_immutable_fields: a frozenset of strings representing the names
      of fields which may not be modified after creation (this differs from
      editable=False in that introduced_immutable_fields may be customized by a
      user upon creation, but uneditable fields are not to be edited in the
      front end)
    * introduced_abilities: a frozenset of abilities that are relevant to this
      item type
    * introduced_global_abilities: a frozenset of global abilities that are
      introduced by this item type
    * dyadic_relations: a dict from field_name1 to (field_name2, relation_name)
      for showing that this item type is really just a dyadic relation between
      the two fields
    """

    # Setup
    __metaclass__ = ItemMetaClass
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['do_anything', 'view_anything', 'edit_anything', 'modify_privacy_settings', 'view_permissions', 'comment_on', 'delete', 'view Item.action_notices', 'view Item.name', 'view Item.description', 'view Item.creator', 'view Item.created_at', 'view Item.default_viewer', 'view Item.email_list_address', 'view Item.email_sets_reply_to_all_subscribers', 'edit Item.name', 'edit Item.description', 'edit Item.default_viewer', 'edit Item.email_list_address', 'edit Item.email_sets_reply_to_all_subscribers'])
    introduced_global_abilities = frozenset(['do_anything', 'view_anything', 'edit_anything'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')

    # Fields
    version_number                      = models.PositiveIntegerField(_('version number'), default=1, editable=False)
    item_type_string                    = models.CharField(_('item type'), max_length=255, editable=False)
    active                              = models.BooleanField(_('active'), default=True, editable=False, db_index=True)
    destroyed                           = models.BooleanField(_('destroyed'), default=False, editable=False)
    creator                             = FixedForeignKey('Agent', related_name='items_created', editable=False, verbose_name=_('creator'))
    created_at                          = models.DateTimeField(_('created at'), editable=False)
    name                                = models.CharField(_('item name'), max_length=255, blank=True, help_text=_('The name used to refer to this item'))
    description                         = models.CharField(_('purpose'), max_length=255, blank=True, help_text=_('Description of the purpose of this item'))
    default_viewer                      = models.CharField(_('default viewer'), max_length=255, choices=PossibleViewerNamesIterable(), help_text=_('(Advanced) The default viewer to display this item'))
    email_list_address                  = models.CharField(_('email list address'), max_length=63, null=True, blank=True, unique=True, default=None, validators=[RegexValidator(email_local_address_re1, 'Field must be a valid local part of an email address (before the at-sign)'), RegexValidator(email_local_address_re2, 'Cannot be of the form "item-#" or "comment-#"')], help_text=_('(Advanced) The local part (before the at-sign) of the to email address of emails sent to subscribers of this item'))
    email_sets_reply_to_all_subscribers = FixedBooleanField(_('email sets reply to all subscribers'), default=True, help_text=_('(Advanced) For the reply-to field of emails sent to subscribers of this item: if set, reply to all subscribers, else reply to sender'))

    def __unicode__(self):
        return u'%s[%s] "%s"' % (self.item_type_string, self.pk, self.name)

    def display_name(self, can_view_name_field=True):
        """
        Return a friendly display name for the item.

        If the item has a blank name field, return a string of the form
        "ItemType id" (like Agent 1).  Otherwise, just return the value of the
        name field.

        If can_view_name_field is False, only return the "ItemType id" form.
        """
        if self.name and can_view_name_field:
            return self.name
        else:
            return u'%s %s' % (capfirst(self.actual_item_type()._meta.verbose_name), self.pk)

    def actual_item_type(self):
        """
        Return the actual item type for this item as a class (not a string).

        For example, Item.objects.get(pk=1).actual_item_type() == Agent
        """
        return get_item_type_with_name(self.item_type_string)

    def get_default_viewer(self):
        """
        Return the name of the default viewer. If the default_viewer field is
        invalid, returns the item type's default viewer.
        """
        from cms.base_viewer import get_viewer_class_by_name
        viewer_name = self.default_viewer
        viewer = get_viewer_class_by_name(viewer_name)
        if not (viewer and issubclass(self.actual_item_type(), viewer.accepted_item_type)):
            viewer_name = self.item_type_string.lower()
        return viewer_name

    @models.permalink
    def get_absolute_url(self):
        return ('item_url', (), {'viewer': self.get_default_viewer(), 'noun': self.pk})

    def downcast(self):
        """
        Return this item as an instance of the actual item type.

        For example, if the current item is an Agent, this will return an
        Agent, even though self is an Item.

        When the type of self is the actual item type, this returns self (not a
        copy); otherwise, this makes a single database query and returns an
        instance of the actual item type.
        """
        item_type = self.actual_item_type()
        if type(self) != item_type:
            return item_type.objects.get(pk=self.pk)
        else:
            return self

    def is_downcast(self):
        """
        Return true if this item is instantiated at the actual item type.

        For example, if item 123 is an agent, then:
        Agent.get(pk=123).is_downcast() == true
        Item.get(pk=123).is_downcast() == false
        """
        return self.actual_item_type() == type(self)

    def notification_email_username(self):
        if self.email_list_address:
            return self.email_list_address
        prefix = 'comment' if issubclass(self.actual_item_type(), Comment) else 'item'
        return u'%s-%d' % (prefix, self.pk)

    @staticmethod
    def item_for_notification_email_username(email_username):
        m = re.match(r'(item|comment)-(\d+)', email_username, re.IGNORECASE)
        if m:
            item_id = m.group(2)
            return Item.objects.get(pk=item_id)
        else:
            return Item.objects.get(email_list_address__iexact=email_username)

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
        version_number = int(version_number)
        if self.destroyed:
            self.version_number = int(version_number)
            return
        if version_number == self.version_number:
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
    def deactivate(self, action_agent, action_summary=None, action_time=None):
        """
        Deactivate the current Item (the specified agent was responsible with
        the given summary at the given time). This will call _after_deactivate
        if the item was previously active.
        """
        assert self.is_downcast()
        action_summary = action_summary or ''
        action_time = action_time or datetime.datetime.now()
        if not self.active:
            return
        # Execute after-callbacks
        self._before_deactivate(action_agent, action_summary, action_time)
        # Deactivate the item
        self.active = False
        self.save()
        # Execute after-callbacks
        self._after_deactivate(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        DeactivateActionNotice(action_item=self, action_item_version_number=self.version_number, action_agent=action_agent, action_time=action_time, action_summary=action_summary).save()
        old_item = self
        new_item = None
        RelationActionNotice.create_notices(action_agent, action_summary, action_time, action_item=self, existed_before=True, existed_after=False)
    deactivate.alters_data = True

    @transaction.commit_on_success
    def reactivate(self, action_agent, action_summary=None, action_time=None):
        """
        Reactivate the current Item (the specified agent was responsible with
        the given summary at the given time). This will call _after_reactivate
        if the item was previously inactive.
        """
        assert self.is_downcast()
        action_summary = action_summary or ''
        action_time = action_time or datetime.datetime.now()
        if self.active:
            return
        # Execute before-callbacks
        self._before_reactivate(action_agent, action_summary, action_time)
        # Reactivate the item
        self.active = True
        self.save()
        # Execute after-callbacks
        self._after_reactivate(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        ReactivateActionNotice(action_item=self, action_item_version_number=self.version_number, action_agent=action_agent, action_time=action_time, action_summary=action_summary).save()
        old_item = None
        new_item = self
        RelationActionNotice.create_notices(action_agent, action_summary, action_time, action_item=self, existed_before=False, existed_after=True)
    reactivate.alters_data = True

    @transaction.commit_on_success
    def destroy(self, action_agent, action_summary=None, action_time=None):
        """
        Nullify the fields of this item (the specified agent was responsible
        with the given summary at the given time) and delete all versions.
        The item must already be inactive and cannot have already been
        destroyed. This will call _after_destroy.
        """
        assert self.is_downcast()
        action_summary = action_summary or ''
        action_time = action_time or datetime.datetime.now()
        if self.destroyed or self.active:
            return
        # Execute before-callbacks
        self._before_destroy(action_agent, action_summary, action_time)
        # Set all non-special fields to null
        self.destroyed = True
        for field in self._meta.fields:
            if field.primary_key or isinstance(field, models.OneToOneField):
                continue
            elif field.name in UN_NULLABLE_FIELDS:
                continue
            elif field.null:
                setattr(self, field.name, None)
            else:
                raise Exception("Failed attempt to nullify un-nullable field: %s" % field.name)
        self.save()
        # Remove all versions
        type(self).Version.objects.filter(current_item=self).delete()
        # Remove all existing action notices
        self.action_notices.all().delete()
        # Remove all permissions on this item
        self.one_to_one_permissions_as_target.all().delete()
        self.some_to_one_permissions_as_target.all().delete()
        self.all_to_one_permissions_as_target.all().delete()
        if isinstance(self, Agent):
            self.one_to_one_permissions_as_source.all().delete()
            self.one_to_some_permissions_as_source.all().delete()
            self.one_to_all_permissions_as_source.all().delete()
        if isinstance(self, Collection):
            self.some_to_one_permissions_as_source.all().delete()
            self.some_to_some_permissions_as_source.all().delete()
            self.some_to_all_permissions_as_source.all().delete()
            self.one_to_some_permissions_as_target.all().delete()
            self.some_to_some_permissions_as_target.all().delete()
            self.all_to_some_permissions_as_target.all().delete()
        # Execute after-callbacks
        self._after_destroy(action_agent, action_summary, action_time)
        # Create relevant ActionNotices
        DestroyActionNotice(action_item=self, action_item_version_number=self.version_number, action_agent=action_agent, action_time=action_time, action_summary=action_summary).save()
    destroy.alters_data = True

    @transaction.commit_on_success
    def save_versioned(self, action_agent, action_summary=None, action_time=None, first_agent=False, initial_permissions=None, multi_agent_permission_cache=None):
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

        If the initial_permissions parameter is given, it should be a list of
        unsaved Permissions. After successfully saving self, this method
        will save these permissions (setting permission.target = self) before
        calling any callbacks.

        This will call _after_create or _after_edit, depending on whether the
        item already existed.
        """
        is_new = not self.pk
        if not is_new:
            assert self.is_downcast()
        action_summary = action_summary or ''
        action_time = action_time or datetime.datetime.now()

        # Initialize a multi_agent_permission_cache if we weren't given one
        if multi_agent_permission_cache is None:
            from cms.permissions import MultiAgentPermissionCache
            multi_agent_permission_cache = MultiAgentPermissionCache()

        # Set the special fields
        self.item_type_string = type(self).__name__
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

        # Set default_viewer if it wasn't already set (for non-form item creations)
        if not self.default_viewer:
            self.default_viewer = type(self).__name__.lower()

        # Set the email_list_address to null if blank
        if not self.email_list_address:
            self.email_list_address = None

        # Execute before-callbacks
        if is_new:
            self._before_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        else:
            self._before_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)

        # Save the old item version
        if not is_new:
            old_version = type(self).Version()
            old_self = type(self).objects.get(pk=self.pk)
            old_self.copy_fields_to_itemversion(old_version)
            old_version.save()

        # Update the item
        self.save()

        # Create the permissions
        if initial_permissions:
            for permission in initial_permissions:
                permission.target = self
                permission.save()

        # Execute after-callbacks
        if is_new:
            self._after_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        else:
            self._after_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)

        # Create relevant ActionNotices
        if is_new:
            CreateActionNotice(action_item=self, action_item_version_number=self.version_number, action_agent=action_agent, action_time=action_time, action_summary=action_summary).save()
            if self.active:
                RelationActionNotice.create_notices(action_agent, action_summary, action_time, action_item=self, existed_before=False, existed_after=True)
        else:
            EditActionNotice(action_item=self, action_item_version_number=self.version_number, action_agent=action_agent, action_time=action_time, action_summary=action_summary).save()
            if self.active:
                RelationActionNotice.create_notices(action_agent, action_summary, action_time, action_item=self, existed_before=True, existed_after=True)
    save_versioned.alters_data = True

    def can_be_deleted(self):
        """
        This method returns False for special items that should never be
        deleted, such as the AnonymousAgent; and it returns True for ordinary
        items.

        Item types that want to define special items should override this
        method.
        """
        return True

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        """
        Return a natural language representation of a RelationActionNotice with
        the given parameters, such that the from_item is self. The result will
        be in the form of a list of strings and items. The string representation
        can later be formed by concatenating the elements of the list, using the strings
        and relevant fields of the items. Remember to include spaces in the strings
        so that there is space around the item name. If field_name does not match
        any of the foreign keys for the item type, return None.
        """
        # We don't generate RelationActionNotices on creator, and there are no
        # other ForeignKeys defined in Item
        return None

    def unique_error_message(self, model_class, unique_check):
        """
        Set the error message function for uniqueness constraint violations, so
        that when it is displayed, it links to the item it clashes with (and
        provides a quick link to overwrite it).
        """
        from django.utils.html import escape
        from django.utils.text import get_text_list, capfirst
        from django.utils.safestring import mark_safe
        from django.utils.html import escape
        from urllib import urlencode
        unique_field_dict = {}
        for field_name in unique_check:
            unique_field_dict[field_name] = getattr(self, field_name)
        try:
            existing_item = type(self).objects.get(**unique_field_dict)
        except ObjectDoesNotExist:
            existing_item = None
        if existing_item:
            #TODO we can't know if we have permission to view the name now that we don't have the viewer
            item_name = existing_item.display_name(can_view_name_field=False)
            show_item_url = existing_item.get_absolute_url()
            overwrite_url = reverse('item_url', kwargs={'viewer': existing_item.get_default_viewer(), 'noun': existing_item.pk, 'action': 'edit'})
            overwrite_query_params = []
            for field in self._meta.fields:
                k = 'populate_' + field.name
                v = getattr(self, field.attname)
                overwrite_query_params.append(urlencode({k: v}))
            #TODO we can't do this anymore now now that we don't have the viewer
            #for k, list_ in viewer.request.GET.lists():
            #    overwrite_query_params.extend([urlencode({k: v}) for v in list_])
            overwrite_query_string = '&'.join(overwrite_query_params)
            existing_item_str = u' as <a href="%s">%s</a> (<a href="%s?%s">overwrite it</a>)' % (show_item_url, item_name, overwrite_url, escape(overwrite_query_string))
            model_name = capfirst(self._meta.verbose_name)
            field_labels = [self._meta.get_field(field_name).verbose_name for field_name in unique_check]
            field_labels = get_text_list(field_labels, _('and'))
            result = _(u"%(model_name)s with this %(field_label)s already exists%(existing_item_str)s.") %  {
                'model_name': unicode(model_name),
                'field_label': unicode(field_labels),
                'existing_item_str': existing_item_str,
            }
            return mark_safe(result)
        else:
            return super(Item, self).unique_error_message(model_class, unique_check)

    @classmethod
    def all_immutable_fields(cls):
        """
        Return a frozenset of the names of all the fields that are immutable
        for this item type (recursively traverses through item type hierarchy).
        """
        result = cls.introduced_immutable_fields
        for base in cls.__bases__:
            if getattr(base, '__metaclass__', None) == ItemMetaClass:
                result = result | base.all_immutable_fields()
        return result

    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        """
        Perform any specialized configuration for a Django form. The
        is_new parameter is True if the form is creating a new item, and is
        False if the form is updating an existing item. The attrs parameter is
        the list of class attrs that are about to be passed into the
        forms.models.ModelFormMetaclass constructor.

        This function should modify the attrs dictionary in order to configure
        the form.

        Item types that want to configure the default Django form in a special
        way should override this method, making sure to put a call superclasses
        at the top, like:
        >> super(Membership, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        """
        use_default_viewer_field = True
        if attrs['Meta'].fields is not None and 'default_viewer' not in attrs['Meta'].fields:
            use_default_viewer_field = False
        if attrs['Meta'].exclude is not None and 'default_viewer' in attrs['Meta'].exclude:
            use_default_viewer_field = False
        if use_default_viewer_field:
            default_viewer_field = item_type._meta.get_field_by_name('default_viewer')[0]
            from cms.base_viewer import get_viewer_class_by_name
            choices = [x for x in default_viewer_field.choices if issubclass(item_type, get_viewer_class_by_name(x[0]).accepted_item_type)]
            attrs['default_viewer'] = default_viewer_field.formfield(initial=item_type.__name__.lower(), choices=choices)

        if 'name' in attrs:
            attrs['name'] = forms.CharField(label=_(item_type.__name__ + " name"), help_text=_('The name used to refer to this ' + item_type.__name__.lower()), required=False)
        from cms.forms import CaptchaField
        attrs['captcha'] = CaptchaField(label=("Security Question"))

    @classmethod
    def auto_populate_fields(cls, item_type, field_dict, viewer):
        """
        Given a field_dict from field names to initial values, populate any
        other fields (in the dict) with values. For example, in a Subscription,
        given that the subscribed item is X, we might want to set the name of
        the subscription to "Subscription to X". This is used when presenting
        a user with a form.

        Item types that want to automatically populate field names based on
        other fields should override this method, making sure to put a call
        superclasses at the top, like:
        >> super(Subscription, cls).auto_populate_fields(item_type, field_dict, viewer)
        """
        pass

    def _before_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        """
        This method gets called before the first version of an item is
        created via save_versioned().

        Item types that want to trigger an action before creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._before_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        """
        pass
    _before_create.alters_data = True

    def _after_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        """
        This method gets called after the first version of an item is
        created via save_versioned().

        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        """
        pass
    _after_create.alters_data = True

    def _before_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        """
        This method gets called before an existing item is edited via
        save_versioned().

        Item types that want to trigger an action before creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._before_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
        """
        pass
    _before_edit.alters_data = True

    def _after_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        """
        This method gets called after an existing item is edited via
        save_versioned().

        Item types that want to trigger an action after creation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
        """
        pass
    _after_edit.alters_data = True

    def _before_deactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called before an item is deactivated.

        Item types that want to trigger an action before deactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._before_deactivate(action_agent, action_summary, action_time)
        """
        pass
    _before_deactivate.alters_data = True

    def _after_deactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called after an item is deactivated.

        Item types that want to trigger an action after deactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_deactivate(action_agent, action_summary, action_time)
        """
        pass
    _after_deactivate.alters_data = True

    def _before_reactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called before an item is reactivated.

        Item types that want to trigger an action before reactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._before_reactivate(action_agent, action_summary, action_time)
        """
        pass
    _before_reactivate.alters_data = True

    def _after_reactivate(self, action_agent, action_summary, action_time):
        """
        This method gets called after an item is reactivated.

        Item types that want to trigger an action after reactivation should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._after_reactivate(action_agent, action_summary, action_time)
        """
        pass
    _after_reactivate.alters_data = True

    def _before_destroy(self, action_agent, action_summary, action_time):
        """
        This method gets called before an item is destroyed.

        Item types that want to trigger an action before destroy should
        override this method, making sure to put a call to super at the top,
        like super(Group, self)._before_destroy(action_agent, action_summary, action_time)
        """
        pass
    _before_destroy.alters_data = True

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
# Webpage
###############################################################################

class Webpage(Item):
    """
    This item type represents a webpage. The only new field that isn't inherited
    from Item is the webpage's url
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Webpage.url', 'edit Webpage.url'])
    introduced_global_abilities = frozenset(['create Webpage'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('webpage')
        verbose_name_plural = _('webpages')

    # Fields
    url = models.CharField(_('URL'), max_length=255, default='http://', help_text = _("URL's to outside websites have to start with 'http://'"))

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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['add_contact_method', 'add_authentication_method', 'login_as', 'view Agent.last_online_at', 'view Agent.photo', 'edit Agent.photo'])
    introduced_global_abilities = frozenset(['create Agent'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('agent')
        verbose_name_plural = _('agents')

    # Fields
    last_online_at = models.DateTimeField(_('last online at'), null=True, blank=True, default=None, editable=False)
    photo = FixedForeignKey('ImageDocument', related_name='agents_with_photo', null=True, blank=True, default=None, verbose_name=_('photo'))

    def can_be_deleted(self):
        # Don't delete the admin agent
        if self.is_admin():
            return False
        return super(Agent, self).can_be_deleted()

    def is_anonymous(self):
        return issubclass(self.actual_item_type(), AnonymousAgent)

    def is_admin(self):
        return self.pk == 1



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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('anonymous agent')
        verbose_name_plural = _('anonymous agents')

    def can_be_deleted(self):
        # Don't delete the anonymous agent
        return False


class GroupAgent(Agent):
    """
    This item type is an Agent that acts on behalf of an entire group. It can't
    do anything that other agents can't do. Its significance is just symbolic:
    by being associated with a group, the actions taken by the group agent are
    seen as collective action of the group members. In general, permission to
    login_as the group agent will be limited to powerful members of the group.

    There should be exactly one GroupAgent for every group.
    """

    # Setup
    introduced_immutable_fields = frozenset(['group'])
    introduced_abilities = frozenset(['view GroupAgent.group'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('group agent')
        verbose_name_plural = _('group agents')

    # Fields
    group = FixedForeignKey('Group', related_name='group_agents', unique=True, editable=False, verbose_name=_('group'))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'group':
            if relation_added:
                status = _(" is now represented by ")
            else:
                status = _(" is no longer represented by ")
            return [action_item, status, self]
        else:
            return super(GroupAgent, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)


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
    introduced_immutable_fields = frozenset(['agent'])
    introduced_abilities = frozenset(['view AuthenticationMethod.agent'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('authentication method')
        verbose_name_plural = _('authentication methods')

    # Fields
    agent = FixedForeignKey(Agent, related_name='authentication_methods', verbose_name=_('agent'), required_abilities=['add_authentication_method'])

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'agent':
            if relation_added:
                status = _(" can now authenticate via ")
            else:
                status = _(" can no longer authenticate via ")
            return [action_item, status, self]
        else:
            return super(AuthenticationMethod, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)


class Person(Agent):
    """
    A Person is an Agent that represents a person in real life.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Person.first_name', 'view Person.middle_names', 'view Person.last_name', 'view Person.suffix',
                                      'edit Person.first_name', 'edit Person.middle_names', 'edit Person.last_name', 'edit Person.suffix'])
    introduced_global_abilities = frozenset(['create Person'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    # Fields
    first_name   = models.CharField(_('first name'), max_length=255, blank=True)
    middle_names = models.CharField(_('middle names'), max_length=255, blank=True)
    last_name    = models.CharField(_('last name'), max_length=255, blank=True)
    suffix       = models.CharField(_('suffix'), max_length=255, blank=True)

    def full_name(self):
      return " ".join([self.first_name, self.middle_names, self.last_name, self.suffix]).strip()


class ContactMethod(Item):
    """
    A ContactMethod belongs to an Agent and contains details on how to contact
    them. ContactMethod is meant to be abstract, so developers should always
    create subclasses rather than creating raw ContactMethods.
    """

    # Setup
    introduced_immutable_fields = frozenset(['agent'])
    introduced_abilities = frozenset(['add_subscription', 'view ContactMethod.agent'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('contact method')
        verbose_name_plural = _('contact methods')

    # Fields
    agent = FixedForeignKey(Agent, related_name='contact_methods', verbose_name=_('agent'), required_abilities=['add_contact_method'])

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'agent':
            if relation_added:
                status = _(" can now be contacted via ")
            else:
                status = _(" can no longer be contacted via ")
            return [action_item, status, self]
        else:
            return super(ContactMethod, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)


class EmailContactMethod(ContactMethod):
    """
    An EmailContactMethod is a ContactMethod that specifies an email address.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view EmailContactMethod.email', 'edit EmailContactMethod.email'])
    introduced_global_abilities = frozenset(['create EmailContactMethod'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PhoneContactMethod.phone', 'edit PhoneContactMethod.phone'])
    introduced_global_abilities = frozenset(['create PhoneContactMethod'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view FaxContactMethod.fax', 'edit FaxContactMethod.fax'])
    introduced_global_abilities = frozenset(['create FaxContactMethod'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view WebsiteContactMethod.url', 'edit WebsiteContactMethod.url'])
    introduced_global_abilities = frozenset(['create WebsiteContactMethod'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('website contact method')
        verbose_name_plural = _('website contact methods')

    # Fields
    url = models.CharField(_('website URL'), max_length=255, default='http://', help_text = _("URL's to outside websites have to start with 'http://'"))


class AIMContactMethod(ContactMethod):
    """
    An AIMContactMethod is a ContactMethod that specifies an AIM screen name.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view AIMContactMethod.screen_name', 'edit AIMContactMethod.screen_name'])
    introduced_global_abilities = frozenset(['create AIMContactMethod'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view AddressContactMethod.street1', 'view AddressContactMethod.street2', 'view AddressContactMethod.city',
                                      'view AddressContactMethod.state', 'view AddressContactMethod.country', 'view AddressContactMethod.zip',
                                      'edit AddressContactMethod.street1', 'edit AddressContactMethod.street2', 'edit AddressContactMethod.city',
                                      'edit AddressContactMethod.state', 'edit AddressContactMethod.country', 'edit AddressContactMethod.zip'])
    introduced_global_abilities = frozenset(['create AddressContactMethod'])
    dyadic_relations = {}
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
    indicating that all action notices on the item should be sent to the contact
    method as notifications.

    If deep=True and the item is a Collection, then action notices on all items
    in the collection (direct or indirect) will be sent in addition to comments
    on the collection itself.

    The subscribe_edit, subscribe_delete, subscribe_comments, and
    subscribe_relations fields determine what action notices will trigger this
    subscription.
    """

    # Setup
    introduced_immutable_fields = frozenset(['contact_method', 'item'])
    introduced_abilities = frozenset(['view Subscription.contact_method', 'view Subscription.item',
                                      'view Subscription.deep', 'edit Subscription.deep',
                                      'view Subscription.subscribe_edit', 'edit Subscription.subscribe_edit',
                                      'view Subscription.subscribe_delete', 'edit Subscription.subscribe_delete',
                                      'view Subscription.subscribe_comments', 'edit Subscription.subscribe_comments',
                                      'view Subscription.subscribe_relations', 'edit Subscription.subscribe_relations',
                                      'view Subscription.subscribe_members', 'edit Subscription.subscribe_members'])
    introduced_global_abilities = frozenset(['create Subscription'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        unique_together = ('contact_method', 'item')

    # Fields
    contact_method      = FixedForeignKey(ContactMethod, related_name='subscriptions', verbose_name=_('contact method'), required_abilities=['add_subscription'])
    item                = FixedForeignKey(Item, related_name='subscriptions_to', verbose_name=_('item'), required_abilities=['view Item.action_notices'])
    deep                = FixedBooleanField(_('deep subscription'), default=False, help_text=_("Enable this to extend your subscription to all members of this collection (applies only to collections)"))
    subscribe_edit      = FixedBooleanField(_('subscribe edit'), default=True, help_text=_("Enable this to receive notifications about edits"))
    subscribe_delete    = FixedBooleanField(_('subscribe delete'), default=True, help_text=_("Enable this to receive notifications about deletes"))
    subscribe_comments  = FixedBooleanField(_('subscribe comments'), default=True, help_text=_("Enable this to receive notifications about comments"))
    subscribe_relations = FixedBooleanField(_('subscribe relations'), default=False, help_text=_("Enable this to receive notifications about relations"))
    subscribe_members   = FixedBooleanField(_('subscribe members'), default=True, help_text=_("Enable this to receive notifications when members are added (applies only to collections)"))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'contact_method':
            if permission_cache.agent_can('view Subscription.item', self):
                if relation_added:
                    return [action_item, _(' is now subscribed to '), self.item, _(' via '), self]
                else:
                    return [action_item, _(' is no longer subscribed to '), self.item, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' is now subscribed via '), self]
                else:
                    return [action_item, _(' is no longer subscribed via '), self]
        elif field_name == 'item':
            if permission_cache.agent_can('view Subscription.contact_method', self):
                if relation_added:
                    return [action_item, _(' is now subscribed to by '), self.contact_method, _(' via '), self]
                else:
                    return [action_item, _(' is no longer subscribed to by '), self.contact_method, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' is now subscribed to via '), self]
                else:
                    return [action_item, _(' is no longer subscribed to via '), self]
        else:
            return super(Subscription, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

    @classmethod
    def auto_populate_fields(cls, item_type, field_dict, viewer):
        super(Subscription, cls).auto_populate_fields(item_type, field_dict, viewer)
        if 'item' in field_dict and 'name' not in field_dict:
            try:
                item = Item.objects.get(pk=field_dict['item'])
            except ObjectDoesNotExist:
                item = None
            if item:
                can_view_item_name = viewer.permission_cache.agent_can('view Item.name', item)
                can_view_agent_name = viewer.permission_cache.agent_can('view Item.name', viewer.cur_agent)
                item_name = item.display_name(can_view_item_name)
                agent_name = viewer.cur_agent.display_name(can_view_agent_name)
                field_dict['name'] = "%s's subscription to %s" % (agent_name, item_name)

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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['modify_membership', 'add_self', 'remove_self'])
    introduced_global_abilities = frozenset(['create Collection'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Group.image', 'edit Group.image'])
    introduced_global_abilities = frozenset(['create Group'])
    dyadic_relations = {}
    default_membership_type = 'agent'

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    # Fields
    image = FixedForeignKey('ImageDocument', related_name='groups_with_image', null=True, blank=True, default=None, verbose_name=_('image'))

    def _after_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Group, self)._after_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        # Create a folio for this group
        folio = Folio(group=self, name='%s folio' % self.display_name())
        permissions = [OneToOnePermission(source=action_agent, ability='do_anything', is_allowed=True)]
        folio.save_versioned(action_agent, action_summary, action_time, initial_permissions=permissions)
        # Create a group agent for this group
        group_agent = GroupAgent(group=self, name='%s agent' % self.display_name())
        permissions = [OneToOnePermission(source=action_agent, ability='do_anything', is_allowed=True)]
        group_agent.save_versioned(action_agent, action_summary, action_time, initial_permissions=permissions)
    _after_create.alters_data = True


class Folio(Collection):
    """
    A folio is a special collection that belongs to a group.
    """

    # Setup
    introduced_immutable_fields = frozenset(['group'])
    introduced_abilities = frozenset(['view Folio.group'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('folio')
        verbose_name_plural = _('folios')

    # Fields
    group = FixedForeignKey(Group, related_name='folios', unique=True, editable=False, verbose_name=_('group'))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'group':
            if relation_added:
                status = _(" now has the folio ")
            else:
                status = _(" no longer has the folio ")
            return [action_item, status, self]
        else:
            return super(Folio, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

class Membership(Item):
    """
    A Membership is a relationship between a collection and one of its items.
    """

    # Setup
    introduced_immutable_fields = frozenset(['item', 'collection'])
    introduced_abilities = frozenset(['view Membership.item', 'view Membership.collection', 'view Membership.permission_enabled', 'edit Membership.permission_enabled'])
    introduced_global_abilities = frozenset(['create Membership'])
    dyadic_relations = {'item': ('collection', _('member of'))}
    class Meta:
        verbose_name = _('membership')
        verbose_name_plural = _('memberships')
        unique_together = ('item', 'collection')

    # Fields
    item               = FixedForeignKey(Item, related_name='memberships', verbose_name=_('item'))
    collection         = FixedForeignKey(Collection, related_name='child_memberships', verbose_name=_('collection'), required_abilities=['modify_membership'])
    permission_enabled = FixedBooleanField(_('permission enabled'), help_text=_('Enable this if you want collection-wide permissions to apply to this child item'))

    def _before_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Membership, self)._before_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        if self.permission_enabled:
            permission_cache = multi_agent_permission_cache.get(action_agent)
            if not permission_cache.agent_can('do_anything', self.item):
                self.permission_enabled = False
    _before_create.alters_data = True

    def _before_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Membership, self)._before_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
        if self.permission_enabled:
            permission_cache = multi_agent_permission_cache.get(action_agent)
            if not permission_cache.agent_can('do_anything', self.item):
                self.permission_enabled = False
    _before_edit.alters_data = True

    def _after_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Membership, self)._after_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        if self.collection.active:
            # Update the RecursiveMembership to indicate this Membership exists
            RecursiveMembership.recursive_add_membership(self)
    _after_create.alters_data = True

    def _after_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Membership, self)._after_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
        if self.collection.active:
            # Update the RecursiveMembership in case permission_enabled changed
            #TODO figure out how to do this only when permission_enabled actually changes, rather than for every edit
            RecursiveMembership.recursive_remove_edge(self.collection, self.item)
            RecursiveMembership.recursive_add_membership(self)
    _after_edit.alters_data = True

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

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'item':
            if permission_cache.agent_can('view Membership.collection', self):
                if relation_added:
                    return [action_item, _(' now belongs to '), self.collection, _(' via '), self]
                else:
                    return [action_item, _(' no longer belongs to '), self.collection, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' now belongs to a collection via '), self]
                else:
                    return [action_item, _(' no longer belongs to a collection via '), self]
        elif field_name == 'collection':
            if permission_cache.agent_can('view Membership.item', self):
                if relation_added:
                    return [action_item, _(' now contains '), self.item, _(' via '), self]
                else:
                    return [action_item, _(' no longer contains '), self.item, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' now contains an item via '), self]
                else:
                    return [action_item, _(' no longer contains an item via '), self]
        else:
            return super(Membership, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        super(Membership, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        if is_new:
            attrs['Meta'].exclude.append('name')
            attrs['Meta'].exclude.append('description')


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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')


class TextDocument(Document):
    """
    A TextDocument is a Document that has a body that stores arbitrary text.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view TextDocument.body', 'edit TextDocument.body', 'add_transclusion'])
    introduced_global_abilities = frozenset(['create TextDocument'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view DjangoTemplateDocument.layout', 'view DjangoTemplateDocument.override_default_layout',
                                    'edit DjangoTemplateDocument.layout', 'edit DjangoTemplateDocument.override_default_layout'])
    introduced_global_abilities = frozenset(['create DjangoTemplateDocument'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('Django template document')
        verbose_name_plural = _('Django template documents')

    # Fields
    layout = FixedForeignKey('DjangoTemplateDocument', related_name='django_template_documents_with_layout', null=True, blank=True, default=None, verbose_name=_('layout'))
    override_default_layout = FixedBooleanField(_('override default layout'), default=False, help_text=_('Select this if this item will be used as a layout template'))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'layout':
            if relation_added:
                status = _(" is now the layout for ")
            else:
                status = _(" is no longer the layout for ")
            return [action_item, status, self]
        else:
            return super(DjangoTemplateDocument, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

class HtmlDocument(TextDocument):
    """
    An HtmlDocument is a TextDocument that renders its body as HTML.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HtmlDocument'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view FileDocument.datafile', 'edit FileDocument.datafile'])
    introduced_global_abilities = frozenset(['create FileDocument'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('file document')
        verbose_name_plural = _('file documents')

    # Fields
    datafile = models.FileField(_('data file'), upload_to='filedocument/%Y/%m/%d', max_length=255)

    def _before_destroy(self, action_agent, action_summary, action_time):
        super(FileDocument, self)._before_destroy(action_agent, action_summary, action_time)
        # Delete the datafile from the filesystem
        for version in FileDocument.Version.objects.filter(current_item=self.pk):
            version.datafile.delete()
        self.datafile.delete()
    _before_destroy.alters_data = True


class ImageDocument(FileDocument):
    """
    An ImageDocument is a FileDocument that stores an image.

    Right now, the only difference is that viewers know the file can be
    displayed as an image. In the future, this may add metadata like EXIF data
    and thumbnails.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create ImageDocument'])
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset(['from_item', 'from_item_version_number', 'to_item'])
    introduced_abilities = frozenset(['view Transclusion.from_item', 'view Transclusion.from_item_version_number',
                                      'view Transclusion.from_item_index', 'view Transclusion.to_item', 'edit Transclusion.from_item_index'])
    introduced_global_abilities = frozenset(['create Transclusion'])
    dyadic_relations = {'from_item': ('to_item', _('transcluded items')), 'to_item': ('from_item', _('transcluded in'))}
    class Meta:
        verbose_name = _('transclusion')
        verbose_name_plural = _('transclusions')

    # Fields
    from_item                = FixedForeignKey(TextDocument, related_name='transclusions_from', verbose_name=_('from item'), required_abilities=['add_transclusion'])
    from_item_version_number = models.PositiveIntegerField(_('from item version number'))
    from_item_index          = models.PositiveIntegerField(_('from item index'))
    to_item                  = FixedForeignKey(Item, related_name='transclusions_to', verbose_name=_('to item'))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'from_item':
            if permission_cache.agent_can('view Transclusion.to_item', self):
                if relation_added:
                    return [action_item, _(' now transcludes '), self.to_item, _(' via '), self]
                else:
                    return [action_item, _(' no longer transcludes '), self.to_item, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' now transcludes an item via '), self]
                else:
                    return [action_item, _(' no longer transcludes an item via '), self]
        elif field_name == 'to_item':
            if permission_cache.agent_can('view Transclusion.from_item', self):
                if relation_added:
                    return [action_item, _(' is now transcluded by '), self.from_item, _(' via '), self]
                else:
                    return [action_item, _(' is no longer transcluded by '), self.from_item, _(' via '), self]
            else:
                if relation_added:
                    return [action_item, _(' is now transcluded by something via '), self]
                else:
                    return [action_item, _(' is no longer transcluded by something via '), self]
        else:
            return super(Translusion, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

class Comment(Item):
    """
    A Comment is a unit of discussion about an Item.

    Each comment specifies the commented item and version number. Like
    Document, Comment is meant to be abstract, so developers should always
    create subclasses rather than creating raw Comments.

    Currently, users can only create TextComments.
    """

    # Setup
    introduced_immutable_fields = frozenset(['item', 'item_version_number', 'from_contact_method'])
    introduced_abilities = frozenset(['view Comment.item', 'view Comment.item_version_number', 'view Comment.from_contact_method'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    # Fields
    item                = FixedForeignKey(Item, related_name='comments', verbose_name=_('item'), required_abilities=['comment_on'])
    item_version_number = models.PositiveIntegerField(_('item version number'))
    from_contact_method = FixedForeignKey(ContactMethod, related_name='comments_from_contactmethod', null=True, blank=True, default=None, verbose_name=_('from contact method'), required_abilities=['do_anything'])

    def _after_create(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Comment, self)._after_create(action_agent, action_summary, action_time, multi_agent_permission_cache)
        # Update the RecursiveComment to indicate this Comment exists
        RecursiveComment.recursive_add_comment(self)
    _after_create.alters_data = True

    def _after_destroy(self, action_agent, action_summary, action_time):
        super(Comment, self)._after_destroy(action_agent, action_summary, action_time)
        # Update the RecursiveComment to indicate this Comment is gone
        RecursiveComment.recursive_remove_comment(self)
    _after_destroy.alters_data = True

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'item':
            if relation_added:
                status = _(" was commented on in ")
            else:
                status = _(" is no longer commented on in ")
            return [action_item, status, self]
        elif field_name == 'from_contact_method':
            if relation_added:
                status = _(" submitted the comment ")
            else:
                status = _(" is no longer the contact method for ")
            return [action_item, status, self]
        else:
            return super(Comment, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

    def original_comment_in_thread(self):
        """
        Return the original comment at the top of this thread. If this already
        the topmost comment (i.e. it is a comment on a non-comment item), just
        return self.

        For example, imagine self is comment A, and A is a reply to comment B,
        and B is a reply to non-comment item C. This method would return B.
        This method uses the RecursiveComment table.
        """
        parent_pks_query = RecursiveComment.objects.filter(child=self).values('parent').query
        comment_pks_query = Comment.objects.all().values('pk').query
        try:
            return Comment.objects.exclude(item__pk__in=comment_pks_query).get(pk__in=parent_pks_query)
        except ObjectDoesNotExist:
            return self


class TextComment(TextDocument, Comment):
    """
    A TextComment is a Comment and a TextDocument combined. It is currently the
    only form of user-generated comments.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create TextComment'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('text comment')
        verbose_name_plural = _('text comments')

    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        super(TextComment, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        if is_new:
            attrs['item_version_number'] = forms.IntegerField(widget=forms.HiddenInput())
            attrs['item_index'] = forms.IntegerField(widget=forms.HiddenInput(), required=False)
            attrs['name'] = forms.CharField(label=_("Comment title"), help_text=_("A brief description of the comment"), widget=forms.TextInput, required=False)
            attrs['Meta'].fields = ['name', 'body', 'item', 'item_version_number', 'from_contact_method']
            attrs['Meta'].exclude.append('action_summary')


class Excerpt(Item):
    """
    An Excerpt is an Item that refers to a portion of another Item (or an
    external resource, such as a webpage).

    Excerpt is meant to be abstract, so developers should always create
    subclasses rather than creating raw Excerpts.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
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
    introduced_immutable_fields = frozenset(['text_document'])
    introduced_abilities = frozenset(['view TextDocumentExcerpt.text_document', 'view TextDocumentExcerpt.text_document_version_number',
                                      'view TextDocumentExcerpt.start_index', 'view TextDocumentExcerpt.length',
                                      'edit TextDocumentExcerpt.text_document_version_number', 'edit TextDocumentExcerpt.start_index',
                                      'edit TextDocumentExcerpt.length'])
    introduced_global_abilities = frozenset(['create TextDocumentExcerpt'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('text document excerpt')
        verbose_name_plural = _('text document excerpts')

    # Fields
    text_document                = FixedForeignKey(TextDocument, related_name='text_document_excerpts', verbose_name=_('text document'))
    text_document_version_number = models.PositiveIntegerField(_('text document version number'))
    start_index                  = models.PositiveIntegerField(_('start index'))
    length                       = models.PositiveIntegerField(_('length'))

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'text_document':
            if relation_added:
                status = _(" is now excerpted in ")
            else:
                status = _(" is no longer excerpted in ")
            return [action_item, status, self]
        else:
            return super(TextDocumentExcerpt, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        super(TextDocumentExcerpt, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        # For now, this is how we prevent manual creation of TextDocumentExcerpts
        attrs['Meta'].fields = ['name']


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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['add_sub_path', 'view ViewerRequest.aliased_item', 'view ViewerRequest.viewer',
                                      'view ViewerRequest.action', 'view ViewerRequest.query_string', 'view ViewerRequest.format',
                                      'edit ViewerRequest.aliased_item', 'edit ViewerRequest.viewer', 'edit ViewerRequest.action',
                                      'edit ViewerRequest.query_string', 'edit ViewerRequest.format'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('viewer request')
        verbose_name_plural = _('viewer requests')

    # Fields
    viewer       = models.CharField(_('viewer'), max_length=255, help_text=_("This describes the type of the Aliased item. For example, a DjangoTemplateDocument should have 'djangotemplatedocument' while a HtmlDocument should have 'htmldocument'"))
    action       = models.CharField(_('action'), max_length=255, help_text=_("This is the action that should be taken on the Aliased item. The 'show' action works for most any item type. For DjangoTemplateDocuments, the action should be 'render'"))
    # If aliased_item is null, it is a collection action
    aliased_item = FixedForeignKey(Item, related_name='viewer_requests', null=True, blank=True, default=None, verbose_name=_('aliased item'), help_text=_("This is the item that should be shown. The item is typically a HtmlDocument or DjangoTemplateDocument but can be any type of item so long as the viewer and action are set appropriately"))
    query_string = models.CharField(_('query string'), max_length=1024, blank=True, help_text=_("This is used to pass parameters to an item, for instance 'page=2' for a Group item with many pages of members"))
    format       = models.CharField(_('format'), max_length=255, default='html', help_text=_("Typically this should be 'html', but could also be 'rss', etc"))

    def calculate_full_path(self):
        """Return a tuple (site, custom_urls) where custom_urls is a list."""
        req = self.downcast()
        if isinstance(req, Site):
            return (req, [])
        elif isinstance(req, CustomUrl):
            parent_path = req.parent_url.calculate_full_path()
            return (parent_path[0], parent_path[1] + [req])

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'aliased_item':
            if relation_added:
                status = _(" is now aliased in ")
            else:
                status = _(" is no longer aliased in ")
            return [action_item, status, self]
        else:
            return super(ViewerRequest, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Site.hostname', 'edit Site.hostname', 'view Site.default_layout', 'edit Site.default_layout', 'advanced_layout', 'view Site.title', 'edit Site.title', 'view Site.logo', 'edit Site.logo', ])
    introduced_global_abilities = frozenset(['create Site'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('site')
        verbose_name_plural = _('sites')

    # Fields
    title = models.CharField(_('site title'), null=True, blank=True, max_length=255, help_text=_("Displayed in the title bar and on the top left by default."))
    logo = FixedForeignKey('ImageDocument', related_name='sites_with_logo', null=True, blank=True, default=None, verbose_name=_('site logo'), help_text=_("Replaces the site title on the top left of the page by default"))
    hostname = models.CharField(_('hostname'), max_length=255, unique=True, help_text=_("Used for multi-site installations, for example `one.domain.com`, `two.domain.com`"))
    default_layout = FixedForeignKey(DjangoTemplateDocument, related_name='sites_with_layout', null=True, blank=True, default=None, verbose_name=_('default layout'), help_text=_("A DjangoTemplateDocument used as the base layout throughout the entire site"))

    def can_be_deleted(self):
        # Don't delete the default site
        if str(self.pk) == DemeSetting.get('cms.default_site'):
            return False
        return super(Site, self).can_be_deleted()

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'default_layout':
            if relation_added:
                status = _(" is now the default layout for ")
            else:
                status = _(" is no longer the default layout for ")
            return [action_item, status, self]
        else:
            return super(Site, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)

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
    introduced_immutable_fields = frozenset(['parent_url', 'path'])
    introduced_abilities = frozenset(['view CustomUrl.parent_url', 'view CustomUrl.path'])
    introduced_global_abilities = frozenset(['create CustomUrl'])
    dyadic_relations = {}
    class Meta:
        verbose_name = _('custom URL')
        verbose_name_plural = _('custom URLs')
        unique_together = ('parent_url', 'path')

    # Fields
    parent_url = FixedForeignKey(ViewerRequest, related_name='child_urls', verbose_name=_('parent URL'), required_abilities=['add_sub_path'])
    path       = models.CharField(_('path'), max_length=255)

    def relation_action_notice_natural_language_representation(self, permission_cache, field_name, relation_added, action_item):
        if field_name == 'parent_url':
            if relation_added:
                status = " has a subdirectory "
            else:
                status = " no longer has the subdirectory "
            return [action_item, status, self]
        else:
            return super(CustomUrl, self).relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)


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
    introduced_immutable_fields = frozenset(['key'])
    introduced_abilities = frozenset(['view DemeSetting.key', 'view DemeSetting.value', 'edit DemeSetting.value'])
    introduced_global_abilities = frozenset()
    dyadic_relations = {}
    class Meta:
        verbose_name = _('Deme setting')
        verbose_name_plural = _('Deme settings')

    # Fields
    key   = models.CharField(_('key'), max_length=255, unique=True)
    value = models.CharField(_('value'), max_length=255, blank=True)

    def can_be_deleted(self):
        # Don't delete important settings
        if self.key in ['cms.default_site']:
            return False
        return super(DemeSetting, self).can_be_deleted()

    @staticmethod
    def get(key):
        """
        Return the value of the DemeSetting with the specified key, or None if
        it is inactive or no such DemeSetting exists.
        """
        try:
            setting = DemeSetting.objects.get(key=key)
            if not setting.active:
                return None
            return setting.value
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def set(key, value, action_agent):
        """
        Set the DemeSetting with the specified key to the specified value,
        such that the agent is the creator. This may result in creating a new
        DemeSetting, updating an existing DemeSetting, or reactivating an
        inactive DemeSetting.
        """
        try:
            setting = DemeSetting.objects.get(key=key)
        except ObjectDoesNotExist:
            setting = DemeSetting(name=key, key=key)
        if setting.value != value:
            setting.value = value
            setting.save_versioned(action_agent=action_agent)
        if not setting.active:
            setting.reactivate(action_agent=action_agent)


###############################################################################
# Action notices
###############################################################################

class ActionNotice(models.Model):
    """
    An ActionNotice is a model (not a subclass of Item) that records an action
    happening in Deme. ActionNotice is meant to be abstract, so only subclasses
    should ever be created.
    """
    action_item                = models.ForeignKey(Item, related_name='action_notices', verbose_name=_('action item'))
    action_item_version_number = models.PositiveIntegerField(_('action item version number'))
    action_agent               = models.ForeignKey(Agent, related_name='action_notices_created', verbose_name=_('action agent'))
    action_time                = models.DateTimeField(_('action time'))
    action_summary             = models.CharField(_('action summary'), max_length=255, blank=True)

    def notification_reply_item(self):
        """
        Return the item that comments created about this notice (via replying
        to a notification email for this notice) are replies to.
        """
        return self.action_item

    def notification_email(self, subscription, email_contact_method):
        """
        Return an EmailMessage with the notification that should be sent to the
        specified EmailContactMethod. If there is no Subscription, or the Agent
        with the subscription is not allowed to receive the notification,
        return None.
        """
        # Make sure we were given consistent parameters
        assert subscription.contact_method.pk == email_contact_method.pk, 'Subscription %s for %s does not match EmailContactMethod %s' % (subscription, subscription.contact_method, email_contact_method)

        # Make sure the subscription is subscribed to this type of action notice
        is_subscribed = False
        if isinstance(self, RelationActionNotice):
            is_membership_relation = self.from_field_name == 'collection' and self.from_field_model == 'Membership'
            is_subscribed = subscription.subscribe_relations or (is_membership_relation and subscription.subscribe_members)
        elif isinstance(self, DeactivateActionNotice):
            is_subscribed = subscription.subscribe_delete
        elif isinstance(self, ReactivateActionNotice):
            is_subscribed = subscription.subscribe_delete
        elif isinstance(self, DestroyActionNotice):
            is_subscribed = subscription.subscribe_delete
        elif isinstance(self, CreateActionNotice):
            if issubclass(self.action_item.actual_item_type(), TextComment):
                is_subscribed = subscription.subscribe_comments
            else:
                is_subscribed = subscription.subscribe_edit
        elif isinstance(self, EditActionNotice):
            is_subscribed = subscription.subscribe_edit
        if not is_subscribed:
            return None

        # Initialize viewer
        from cms.views import ItemViewer
        from cms.templatetags.item_tags import get_viewable_name
        viewer = ItemViewer()
        viewer.init_for_outgoing_email(email_contact_method.agent)
        permission_cache = viewer.permission_cache

        # Make sure the recipient can view action_notices on the item
        if not (permission_cache.agent_can('view Item.action_notices', self.action_item) or permission_cache.agent_can('view Item.action_notices', self.action_agent)):
            #TODO what happens if i'm subscribed to the item, but not allowed to view its action notices, but i AM allowed to view action
            #notices for the action_agent? or vice versa?
            # Malicious case: Jon does not want me to see his actions, but everything he acts upon allows me to see its actions. So I can subscribe to Jon and still get notifications
            return None
        if isinstance(self, RelationActionNotice):
            if not permission_cache.agent_can('view %s.%s' % (self.from_field_model, self.from_field_name), self.from_item):
                return None

        # Get the fields the recipient is allowed to view
        subscribed_item = subscription.item
        item = self.action_item
        reply_item = self.notification_reply_item()
        topmost_item = item.original_item_in_thread()
        def get_url(x):
            return 'http://%s%s' % (settings.DEFAULT_HOSTNAME, x.get_absolute_url())
        subscribed_item_name = get_viewable_name(viewer.context, subscribed_item)
        item_name = get_viewable_name(viewer.context, item)
        topmost_item_name = get_viewable_name(viewer.context, topmost_item)
        action_agent_name = get_viewable_name(viewer.context, self.action_agent)
        recipient_name = get_viewable_name(viewer.context, email_contact_method.agent)

        #TODO what happens if agent cannot view email_list_address of subscribed_item and/or reply_item?
        generic_from_email_name = 'Deme action notice'
        noreply_from_email_address = '%s@%s' % ('noreply', settings.NOTIFICATION_EMAIL_HOSTNAME)
        from_email_name = None
        from_email_address = None
        subscribed_item_email_address = '%s@%s' % (subscribed_item.notification_email_username(), settings.NOTIFICATION_EMAIL_HOSTNAME)
        reply_item_name = "Subscribers to %s" % item_name
        reply_item_email_address = '%s@%s' % (reply_item.notification_email_username(), settings.NOTIFICATION_EMAIL_HOSTNAME)
        recipient_email_address = email_contact_method.email
        subject_prefix = subscribed_item_email_address

        # Generate the subject and body
        viewer.context['action_item'] = self.action_item
        viewer.context['action_item_reference_version_number'] = self.action_item_version_number - 1
        viewer.context['action_item_version_number'] = self.action_item_version_number
        viewer.context['action_agent'] = self.action_agent
        viewer.context['action_time'] = self.action_time
        viewer.context['action_summary'] = self.action_summary
        viewer.context['topmost_item'] = topmost_item
        viewer.context['url_prefix'] = 'http://%s' % settings.DEFAULT_HOSTNAME
        if isinstance(self, RelationActionNotice):
            # We don't send RelationActionNotices for Comment.item to prevent duplicate emails
            if self.from_field_name == 'item' and self.from_field_model == 'Comment':
                return
            from_item_name = get_viewable_name(viewer.context, self.from_item)
            natural_language_representation = self.natural_language_representation(permission_cache)
            action_sentence_parts = []
            for part in natural_language_representation:
                if isinstance(part, Item):
                    action_sentence_parts.append(get_viewable_name(viewer.context, part))
                else:
                    action_sentence_parts.append(unicode(part))
            action_sentence = u''.join(action_sentence_parts)
            subject = '[%s] %s' % (subject_prefix, action_sentence)
            template_name = 'relation'
            viewer.context['relation_added'] = self.relation_added
            viewer.context['from_item'] = self.from_item
            viewer.context['from_item_version_number'] = self.from_item_version_number
            viewer.context['from_field_name'] = self.from_field_name
            viewer.context['from_field_model'] = self.from_field_model
            viewer.context['natural_language_representation'] = natural_language_representation
        elif isinstance(self, DeactivateActionNotice):
            subject = '[%s] %s deactivated %s' % (subject_prefix, action_agent_name, item_name)
            template_name = 'delete'
            viewer.context['delete_type'] = 'deactivate'
        elif isinstance(self, ReactivateActionNotice):
            subject = '[%s] %s reactivated %s' % (subject_prefix, action_agent_name, item_name)
            template_name = 'delete'
            viewer.context['delete_type'] = 'reactivate'
        elif isinstance(self, DestroyActionNotice):
            subject = '[%s] %s destroyed %s' % (subject_prefix, action_agent_name, item_name)
            template_name = 'delete'
            viewer.context['delete_type'] = 'destroy'
        elif isinstance(self, CreateActionNotice):
            if issubclass(item.actual_item_type(), TextComment):
                comment = item.downcast()
                topmost_comment = comment.original_comment_in_thread()
                topmost_comment_name = get_viewable_name(viewer.context, topmost_comment)
                comment_creator_email_address = None
                if comment.from_contact_method and issubclass(comment.from_contact_method.actual_item_type(), EmailContactMethod):
                    if permission_cache.agent_can('view Comment.from_contact_method', comment):
                        from_email_contact_method = comment.from_contact_method.downcast()
                        if permission_cache.agent_can('view EmailContactMethod.email', from_email_contact_method):
                            comment_creator_email_address = from_email_contact_method.email
                from_email_name = action_agent_name
                if comment_creator_email_address:
                    from_email_address = comment_creator_email_address
                else:
                    from_email_address = noreply_from_email_address
                subject = '[%s] %s' % (subject_prefix, topmost_comment_name)
                if comment.pk != topmost_comment.pk:
                    subject = 'Re: %s' % subject
                template_name = 'comment'
                viewer.context['comment'] = comment
            else:
                subject = '[%s] %s created %s' % (subject_prefix, action_agent_name, item_name)
                template_name = 'save'
                viewer.context['save_type'] = 'create'
        elif isinstance(self, EditActionNotice):
            subject = '[%s] %s edited %s' % (subject_prefix, action_agent_name, item_name)
            template_name = 'save'
            viewer.context['save_type'] = 'edit'
        else:
            return None

        # Construct the EmailMessage
        template = loader.get_template("notification/%s_email.html" % template_name)
        body_html = template.render(viewer.context)
        body_text = html2text.html2text_file(body_html, None)
        body_text = wrap(body_text, 78)
        subscribed_item_email = formataddr((subscribed_item_name, subscribed_item_email_address))
        reply_item_email = formataddr((reply_item_name, reply_item_email_address))
        recipient_email = formataddr((recipient_name, recipient_email_address))
        if from_email_address is None:
            from_email = formataddr((generic_from_email_name, reply_item_email_address))
        else:
            from_email = formataddr((from_email_name, from_email_address))
        headers = {}
        headers['To'] = reply_item_email
        if subscribed_item.email_sets_reply_to_all_subscribers:
            headers['Reply-To'] = headers['To']
        def messageid(x):
            prefix = 'notice' if isinstance(x, ActionNotice) else 'item'
            date = (x.action_time if isinstance(x, ActionNotice) else x.created_at).strftime("%Y%m%d%H%M%S")
            return '<%s-%s-%s@%s>' % (prefix, x.pk, date, settings.NOTIFICATION_EMAIL_HOSTNAME)
        if reply_item == item:
            headers['Message-ID'] = messageid(self)
        else:
            headers['Message-ID'] = messageid(reply_item)
        headers['In-Reply-To'] = messageid(item)
        headers['References'] = '%s %s' % (messageid(topmost_item), messageid(item))
        email_message = EmailMultiAlternatives(subject, body_text, from_email, bcc=[recipient_email], headers=headers)
        email_message.attach_alternative(body_html, 'text/html')
        return email_message

def _action_notice_post_save_handler(sender, **kwargs):
    """
    This handler should get triggered when an ActionNotice is created. It takes
    care of asynchronously sending out notifications.

    Signals do not propagate to subclasses, this signal must be specified for
    every concrete subclass of ActionNotice.
    """
    action_notice = kwargs['instance']
    # Find all subscriptions to this item (both direct and deep)
    direct_q = Q(item__in=action_notice.action_item.all_parents_in_thread().values('pk').query) | Q(item__in=action_notice.action_agent.all_parents_in_thread().values('pk').query)
    deep_q = (Q(item__in=action_notice.action_item.all_parents_in_thread(True).values('pk').query) | Q(item__in=action_notice.action_agent.all_parents_in_thread(True).values('pk').query)) & Q(deep=True)
    subscriptions = Subscription.objects.filter(direct_q | deep_q, active=True)
    email_contact_methods = EmailContactMethod.objects.filter(pk__in=subscriptions.values('contact_method').query, active=True)
    pk_to_email_contact_method = dict([(x.pk, x) for x in email_contact_methods])
    # Generate an email for each subscription
    messages = [action_notice.notification_email(x, pk_to_email_contact_method[x.contact_method_id]) for x in subscriptions if x.contact_method_id in pk_to_email_contact_method]
    messages = [x for x in messages if x is not None]
    # Send the emails
    if messages:
        try:
            smtp_connection = SMTPConnection()
            smtp_connection.send_messages(messages)
        except:
            pass


class RelationActionNotice(ActionNotice):
    """
    A RelationActionNotice is created on an item whenever another item (the
    "from item") is created or modified so that one of its foreign-key fields
    now points to the item (when it didn't before) or no longer points to the
    item (when it did before).

    If relation_added is true, it means that the from item did not point before
    but now does; and if relation_added is false, it means that from item did
    point before but no longer does.
    """
    from_item                = models.ForeignKey(Item, related_name='relation_action_notices_from', verbose_name=_('from item'))
    from_item_version_number = models.PositiveIntegerField(_('from item version number'))
    from_field_name          = models.CharField(_('from field name'), max_length=255)
    from_field_model         = models.CharField(_('from field model'), max_length=255)
    relation_added           = models.BooleanField(_('relation added'))

    def natural_language_representation(self, permission_cache):
        from_item = self.from_item.downcast() #TODO this may cause performance issues
        field_name = self.from_field_name
        relation_added = self.relation_added
        action_item = self.action_item
        result = from_item.relation_action_notice_natural_language_representation(permission_cache, field_name, relation_added, action_item)
        if result is None:
            # Nobody wrote the code to define this natural language representation
            item_type = get_item_type_with_name(self.from_field_model)
            field = item_type._meta.get_field_by_name(field_name)[0]
            if relation_added:
                return [action_item, _(' is now the `'), field.verbose_name, _('` for '), from_item]
            else:
                return [action_item, _(' is no longer the `'), field.verbose_name, _('` for '), from_item]
        else:
            return result

    def notification_reply_item(self):
        """
        In RelationActionNotices, when someone replies to a notification, it
        should be turned into a comment on from_item, not item.

        For example, if we have a RelationActionNotice with from_item=membership
        and item=agent, the reply comment should go to membership, not agent.
        """
        return self.from_item

    @staticmethod
    def create_notices(action_agent, action_summary, action_time, action_item, existed_before, existed_after):
        """
        This method should be called whenever an item is created, edited,
        deactivated, or reactivated. It generates all relevant
        RelationActionNotices relevant to the action.

        The flags existed_before and existed_after are used to indicate what
        the action did to the item.  If the item was reactivated or created,
        existed_before would be false, otherwise it would be true. If the item
        was deactivated, existed_after would be false, otherwise it would be
        true.
        """
        if existed_before and existed_after:
            old_item = type(action_item).objects.get(pk=action_item.pk)
            old_item.copy_fields_from_version(action_item.version_number - 1)
            new_item = action_item
        elif existed_before:
            old_item = action_item
            new_item = None
        elif existed_after:
            old_item = None
            new_item = action_item
        # Because of multiple inheritance, we need to put the field/model pairs
        # into a set to eliminate duplicates
        fields_and_models = set(action_item._meta.get_fields_with_model())
        for field, model in fields_and_models:
            if isinstance(field, (models.OneToOneField, models.ManyToManyField)):
                continue
            if field.name == 'creator':
                continue # we do creator stuff separately
            if isinstance(field, models.ForeignKey):
                if model is None:
                    model = type(action_item)
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
                            action_notice.action_item = value
                            action_notice.action_item_version_number = value.version_number
                            action_notice.action_agent = action_agent
                            action_notice.action_time = action_time
                            action_notice.action_summary = action_summary
                            action_notice.from_item = action_item
                            action_notice.from_item_version_number = action_item.version_number
                            action_notice.from_field_name = field.name
                            action_notice.from_field_model = model.__name__
                            action_notice.relation_added = relation_added
                            action_notice.save()

signals.post_save.connect(_action_notice_post_save_handler, sender=RelationActionNotice, dispatch_uid='RelationActionNotice post_save')


class DeactivateActionNotice(ActionNotice):
    """
    A DeactivateActionNotice is generated whenever someone deactivates an item.
    """
    pass
signals.post_save.connect(_action_notice_post_save_handler, sender=DeactivateActionNotice, dispatch_uid='DeactivateActionNotice post_save')


class ReactivateActionNotice(ActionNotice):
    """
    A ReactivateActionNotice is generated whenever someone reactivates an item.
    """
    pass
signals.post_save.connect(_action_notice_post_save_handler, sender=ReactivateActionNotice, dispatch_uid='ReactivateActionNotice post_save')


class DestroyActionNotice(ActionNotice):
    """
    A DestroyActionNotice is generated whenever someone destroys an item.
    """
    pass
signals.post_save.connect(_action_notice_post_save_handler, sender=DestroyActionNotice, dispatch_uid='DestroyActionNotice post_save')


class CreateActionNotice(ActionNotice):
    """
    A CreateActionNotice is generated whenever someone creates an item.
    """
    pass
signals.post_save.connect(_action_notice_post_save_handler, sender=CreateActionNotice, dispatch_uid='CreateActionNotice post_save')

class EditActionNotice(ActionNotice):
    """
    An EditActionNotice is generated whenever someone edits an item.
    """
    pass
signals.post_save.connect(_action_notice_post_save_handler, sender=EditActionNotice, dispatch_uid='EditActionNotice post_save')


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
            for ability in item_type.introduced_abilities:
                if ability.startswith('view ') or ability.startswith('edit '):
                    action_str, parameter_str = ability.split(' ', 1)
                    item_type_str, field_str = parameter_str.split('.', 1)
                    assert item_type.__name__ == item_type_str
                    field = item_type._meta.get_field_by_name(field_str)[0]
                    if isinstance(field, models.related.RelatedObject):
                        field_name = field.field.rel.related_name.replace('_', ' ')
                    else:
                        field_name = field.verbose_name
                    friendly_name = u'%s %s (%s)' % (action_str, field_name, item_type._meta.verbose_name)
                else:
                    friendly_name = ability.replace('_', ' ')
                choice = (ability, friendly_name)
                choices.add(choice)
        choices = list(choices)
        choices.sort(key=lambda x: x[1].lower())
        for x in choices:
            yield x

class PossibleGlobalAbilitiesIterable(object):
    """
    Instantiated objects from this class are dynamic iterables, in that each
    time you iterate through them, you get the latest set of global abilities
    (according to the current state of introduced_global_abilities in the item
    types).

    Each ability is of the form (ability_name, friendly_name).
    """
    def __iter__(self):
        choices = set()
        for item_type in all_item_types():
            for ability in item_type.introduced_global_abilities:
                if ability.startswith('create '):
                    action_str, item_type_str = ability.split(' ', 1)
                    assert item_type.__name__ == item_type_str
                    friendly_name = u'%s %s' % (action_str, item_type._meta.verbose_name_plural)
                else:
                    friendly_name = ability.replace('_', ' ')
                choice = (ability, friendly_name)
                choices.add(choice)
        choices = list(choices)
        choices.sort(key=lambda x: x[1].lower())
        for x in choices:
            yield x

class PossibleItemAndGlobalAbilitiesIterable(object):
    """
    Instantiated objects from this class are dynamic iterables, in that each
    time you iterate through them, you get the latest set of item abilities and
    global abilities (according to the current state of introduced_abilities
    and introduced_global_abilities in the item types).

    Each ability is of the form (ability_name, friendly_name).
    """
    def __iter__(self):
        choices = set(PossibleItemAbilitiesIterable()) | set(PossibleGlobalAbilitiesIterable())
        choices = list(choices)
        choices.sort(key=lambda x: x[1].lower())
        for x in choices:
            yield x

# Iterable of all (ability, friendly_name) item abilities
POSSIBLE_ITEM_ABILITIES = PossibleItemAbilitiesIterable()

# Iterable of all (ability, friendly_name) global abilities
POSSIBLE_GLOBAL_ABILITIES = PossibleGlobalAbilitiesIterable()

# Iterable of all (ability, friendly_name) item and global abilities
POSSIBLE_ITEM_AND_GLOBAL_ABILITIES = PossibleItemAndGlobalAbilitiesIterable()

def friendly_name_for_ability(ability):
    "Return a friendly name string for the given ability, or None if not found."
    for other_ability, friendly_name in POSSIBLE_ITEM_AND_GLOBAL_ABILITIES:
        if other_ability == ability:
            return friendly_name
    return None

class Permission(models.Model):
    """Abstract superclass of all permissions."""
    ability = models.CharField(max_length=255, choices=POSSIBLE_ITEM_AND_GLOBAL_ABILITIES, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        abstract = True


class OneToOnePermission(Permission):
    """Permissions from individual agents to individual items."""
    source = models.ForeignKey(Agent, related_name='one_to_one_permissions_as_source')
    target = models.ForeignKey(Item, related_name='one_to_one_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'source', 'target')


class OneToSomePermission(Permission):
    """Permissions from individual agents to collections of items."""
    source = models.ForeignKey(Agent, related_name='one_to_some_permissions_as_source')
    target = models.ForeignKey(Collection, related_name='one_to_some_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'source', 'target')


class OneToAllPermission(Permission):
    """Permissions from individual agents to all items."""
    source = models.ForeignKey(Agent, related_name='one_to_all_permissions_as_source')
    class Meta:
        unique_together = ('ability', 'source')


class SomeToOnePermission(Permission):
    """Permissions from collections of agents to individual items."""
    source = models.ForeignKey(Collection, related_name='some_to_one_permissions_as_source')
    target = models.ForeignKey(Item, related_name='some_to_one_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'source', 'target')


class SomeToSomePermission(Permission):
    """Permissions from collections of agents to collections of items."""
    source = models.ForeignKey(Collection, related_name='some_to_some_permissions_as_source')
    target = models.ForeignKey(Collection, related_name='some_to_some_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'source', 'target')


class SomeToAllPermission(Permission):
    """Permissions from collections of agents to all items."""
    source = models.ForeignKey(Collection, related_name='some_to_all_permissions_as_source')
    class Meta:
        unique_together = ('ability', 'source')


class AllToOnePermission(Permission):
    """Permissions from all agents to individual items."""
    target = models.ForeignKey(Item, related_name='all_to_one_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'target')


class AllToSomePermission(Permission):
    """Permissions from all agents to collections of items."""
    target = models.ForeignKey(Collection, related_name='all_to_some_permissions_as_target')
    class Meta:
        unique_together = ('ability', 'target')


class AllToAllPermission(Permission):
    """Permissions from all agents to all items."""
    class Meta:
        unique_together = ('ability',)


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
        unique_together = ('parent', 'child')

    @staticmethod
    def recursive_add_comment(comment):
        """
        Update the table to reflect that the given comment was created.
        """
        parent = comment.item
        ancestors = Item.objects.filter(Q(pk__in=RecursiveComment.objects.filter(child=parent).values('parent').query)
                                        | Q(pk=parent.pk))
        for ancestor in ancestors:
            RecursiveComment(parent=ancestor, child=comment).save()

    @staticmethod
    def recursive_remove_comment(comment):
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

    The permission_enabled field is set to True if there exists at least one
    path of Memberships from parent to child, such that each membership in the
    path has permission_enabled=True.
    """
    parent             = models.ForeignKey(Collection, related_name='recursive_memberships_as_parent', verbose_name=_('parent'))
    child              = models.ForeignKey(Item, related_name='recursive_memberships_as_child', verbose_name=_('child'))
    permission_enabled = models.BooleanField(_('permission enabled'), default=False)
    child_memberships  = models.ManyToManyField(Membership, verbose_name=_('child memberships'))
    class Meta:
        unique_together = ('parent', 'child')

    @staticmethod
    def recursive_add_membership(membership):
        """
        Update the table to reflect that the given membership was created (or
        reactivated).
        """
        parent = membership.collection
        child = membership.item
        # Connect parent to child
        try:
            recursive_membership = RecursiveMembership.objects.get(parent=parent, child=child)
            if recursive_membership.permission_enabled != membership.permission_enabled:
                RecursiveMembership.recursive_remove_edge(parent, child)
                recursive_membership = None
        except ObjectDoesNotExist:
            recursive_membership = None
        if recursive_membership is None:
            recursive_membership = RecursiveMembership(parent=parent, child=child, permission_enabled=membership.permission_enabled)
            recursive_membership.save()
        recursive_membership.child_memberships.add(membership)
        # Connect ancestors to child, via parent
        ancestor_recursive_memberships = RecursiveMembership.objects.filter(child=parent)
        for ancestor_recursive_membership in ancestor_recursive_memberships:
            try:
                recursive_membership = RecursiveMembership.objects.get(parent=ancestor_recursive_membership.parent, child=child)
                if not recursive_membership.permission_enabled:
                    if membership.permission_enabled and ancestor_recursive_membership.permission_enabled:
                        recursive_membership.permission_enabled = True
                        recursive_membership.save()
            except ObjectDoesNotExist:
                recursive_membership = RecursiveMembership(parent=ancestor_recursive_membership.parent, child=child)
                recursive_membership.permission_enabled = ancestor_recursive_membership.permission_enabled and membership.permission_enabled
                recursive_membership.save()
            recursive_membership.child_memberships.add(membership)
        # Connect parent and ancestors to all descendants
        descendant_recursive_memberships = RecursiveMembership.objects.filter(parent=child)
        for descendant_recursive_membership in descendant_recursive_memberships:
            child_memberships = descendant_recursive_membership.child_memberships.all()
            # Indirect ancestors
            for ancestor_recursive_membership in ancestor_recursive_memberships:
                try:
                    recursive_membership = RecursiveMembership.objects.get(parent=ancestor_recursive_membership.parent,
                                                                           child=descendant_recursive_membership.child)
                    if not recursive_membership.permission_enabled:
                        if membership.permission_enabled and ancestor_recursive_membership.permission_enabled and descendant_recursive_membership.permission_enabled:
                            recursive_membership.permission_enabled = True
                            recursive_membership.save()
                except ObjectDoesNotExist:
                    recursive_membership = RecursiveMembership(parent=ancestor_recursive_membership.parent,
                                                               child=descendant_recursive_membership.child)
                    recursive_membership.permission_enabled = ancestor_recursive_membership.permission_enabled and membership.permission_enabled and descendant_recursive_membership.permission_enabled
                    recursive_membership.save()
                for child_membership in child_memberships:
                    recursive_membership.child_memberships.add(child_membership)
            # Parent
            try:
                recursive_membership = RecursiveMembership.objects.get(parent=parent, child=descendant_recursive_membership.child)
                if not recursive_membership.permission_enabled:
                    if membership.permission_enabled and descendant_recursive_membership.permission_enabled:
                        recursive_membership.permission_enabled = True
                        recursive_membership.save()
            except ObjectDoesNotExist:
                recursive_membership = RecursiveMembership(parent=parent, child=descendant_recursive_membership.child)
                recursive_membership.permission_enabled = membership.permission_enabled and descendant_recursive_membership.permission_enabled
                recursive_membership.save()

            for child_membership in child_memberships:
                recursive_membership.child_memberships.add(child_membership)

    @staticmethod
    def recursive_remove_edge(parent, child):
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

    @staticmethod
    def recursive_add_collection(collection):
        """
        Update the table to reflect that the given collection was created or
        reactivated.
        """
        memberships = Membership.objects.filter(Q(collection=collection) | Q(item=collection), active=True)
        for membership in memberships:
            RecursiveMembership.recursive_add_membership(membership)

    @staticmethod
    def recursive_remove_collection(collection):
        """
        Update the table to reflect that the given collection was deactivated.
        """
        RecursiveMembership.recursive_remove_edge(collection, collection)


###############################################################################
# Edit locking
###############################################################################

class EditLock(models.Model):
    """
    This table contains information on all items currently being edited.
    This allows us to lock items to prevent simultaneous editing.
    """
    item = models.ForeignKey(Item, related_name='edit_locks', verbose_name=_('item'), unique=True)
    editor = models.ForeignKey(Agent, related_name='edit_locks_as_editor', verbose_name=_('editor'))
    lock_acquire_time = models.DateTimeField(_('lock acquire time'))
    lock_refresh_time = models.DateTimeField(_('lock refresh time'))


###############################################################################
# all_item_types()
###############################################################################

def all_item_types():
    """Return a list of every item type (as a class)."""
    result = [x for x in models.loading.get_models() if issubclass(x, Item)]
    return result

def get_item_type_with_name(name, case_sensitive=True):
    """
    Return the item type class with the given name (case-sensitive or not,
    as specified), or return None if there is no item type with the name.
    """
    try:
        if case_sensitive:
            return (x for x in all_item_types() if x.__name__ == name).next()
        else:
            return (x for x in all_item_types() if x.__name__.lower() == name.lower()).next()
    except StopIteration:
        return None

