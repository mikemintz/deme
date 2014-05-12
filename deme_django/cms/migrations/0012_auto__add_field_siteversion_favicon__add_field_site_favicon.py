# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SiteVersion.favicon'
        db.add_column(u'cms_siteversion', 'favicon',
                      self.gf('django.db.models.ForeignKey')(related_name='version_sites_with_favicon', default=None, to=orm['cms.ImageDocument'], blank=True, null=True, db_index=False),
                      keep_default=False)

        # Adding field 'Site.favicon'
        db.add_column(u'cms_site', 'favicon',
                      self.gf('django.db.models.ForeignKey')(default=None, related_name='sites_with_favicon', null=True, blank=True, to=orm['cms.ImageDocument']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'SiteVersion.favicon'
        db.delete_column(u'cms_siteversion', 'favicon_id')

        # Deleting field 'Site.favicon'
        db.delete_column(u'cms_site', 'favicon_id')


    models = {
        u'cms.actionnotice': {
            'Meta': {'object_name': 'ActionNotice'},
            'action_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices_created'", 'to': u"orm['cms.Agent']"}),
            'action_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices'", 'to': u"orm['cms.Item']"}),
            'action_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'action_summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'action_time': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'cms.addresscontactmethod': {
            'Meta': {'object_name': 'AddressContactMethod', '_ormbases': [u'cms.ContactMethod']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'cms.addresscontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AddressContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        u'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'agents_with_photo'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"})
        },
        u'cms.agentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AgentVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'related_name': "'version_agents_with_photo'", 'default': 'None', 'to': u"orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        },
        u'cms.aimcontactmethod': {
            'Meta': {'object_name': 'AIMContactMethod', '_ormbases': [u'cms.ContactMethod']},
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        u'cms.aimcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AIMContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        u'cms.alltoallpermission': {
            'Meta': {'unique_together': "(('ability',),)", 'object_name': 'AllToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        },
        u'cms.alltoonepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)", 'object_name': 'AllToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_one_permissions_as_target'", 'to': u"orm['cms.Item']"})
        },
        u'cms.alltosomepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)", 'object_name': 'AllToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_some_permissions_as_target'", 'to': u"orm['cms.Collection']"})
        },
        u'cms.anonymousagent': {
            'Meta': {'object_name': 'AnonymousAgent', '_ormbases': [u'cms.Agent']},
            u'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.anonymousagentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AnonymousAgentVersion', '_ormbases': [u'cms.AgentVersion']},
            u'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.authenticationmethod': {
            'Meta': {'object_name': 'AuthenticationMethod', '_ormbases': [u'cms.Item']},
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'authentication_methods'", 'null': 'True', 'to': u"orm['cms.Agent']"}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.authenticationmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AuthenticationMethodVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.collection': {
            'Meta': {'object_name': 'Collection', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.collectionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CollectionVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.comment': {
            'Meta': {'object_name': 'Comment', '_ormbases': [u'cms.Item']},
            'from_contact_method': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'comments_from_contactmethod'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ContactMethod']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'comments'", 'null': 'True', 'to': u"orm['cms.Item']"}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'})
        },
        u'cms.commentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CommentVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.contactmethod': {
            'Meta': {'object_name': 'ContactMethod', '_ormbases': [u'cms.Item']},
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'contact_methods'", 'null': 'True', 'to': u"orm['cms.Agent']"}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.contactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ContactMethodVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.createactionnotice': {
            'Meta': {'object_name': 'CreateActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.customurl': {
            'Meta': {'unique_together': "(('parent_url', 'path'),)", 'object_name': 'CustomUrl', '_ormbases': [u'cms.ViewerRequest']},
            'parent_url': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_urls'", 'null': 'True', 'to': u"orm['cms.ViewerRequest']"}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.customurlversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CustomUrlVersion', '_ormbases': [u'cms.ViewerRequestVersion']},
            'parent_url': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'version_child_urls'", 'null': 'True', 'db_index': 'False', 'to': u"orm['cms.ViewerRequest']"}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.deactivateactionnotice': {
            'Meta': {'object_name': 'DeactivateActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.demesetting': {
            'Meta': {'object_name': 'DemeSetting', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'cms.demesettingversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DemeSettingVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'cms.destroyactionnotice': {
            'Meta': {'object_name': 'DestroyActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.djangotemplatedocument': {
            'Meta': {'object_name': 'DjangoTemplateDocument', '_ormbases': [u'cms.TextDocument']},
            'layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'django_template_documents_with_layout'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.DjangoTemplateDocument']"}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            u'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.djangotemplatedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DjangoTemplateDocumentVersion', '_ormbases': [u'cms.TextDocumentVersion']},
            'layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_django_template_documents_with_layout'", 'default': 'None', 'to': u"orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            u'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.documentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DocumentVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.editactionnotice': {
            'Meta': {'object_name': 'EditActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.editlock': {
            'Meta': {'object_name': 'EditLock'},
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edit_locks_as_editor'", 'to': u"orm['cms.Agent']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edit_locks'", 'unique': 'True', 'to': u"orm['cms.Item']"}),
            'lock_acquire_time': ('django.db.models.fields.DateTimeField', [], {}),
            'lock_refresh_time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'cms.emailcontactmethod': {
            'Meta': {'object_name': 'EmailContactMethod', '_ormbases': [u'cms.ContactMethod']},
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        u'cms.emailcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'EmailContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        u'cms.excerpt': {
            'Meta': {'object_name': 'Excerpt', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.excerptversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ExcerptVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.faxcontactmethod': {
            'Meta': {'object_name': 'FaxContactMethod', '_ormbases': [u'cms.ContactMethod']},
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        u'cms.faxcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FaxContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        u'cms.filedocument': {
            'Meta': {'object_name': 'FileDocument', '_ormbases': [u'cms.Document']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.filedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FileDocumentVersion', '_ormbases': [u'cms.DocumentVersion']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.folio': {
            'Meta': {'object_name': 'Folio', '_ormbases': [u'cms.Collection']},
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'folios'", 'unique': 'True', 'null': 'True', 'to': u"orm['cms.Group']"})
        },
        u'cms.folioversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FolioVersion', '_ormbases': [u'cms.CollectionVersion']},
            u'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.group': {
            'Meta': {'object_name': 'Group', '_ormbases': [u'cms.Collection']},
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'groups_with_image'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"})
        },
        u'cms.groupagent': {
            'Meta': {'object_name': 'GroupAgent', '_ormbases': [u'cms.Agent']},
            u'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'group_agents'", 'unique': 'True', 'null': 'True', 'to': u"orm['cms.Group']"})
        },
        u'cms.groupagentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'GroupAgentVersion', '_ormbases': [u'cms.AgentVersion']},
            u'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.groupversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'GroupVersion', '_ormbases': [u'cms.CollectionVersion']},
            u'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.ForeignKey', [], {'related_name': "'version_groups_with_image'", 'default': 'None', 'to': u"orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        },
        u'cms.htmldocument': {
            'Meta': {'object_name': 'HtmlDocument', '_ormbases': [u'cms.TextDocument']},
            u'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.htmldocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'HtmlDocumentVersion', '_ormbases': [u'cms.TextDocumentVersion']},
            u'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.imagedocument': {
            'Meta': {'object_name': 'ImageDocument', '_ormbases': [u'cms.FileDocument']},
            u'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.imagedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ImageDocumentVersion', '_ormbases': [u'cms.FileDocumentVersion']},
            u'filedocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.FileDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.item': {
            'Meta': {'object_name': 'Item'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True'}),
            'creator': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'items_created'", 'null': 'True', 'to': u"orm['cms.Agent']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'destroyed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_list_address': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '63', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'email_sets_reply_to_all_subscribers': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        u'cms.itemversion': {
            'Meta': {'ordering': "['version_number']", 'unique_together': "(('current_item', 'version_number'),)", 'object_name': 'ItemVersion'},
            'current_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': u"orm['cms.Item']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email_list_address': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '63', 'null': 'True', 'blank': 'True'}),
            'email_sets_reply_to_all_subscribers': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'cms.membership': {
            'Meta': {'unique_together': "(('item', 'collection'),)", 'object_name': 'Membership', '_ormbases': [u'cms.Item']},
            'collection': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_memberships'", 'null': 'True', 'to': u"orm['cms.Collection']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'memberships'", 'null': 'True', 'to': u"orm['cms.Item']"}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'cms.membershipversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'MembershipVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'cms.onetoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)", 'object_name': 'OneToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_all_permissions_as_source'", 'to': u"orm['cms.Agent']"})
        },
        u'cms.onetoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'OneToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_source'", 'to': u"orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_target'", 'to': u"orm['cms.Item']"})
        },
        u'cms.onetosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'OneToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_source'", 'to': u"orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_target'", 'to': u"orm['cms.Collection']"})
        },
        u'cms.person': {
            'Meta': {'object_name': 'Person', '_ormbases': [u'cms.Agent']},
            u'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'cms.personversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PersonVersion', '_ormbases': [u'cms.AgentVersion']},
            u'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'cms.phonecontactmethod': {
            'Meta': {'object_name': 'PhoneContactMethod', '_ormbases': [u'cms.ContactMethod']},
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        u'cms.phonecontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PhoneContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        u'cms.reactivateactionnotice': {
            'Meta': {'object_name': 'ReactivateActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.recursivecomment': {
            'Meta': {'unique_together': "(('parent', 'child'),)", 'object_name': 'RecursiveComment'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_child'", 'to': u"orm['cms.Comment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_parent'", 'to': u"orm['cms.Item']"})
        },
        u'cms.recursivemembership': {
            'Meta': {'unique_together': "(('parent', 'child'),)", 'object_name': 'RecursiveMembership'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_child'", 'to': u"orm['cms.Item']"}),
            'child_memberships': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['cms.Membership']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_parent'", 'to': u"orm['cms.Collection']"}),
            'permission_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'cms.relationactionnotice': {
            'Meta': {'object_name': 'RelationActionNotice', '_ormbases': [u'cms.ActionNotice']},
            u'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'}),
            'from_field_model': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relation_action_notices_from'", 'to': u"orm['cms.Item']"}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'relation_added': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'cms.site': {
            'Meta': {'object_name': 'Site', '_ormbases': [u'cms.ViewerRequest']},
            'default_layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_layout'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.DjangoTemplateDocument']"}),
            'favicon': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_favicon'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'logo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_logo'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.siteversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'SiteVersion', '_ormbases': [u'cms.ViewerRequestVersion']},
            'default_layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_layout'", 'default': 'None', 'to': u"orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'favicon': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_favicon'", 'default': 'None', 'to': u"orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'logo': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_logo'", 'default': 'None', 'to': u"orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.sometoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)", 'object_name': 'SomeToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_all_permissions_as_source'", 'to': u"orm['cms.Collection']"})
        },
        u'cms.sometoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'SomeToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_source'", 'to': u"orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_target'", 'to': u"orm['cms.Item']"})
        },
        u'cms.sometosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'SomeToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_source'", 'to': u"orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_target'", 'to': u"orm['cms.Collection']"})
        },
        u'cms.subscription': {
            'Meta': {'unique_together': "(('contact_method', 'item'),)", 'object_name': 'Subscription', '_ormbases': [u'cms.Item']},
            'contact_method': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions'", 'null': 'True', 'to': u"orm['cms.ContactMethod']"}),
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions_to'", 'null': 'True', 'to': u"orm['cms.Item']"}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'cms.subscriptionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'SubscriptionVersion', '_ormbases': [u'cms.ItemVersion']},
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'cms.textcomment': {
            'Meta': {'object_name': 'TextComment', '_ormbases': [u'cms.TextDocument', u'cms.Comment']},
            u'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Comment']", 'unique': 'True'}),
            u'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.textcommentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextCommentVersion', '_ormbases': [u'cms.TextDocumentVersion', u'cms.CommentVersion']},
            u'commentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.CommentVersion']", 'unique': 'True'}),
            u'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.textdocument': {
            'Meta': {'object_name': 'TextDocument', '_ormbases': [u'cms.Document']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.textdocumentexcerpt': {
            'Meta': {'object_name': 'TextDocumentExcerpt', '_ormbases': [u'cms.Excerpt', u'cms.TextDocument']},
            u'excerpt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Excerpt']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'text_document_excerpts'", 'null': 'True', 'to': u"orm['cms.TextDocument']"}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            u'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocument']", 'unique': 'True'})
        },
        u'cms.textdocumentexcerptversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentExcerptVersion', '_ormbases': [u'cms.ExcerptVersion', u'cms.TextDocumentVersion']},
            u'excerptversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ExcerptVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            u'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocumentVersion']", 'unique': 'True'})
        },
        u'cms.textdocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentVersion', '_ormbases': [u'cms.DocumentVersion']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.transclusion': {
            'Meta': {'object_name': 'Transclusion', '_ormbases': [u'cms.Item']},
            'from_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_from'", 'null': 'True', 'to': u"orm['cms.TextDocument']"}),
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'to_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_to'", 'null': 'True', 'to': u"orm['cms.Item']"})
        },
        u'cms.transclusionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TransclusionVersion', '_ormbases': [u'cms.ItemVersion']},
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.viewerrequest': {
            'Meta': {'object_name': 'ViewerRequest', '_ormbases': [u'cms.Item']},
            'action': ('django.db.models.fields.CharField', [], {'default': "'show'", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'viewer_requests'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.Item']"}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "'item'", 'max_length': '255', 'null': 'True'})
        },
        u'cms.viewerrequestversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ViewerRequestVersion', '_ormbases': [u'cms.ItemVersion']},
            'action': ('django.db.models.fields.CharField', [], {'default': "'show'", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'related_name': "'version_viewer_requests'", 'default': 'None', 'to': u"orm['cms.Item']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "'item'", 'max_length': '255', 'null': 'True'})
        },
        u'cms.webpage': {
            'Meta': {'object_name': 'Webpage', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        u'cms.webpageversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'WebpageVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        u'cms.websitecontactmethod': {
            'Meta': {'object_name': 'WebsiteContactMethod', '_ormbases': [u'cms.ContactMethod']},
            u'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        u'cms.websitecontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'WebsiteContactMethodVersion', '_ormbases': [u'cms.ContactMethodVersion']},
            u'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        }
    }

    complete_apps = ['cms']