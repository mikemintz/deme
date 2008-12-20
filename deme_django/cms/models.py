from django.db import models
from django.db.models import Q
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
    version_number = models.IntegerField(default=1, editable=False, db_index=True)
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
        #TODO make more efficient
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.VERSION.objects.get(id=self.id)

    @transaction.commit_on_success
    def trash(self):
        #TODO we must update RecursiveItemSetMembership
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
    trash.alters_data = True

    @transaction.commit_on_success
    def untrash(self):
        #TODO we must update RecursiveItemSetMembership
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
    untrash.alters_data = True


class Item(models.Model):
    __metaclass__ = ItemMetaClass
    immutable_fields = []
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
        #TODO make more efficient
        item_type = [x for x in all_models() if x.__name__ == self.item_type][0]
        return item_type.objects.get(id=self.id)

    def all_containing_itemsets(self):
        return ItemSet.objects.filter(trashed=False, pk__in=RecursiveItemSetMembership.objects.filter(child=self).values('parent').query)

    def all_comments(self):
        return Comment.objects.filter(trashed=False, pk__in=RecursiveCommentMembership.objects.filter(parent=self).values('child').query)

    @transaction.commit_on_success
    def trash(self):
        if not self.trashed:
            if isinstance(self, ItemSetMembership):
                RecursiveItemSetMembership.recursive_remove(self.itemset, self.item)
            if isinstance(self, ItemSet):
                RecursiveItemSetMembership.recursive_remove_itemset(self)
        self.trashed = True
        self.save()
        self.versions.all().update(trashed=True)
    trash.alters_data = True

    @transaction.commit_on_success
    def untrash(self):
        if self.trashed:
            if isinstance(self, ItemSetMembership):
                RecursiveItemSetMembership.recursive_add(self.itemset, self.item)
            if isinstance(self, ItemSet):
                RecursiveItemSetMembership.recursive_add_itemset(self)
        self.trashed = False
        self.save()
        self.versions.all().update(trashed=False)
    untrash.alters_data = True

    @transaction.commit_on_success
    def save_versioned(self, updater=None, first_agent=False, create_permissions=True, created_at=None, updated_at=None, overwrite_latest_version=False):
        save_time = datetime.datetime.now()
        is_new = not self.pk

        # Update RecursiveItemSetMembership if we're saving an ItemSetMembership
        if isinstance(self, ItemSetMembership):
            if is_new:
                if not self.trashed:
                    RecursiveItemSetMembership.recursive_add(self.itemset, self.item)
            else:
                old = ItemSetMembership.objects.get(pk=self.pk)
                if not old.trashed:
                    if not self.trashed:
                        #old and new are both around: check for changed pointers
                        if (self.itemset, self.item) != (old.itemset, old.item):
                            RecursiveItemSetMembership.recursive_remove(old.itemset, old.item)
                            RecursiveItemSetMembership.recursive_add(self.itemset, self.item)
                    else:
                        #old is around, new is not around: remove old
                        RecursiveItemSetMembership.recursive_remove(old.itemset, old.item)
                else:
                    if not self.trashed:
                        #old is not around, new is around: add new
                        RecursiveItemSetMembership.recursive_add(self.itemset, self.item)
                    else:
                        #neither old nor new are around: nothing to do
                        pass

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
        self.save()

        # Create the new item version
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
        latest_version_number = 0 if is_new else ItemVersion.objects.filter(current_item__pk=self.pk).order_by('-version_number')[0].version_number
        if overwrite_latest_version and not is_new:
            new_version = self.__class__.VERSION.objects.get(current_item=self, version_number=latest_version_number)
        else:
            new_version = self.__class__.VERSION()
            new_version.current_item_id = self.pk
            new_version.version_number = latest_version_number + 1
        for key, val in fields.iteritems():
            setattr(new_version, key, val)
        new_version.save()

        # Create the permissions
        #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
        #TODO we need to reference the roles by id, not name, otherwise very insecure!
        if create_permissions and latest_version_number == 0 and not issubclass(self.__class__, Permission):
            DefaultRolePermission(name="Default permission for %s" % self.name, item=self, role=Role.objects.get(name="%s Default" % self.__class__.__name__)).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)
            AgentRolePermission(name="Creator permission for %s" % self.name, agent=updater, item=self, role=Role.objects.get(name="%s Creator" % self.__class__.__name__)).save_versioned(updater=updater, created_at=created_at, updated_at=updated_at)

        # Update RecursiveCommentMembership if we're saving a Comment
        if isinstance(self, Comment):
            if is_new:
                RecursiveCommentMembership.recursive_add(self.commented_item, self)
            else:
                # We assume that commented_item cannot change since it is marked immutable
                pass

        # Send notifications if we're creating a new Comment
        #TODO permissions to view name/body/etc
        #TODO maybe this should happen asynchronously somehow
        #TODO why doesn't an exception in this part of the code roll back the transaction?
        if is_new and isinstance(self, Comment):
            # email everyone subscribed to items this comment is relevant for
            if isinstance(self, TextComment):
                comment_type_q = Q(notify_text=True)
            elif isinstance(self, EditComment):
                comment_type_q = Q(notify_edit=True)
            else:
                #TODO what to do if it's none of the above?
                comment_type_q = Q(pk__isnull=False)
            direct_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items().values('pk').query, trashed=False).filter(comment_type_q)
            deep_subscriptions = Subscription.objects.filter(item__in=self.all_commented_items_and_itemsets().values('pk').query, deep=True, trashed=False).filter(comment_type_q)
            subscribed_email_contact_methods = EmailContactMethod.objects.filter(trashed=False).filter(Q(pk__in=direct_subscriptions.values('contact_method').query) | Q(pk__in=deep_subscriptions.values('contact_method').query))
            if subscribed_email_contact_methods:
                from django.core.mail import SMTPConnection, EmailMessage
                from email.utils import formataddr
                subject = '[%s] %s' % (self.commented_item.name, self.name)
                # TODO we need to generate a more dynamic URL here
                if isinstance(self, TextComment):
                    body = '%s wrote a comment in %s\n%s\n\n%s' % (self.creator.name, self.commented_item.name, 'http://deme.stanford.edu/resource/%s/%d' % (self.commented_item.item_type.lower(), self.commented_item.pk), self.body)
                else:
                    body = '%s did action %s to %s\n%s' % (self.creator.name, self.item_type, self.commented_item.name, 'http://deme.stanford.edu/resource/%s/%d' % (self.commented_item.item_type.lower(), self.commented_item.pk))
                sender_agent = self.updater.downcast()
                if isinstance(sender_agent, Person):
                    from_email_address = sender_agent.email or 'noreply@deme.stanford.edu'
                else:
                    from_email_address = 'noreply@deme.stanford.edu'
                from_email = formataddr((sender_agent.name, from_email_address))
                headers = {'Reply-To': '%s@deme.stanford.edu' % self.pk}
                messages = [EmailMessage(subject=subject, body=body, from_email=from_email, to=[formataddr((rcpt.agent.name, rcpt.email))], headers=headers) for rcpt in subscribed_email_contact_methods]
                smtp_connection = SMTPConnection()
                smtp_connection.send_messages(messages)

        # Create an EditComment if we're making an edit
        if not is_new and not overwrite_latest_version:
            edit_comment = EditComment(commented_item=self, name='Edit')
            edit_comment.save_versioned(updater=updater)
            edit_comment_location = CommentLocation(name="Untitled CommentLocation", comment=edit_comment, commented_item_version_number=new_version.version_number, commented_item_index=None)
            edit_comment_location.save_versioned(updater=updater)

        if is_new:
            self.after_create()
    save_versioned.alters_data = True

    def after_create(self):
        pass
    after_create.alters_data = True



class Agent(Item):
    last_online_at = models.DateTimeField(null=True, blank=True) # it's a little sketchy how this gets set without save_versioned(), so maybe reverting to an old version will reset this to NULL


class AnonymousAgent(Agent):
    pass


class AuthenticationMethod(Item):
    immutable_fields = Item.immutable_fields + ['agent']
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

class PasswordAuthenticationMethod(AuthenticationMethod):
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


class Person(Agent):
    first_name = models.CharField(max_length=255)
    middle_names = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255, blank=True)


class ItemSet(Item):
    def all_contained_itemset_members(self):
        return Item.objects.filter(trashed=False, pk__in=RecursiveItemSetMembership.objects.filter(parent=self).values('child').query)


class Group(ItemSet):
    def after_create(self):
        super(Group, self).after_create()
        folio = Folio(name="%s Folio" % self.name, group=self)
        folio.save_versioned(updater=self.updater)
    after_create.alters_data = True


class Folio(ItemSet):
    immutable_fields = ItemSet.immutable_fields + ['group']
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


class Comment(Document):
    immutable_fields = Document.immutable_fields + ['commented_item']
    commented_item = models.ForeignKey(Item, related_name='comments_as_item')
    def all_commented_items(self):
        return Item.objects.filter(trashed=False, pk__in=RecursiveCommentMembership.objects.filter(child=self).values('parent').query)
    def all_commented_items_and_itemsets(self):
        parent_item_pks_query = RecursiveCommentMembership.objects.filter(child=self).values('parent').query
        parent_items = Q(pk__in=parent_item_pks_query)
        parent_item_itemsets = Q(pk__in=RecursiveItemSetMembership.objects.filter(child__in=parent_item_pks_query).values('parent').query)
        return Item.objects.filter(parent_items | parent_item_itemsets, trashed=False)



class CommentLocation(Item):
    immutable_fields = TextDocument.immutable_fields + ['comment', 'commented_item_version_number']
    comment = models.ForeignKey(Comment, related_name='comment_locations_as_comment')
    commented_item_version_number = models.IntegerField()
    commented_item_index = models.IntegerField(null=True, blank=True)
    class Meta:
        unique_together = (('comment', 'commented_item_version_number'),)


class TextComment(TextDocument, Comment):
    pass


class EditComment(Comment):
    pass


class Relationship(Item):
    pass


class ItemSetMembership(Relationship):
    immutable_fields = Relationship.immutable_fields + ['item', 'itemset']
    item = models.ForeignKey(Item, related_name='itemset_memberships_as_item')
    itemset = models.ForeignKey(ItemSet, related_name='itemset_memberships_as_itemset')
    class Meta:
        unique_together = (('item', 'itemset'),)


class RecursiveItemSetMembership(models.Model):
    parent = models.ForeignKey(ItemSet, related_name='recursive_itemset_memberships_as_parent')
    child = models.ForeignKey(Item, related_name='recursive_itemset_memberships_as_child')
    class Meta:
        unique_together = (('parent', 'child'),)
    @classmethod
    def recursive_add(cls, parent, child):
        ancestors = ItemSet.objects.filter(Q(recursive_itemset_memberships_as_parent__child=parent) | Q(pk=parent.pk))
        descendants = Item.objects.filter(Q(recursive_itemset_memberships_as_child__parent=child) | Q(pk=child.pk))
        #TODO make this work with transactions
        if ancestors and descendants:
            cursor = connection.cursor()
            ancestor_select = ' UNION '.join(["SELECT %s" % x.pk for x in ancestors])
            descendant_select = ' UNION '.join(["SELECT %s" % x.pk for x in descendants])
            sql = "INSERT INTO cms_recursiveitemsetmembership (parent_id, child_id) SELECT ancestors.id, descendants.id FROM (%s) AS ancestors(id), (%s) AS descendants(id) WHERE NOT EXISTS (SELECT parent_id,child_id FROM cms_recursiveitemsetmembership WHERE parent_id = ancestors.id AND child_id = descendants.id)" % (ancestor_select, descendant_select)
            cursor.execute(sql)
            transaction.commit_unless_managed()
    @classmethod
    def recursive_remove(cls, parent, child):
        ancestors = ItemSet.objects.filter(Q(recursive_itemset_memberships_as_parent__child=parent) | Q(pk=parent.pk))
        descendants = Item.objects.filter(Q(recursive_itemset_memberships_as_child__parent=child) | Q(pk=child.pk))
        #TODO make this work with transactions
        if ancestors and descendants:
            # first remove all connections between ancestors and descendants
            cursor = connection.cursor()
            ancestor_select = ','.join([str(x.pk) for x in ancestors])
            descendant_select = ','.join([str(x.pk) for x in descendants])
            cursor.execute("DELETE FROM cms_recursiveitemsetmembership WHERE parent_id IN (%s) AND child_id IN (%s)" % (ancestor_select, descendant_select))
            transaction.commit_unless_managed()
            # now add back any real connections between ancestors and descendants that aren't trashed
            memberships = ItemSetMembership.objects.filter(trashed=False, itemset__in=ancestors.values('pk').query, item__in=descendants.values('pk').query).exclude(itemset=parent, item=child)
            for membership in memberships:
                RecursiveItemSetMembership.recursive_add(membership.itemset, membership.item)
    @classmethod
    def recursive_add_itemset(cls, itemset):
        memberships = ItemSetMembership.objects.filter(Q(itemset=itemset) | Q(item=itemset), trashed=False)
        for membership in memberships:
            RecursiveItemSetMembership.recursive_add(membership.itemset, membership.item)
    @classmethod
    def recursive_remove_itemset(cls, itemset):
        RecursiveItemSetMembership.recursive_remove(itemset, itemset)


class RecursiveCommentMembership(models.Model):
    parent = models.ForeignKey(Item, related_name='recursive_comment_memberships_as_parent')
    child = models.ForeignKey(Comment, related_name='recursive_comment_memberships_as_child')
    class Meta:
        unique_together = (('parent', 'child'),)
    @classmethod
    def recursive_add(cls, parent, child):
        ancestors = Item.objects.filter(Q(recursive_comment_memberships_as_parent__child=parent) | Q(pk=parent.pk))
        descendants = Comment.objects.filter(Q(recursive_comment_memberships_as_child__parent=child) | Q(pk=child.pk))
        #TODO make this work with transactions
        if ancestors and descendants:
            cursor = connection.cursor()
            ancestor_select = ' UNION '.join(["SELECT %s" % x.pk for x in ancestors])
            descendant_select = ' UNION '.join(["SELECT %s" % x.pk for x in descendants])
            sql = "INSERT INTO cms_recursivecommentmembership (parent_id, child_id) SELECT ancestors.id, descendants.id FROM (%s) AS ancestors(id), (%s) AS descendants(id) WHERE NOT EXISTS (SELECT parent_id,child_id FROM cms_recursivecommentmembership WHERE parent_id = ancestors.id AND child_id = descendants.id)" % (ancestor_select, descendant_select)
            cursor.execute(sql)
            transaction.commit_unless_managed()
    @classmethod
    def recursive_remove(cls, parent, child):
        ancestors = Item.objects.filter(Q(recursive_comment_memberships_as_parent__child=parent) | Q(pk=parent.pk))
        descendants = Comment.objects.filter(Q(recursive_comment_memberships_as_child__parent=child) | Q(pk=child.pk))
        #TODO make this work with transactions
        if ancestors and descendants:
            # first remove all connections between ancestors and descendants
            cursor = connection.cursor()
            ancestor_select = ','.join([str(x.pk) for x in ancestors])
            descendant_select = ','.join([str(x.pk) for x in descendants])
            cursor.execute("DELETE FROM cms_recursivecommentmembership WHERE parent_id IN (%s) AND child_id IN (%s)" % (ancestor_select, descendant_select))
            transaction.commit_unless_managed()
            # nothing to add back, since comments form a tree structure


class ContactMethod(Item):
    agent = models.ForeignKey(Agent, related_name='contactmethods_as_agent')


class EmailContactMethod(ContactMethod):
    email = models.EmailField(max_length=320)


class PhoneContactMethod(ContactMethod):
    phone = models.CharField(max_length=20)


class FaxContactMethod(ContactMethod):
    fax = models.CharField(max_length=20)


class WebsiteContactMethod(ContactMethod):
    url = models.CharField(max_length=255)


class IMContactMethod(ContactMethod):
    im = models.CharField(max_length=255)


class AddressContactMethod(ContactMethod):
    street1 = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=20, blank=True)


class Subscription(Item):
    immutable_fields = Item.immutable_fields + ['subscriber', 'item']
    contact_method = models.ForeignKey(ContactMethod, related_name='subscriptions_as_contact_method')
    item = models.ForeignKey(Item, related_name='subscriptions_as_item')
    deep = models.BooleanField(default=False)
    notify_text = models.BooleanField(default=True)
    notify_edit = models.BooleanField(default=False)
    class Meta:
        unique_together = (('contact_method', 'item'),)


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
    ('do_something', 'Do Something'),
    ('do_everything', 'Do Everything'),
]

#TODO somehow limit ability_parameter
#TODO make role name unique maybe, or at least have a way of finding the ONE "AuthenticationMethod Creator" role

class GlobalRole(Item):
    pass


class Role(Item):
    pass


class GlobalRoleAbility(Item):
    immutable_fields = Item.immutable_fields + ['global_role', 'ability', 'ability_parameter']
    global_role = models.ForeignKey(GlobalRole, related_name='abilities_as_global_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField(default=True)
    class Meta:
        unique_together = (('global_role', 'ability', 'ability_parameter'),)


class RoleAbility(Item):
    immutable_fields = Item.immutable_fields + ['role', 'ability', 'ability_parameter']
    role = models.ForeignKey(Role, related_name='abilities_as_role')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
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
    is_allowed = models.BooleanField(default=True)
    class Meta:
        unique_together = (('agent', 'ability', 'ability_parameter'),)


class ItemSetGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['itemset', 'ability', 'ability_parameter']
    itemset = models.ForeignKey(ItemSet, related_name='itemset_global_permissions_as_itemset')
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField(default=True)
    class Meta:
        unique_together = (('itemset', 'ability', 'ability_parameter'),)


class DefaultGlobalPermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['ability', 'ability_parameter']
    ability = models.CharField(max_length=255, choices=POSSIBLE_GLOBAL_ABILITIES)
    ability_parameter = models.CharField(max_length=255)
    is_allowed = models.BooleanField(default=True)
    class Meta:
        unique_together = (('ability', 'ability_parameter'),)


class AgentGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['agent', 'global_role']
    agent = models.ForeignKey(Agent, related_name='agent_global_role_permissions_as_agent')
    global_role = models.ForeignKey(GlobalRole, related_name='agent_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('agent', 'global_role'),)


class ItemSetGlobalRolePermission(GlobalPermission):
    immutable_fields = GlobalPermission.immutable_fields + ['itemset', 'global_role']
    itemset = models.ForeignKey(ItemSet, related_name='itemset_global_role_permissions_as_itemset')
    global_role = models.ForeignKey(GlobalRole, related_name='itemset_global_role_permissions_as_global_role')
    class Meta:
        unique_together = (('itemset', 'global_role'),)


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
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('agent', 'item', 'ability', 'ability_parameter'),)


class ItemSetPermission(Permission):
    immutable_fields = Permission.immutable_fields + ['itemset', 'item', 'ability', 'ability_parameter']
    itemset = models.ForeignKey(ItemSet, related_name='itemset_permissions_as_itemset')
    item = models.ForeignKey(Item, related_name='itemset_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('itemset', 'item', 'ability', 'ability_parameter'),)


class DefaultPermission(Permission):
    immutable_fields = Permission.immutable_fields + ['item', 'ability', 'ability_parameter']
    item = models.ForeignKey(Item, related_name='default_permissions_as_item')
    ability = models.CharField(max_length=255, choices=POSSIBLE_ABILITIES, db_index=True)
    ability_parameter = models.CharField(max_length=255, db_index=True)
    is_allowed = models.BooleanField(default=True, db_index=True)
    class Meta:
        unique_together = (('item', 'ability', 'ability_parameter'),)


class AgentRolePermission(Permission):
    immutable_fields = Permission.immutable_fields + ['agent', 'item', 'role']
    agent = models.ForeignKey(Agent, related_name='agent_role_permissions_as_agent')
    item = models.ForeignKey(Item, related_name='agent_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='agent_role_permissions_as_role')
    class Meta:
        unique_together = (('agent', 'item', 'role'),)


class ItemSetRolePermission(Permission):
    immutable_fields = Permission.immutable_fields + ['itemset', 'item', 'role']
    itemset = models.ForeignKey(ItemSet, related_name='itemset_role_permissions_as_itemset')
    item = models.ForeignKey(Item, related_name='itemset_role_permissions_as_item')
    role = models.ForeignKey(Role, related_name='itemset_role_permissions_as_role')
    class Meta:
        unique_together = (('itemset', 'item', 'role'),)


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
    format = models.CharField(max_length=255, default='html')


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


#TODO we should prevent top level names like 'static' and 'resource' and 'modules', although not a big deal since it doesn't overwrite
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

