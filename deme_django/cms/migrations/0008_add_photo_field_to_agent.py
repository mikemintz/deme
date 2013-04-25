# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from cms.models import AllToAllPermission
from cms.permissions import all_possible_permission_models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Agent.photo'
        db.add_column('cms_agent', 'photo', self.gf('django.db.models.ForeignKey')(default=None, related_name='agents_with_photo', null=True, blank=True, to=orm['cms.ImageDocument']), keep_default=False)

        # Adding field 'AgentVersion.photo'
        db.add_column('cms_agentversion', 'photo', self.gf('django.db.models.ForeignKey')(related_name='version_agents_with_photo', default=None, to=orm['cms.ImageDocument'], blank=True, null=True, db_index=False), keep_default=False)

        # Adding default permissions for the new fields
        for action in ['view', 'edit']:
            for field in ['Agent.photo']:
                ability = '%s %s' % (action, field)
                is_allowed = action == 'view'
                AllToAllPermission(ability=ability, is_allowed=is_allowed).save()


    def backwards(self, orm):
        
        # Deleting field 'Agent.photo'
        db.delete_column('cms_agent', 'photo_id')

        # Deleting field 'AgentVersion.photo'
        db.delete_column('cms_agentversion', 'photo_id')

        # Deleting permissions for the new fields
        for action in ['view', 'edit']:
            for field in ['Agent.photo']:
                for permission_model in all_possible_permission_models():
                    ability = '%s %s' % (action, field)
                    permission_model.objects.filter(ability=ability).delete()


    models = {
        'cms.actionnotice': {
            'Meta': {'object_name': 'ActionNotice'},
            'action_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices_created'", 'to': "orm['cms.Agent']"}),
            'action_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices'", 'to': "orm['cms.Item']"}),
            'action_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'action_summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'action_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'cms.addresscontactmethod': {
            'Meta': {'object_name': 'AddressContactMethod', '_ormbases': ['cms.ContactMethod']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.addresscontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AddressContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'agents_with_photo'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ImageDocument']"})
        },
        'cms.agentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AgentVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'related_name': "'version_agents_with_photo'", 'default': 'None', 'to': "orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        },
        'cms.aimcontactmethod': {
            'Meta': {'object_name': 'AIMContactMethod', '_ormbases': ['cms.ContactMethod']},
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.aimcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AIMContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.alltoallpermission': {
            'Meta': {'unique_together': "(('ability',),)", 'object_name': 'AllToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        },
        'cms.alltoonepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)", 'object_name': 'AllToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.alltosomepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)", 'object_name': 'AllToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.anonymousagent': {
            'Meta': {'object_name': 'AnonymousAgent', '_ormbases': ['cms.Agent']},
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.anonymousagentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AnonymousAgentVersion', '_ormbases': ['cms.AgentVersion']},
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethod': {
            'Meta': {'object_name': 'AuthenticationMethod', '_ormbases': ['cms.Item']},
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'authentication_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AuthenticationMethodVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collection': {
            'Meta': {'object_name': 'Collection', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collectionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CollectionVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.comment': {
            'Meta': {'object_name': 'Comment', '_ormbases': ['cms.Item']},
            'from_contact_method': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'comments_from_contactmethod'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ContactMethod']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'comments'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'})
        },
        'cms.commentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CommentVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethod': {
            'Meta': {'object_name': 'ContactMethod', '_ormbases': ['cms.Item']},
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'contact_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ContactMethodVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.createactionnotice': {
            'Meta': {'object_name': 'CreateActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurl': {
            'Meta': {'unique_together': "(('parent_url', 'path'),)", 'object_name': 'CustomUrl', '_ormbases': ['cms.ViewerRequest']},
            'parent_url': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_urls'", 'null': 'True', 'to': "orm['cms.ViewerRequest']"}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurlversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CustomUrlVersion', '_ormbases': ['cms.ViewerRequestVersion']},
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.deactivateactionnotice': {
            'Meta': {'object_name': 'DeactivateActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.demesetting': {
            'Meta': {'object_name': 'DemeSetting', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.demesettingversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DemeSettingVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.destroyactionnotice': {
            'Meta': {'object_name': 'DestroyActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocument': {
            'Meta': {'object_name': 'DjangoTemplateDocument', '_ormbases': ['cms.TextDocument']},
            'layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'django_template_documents_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DjangoTemplateDocumentVersion', '_ormbases': ['cms.TextDocumentVersion']},
            'layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_django_template_documents_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DocumentVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.editactionnotice': {
            'Meta': {'object_name': 'EditActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.editlock': {
            'Meta': {'object_name': 'EditLock'},
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edit_locks_as_editor'", 'to': "orm['cms.Agent']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edit_locks'", 'unique': 'True', 'to': "orm['cms.Item']"}),
            'lock_acquire_time': ('django.db.models.fields.DateTimeField', [], {}),
            'lock_refresh_time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cms.emailcontactmethod': {
            'Meta': {'object_name': 'EmailContactMethod', '_ormbases': ['cms.ContactMethod']},
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.emailcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'EmailContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.excerpt': {
            'Meta': {'object_name': 'Excerpt', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.excerptversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ExcerptVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.faxcontactmethod': {
            'Meta': {'object_name': 'FaxContactMethod', '_ormbases': ['cms.ContactMethod']},
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.faxcontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FaxContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.filedocument': {
            'Meta': {'object_name': 'FileDocument', '_ormbases': ['cms.Document']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FileDocumentVersion', '_ormbases': ['cms.DocumentVersion']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.folio': {
            'Meta': {'object_name': 'Folio', '_ormbases': ['cms.Collection']},
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'folios'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.folioversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'FolioVersion', '_ormbases': ['cms.CollectionVersion']},
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.group': {
            'Meta': {'object_name': 'Group', '_ormbases': ['cms.Collection']},
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'groups_with_image'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ImageDocument']"})
        },
        'cms.groupagent': {
            'Meta': {'object_name': 'GroupAgent', '_ormbases': ['cms.Agent']},
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'group_agents'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.groupagentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'GroupAgentVersion', '_ormbases': ['cms.AgentVersion']},
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.groupversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'GroupVersion', '_ormbases': ['cms.CollectionVersion']},
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.ForeignKey', [], {'related_name': "'version_groups_with_image'", 'default': 'None', 'to': "orm['cms.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        },
        'cms.htmldocument': {
            'Meta': {'object_name': 'HtmlDocument', '_ormbases': ['cms.TextDocument']},
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'HtmlDocumentVersion', '_ormbases': ['cms.TextDocumentVersion']},
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.imagedocument': {
            'Meta': {'object_name': 'ImageDocument', '_ormbases': ['cms.FileDocument']},
            'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.imagedocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ImageDocumentVersion', '_ormbases': ['cms.FileDocumentVersion']},
            'filedocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.item': {
            'Meta': {'object_name': 'Item'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True'}),
            'creator': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'items_created'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'destroyed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_list_address': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '63', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'email_sets_reply_to_all_subscribers': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'cms.itemversion': {
            'Meta': {'ordering': "['version_number']", 'unique_together': "(('current_item', 'version_number'),)", 'object_name': 'ItemVersion'},
            'current_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['cms.Item']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email_list_address': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '63', 'null': 'True', 'blank': 'True'}),
            'email_sets_reply_to_all_subscribers': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.membership': {
            'Meta': {'unique_together': "(('item', 'collection'),)", 'object_name': 'Membership', '_ormbases': ['cms.Item']},
            'collection': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_memberships'", 'null': 'True', 'to': "orm['cms.Collection']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'memberships'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'cms.membershipversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'MembershipVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'cms.onetoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)", 'object_name': 'OneToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_all_permissions_as_source'", 'to': "orm['cms.Agent']"})
        },
        'cms.onetoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'OneToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.onetosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'OneToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.person': {
            'Meta': {'object_name': 'Person', '_ormbases': ['cms.Agent']},
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.personversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PersonVersion', '_ormbases': ['cms.AgentVersion']},
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.phonecontactmethod': {
            'Meta': {'object_name': 'PhoneContactMethod', '_ormbases': ['cms.ContactMethod']},
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.phonecontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PhoneContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.reactivateactionnotice': {
            'Meta': {'object_name': 'ReactivateActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.recursivecomment': {
            'Meta': {'unique_together': "(('parent', 'child'),)", 'object_name': 'RecursiveComment'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_child'", 'to': "orm['cms.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_parent'", 'to': "orm['cms.Item']"})
        },
        'cms.recursivemembership': {
            'Meta': {'unique_together': "(('parent', 'child'),)", 'object_name': 'RecursiveMembership'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_child'", 'to': "orm['cms.Item']"}),
            'child_memberships': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cms.Membership']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_parent'", 'to': "orm['cms.Collection']"}),
            'permission_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'cms.relationactionnotice': {
            'Meta': {'object_name': 'RelationActionNotice', '_ormbases': ['cms.ActionNotice']},
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'}),
            'from_field_model': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relation_action_notices_from'", 'to': "orm['cms.Item']"}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'relation_added': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'cms.site': {
            'Meta': {'object_name': 'Site', '_ormbases': ['cms.ViewerRequest']},
            'default_layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.siteversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'SiteVersion', '_ormbases': ['cms.ViewerRequestVersion']},
            'default_layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.sometoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)", 'object_name': 'SomeToAllPermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_all_permissions_as_source'", 'to': "orm['cms.Collection']"})
        },
        'cms.sometoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'SomeToOnePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.sometosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)", 'object_name': 'SomeToSomePermission'},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.subscription': {
            'Meta': {'unique_together': "(('contact_method', 'item'),)", 'object_name': 'Subscription', '_ormbases': ['cms.Item']},
            'contact_method': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions'", 'null': 'True', 'to': "orm['cms.ContactMethod']"}),
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions_to'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'cms.subscriptionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'SubscriptionVersion', '_ormbases': ['cms.ItemVersion']},
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        'cms.textcomment': {
            'Meta': {'object_name': 'TextComment', '_ormbases': ['cms.TextDocument', 'cms.Comment']},
            'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Comment']", 'unique': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textcommentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextCommentVersion', '_ormbases': ['cms.TextDocumentVersion', 'cms.CommentVersion']},
            'commentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CommentVersion']", 'unique': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocument': {
            'Meta': {'object_name': 'TextDocument', '_ormbases': ['cms.Document']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentexcerpt': {
            'Meta': {'object_name': 'TextDocumentExcerpt', '_ormbases': ['cms.Excerpt', 'cms.TextDocument']},
            'excerpt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Excerpt']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'text_document_excerpts'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True'})
        },
        'cms.textdocumentexcerptversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentExcerptVersion', '_ormbases': ['cms.ExcerptVersion', 'cms.TextDocumentVersion']},
            'excerptversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ExcerptVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True'})
        },
        'cms.textdocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentVersion', '_ormbases': ['cms.DocumentVersion']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.transclusion': {
            'Meta': {'object_name': 'Transclusion', '_ormbases': ['cms.Item']},
            'from_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_from'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'to_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_to'", 'null': 'True', 'to': "orm['cms.Item']"})
        },
        'cms.transclusionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TransclusionVersion', '_ormbases': ['cms.ItemVersion']},
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.viewerrequest': {
            'Meta': {'object_name': 'ViewerRequest', '_ormbases': ['cms.Item']},
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'viewer_requests'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.Item']"}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.viewerrequestversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ViewerRequestVersion', '_ormbases': ['cms.ItemVersion']},
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'related_name': "'version_viewer_requests'", 'default': 'None', 'to': "orm['cms.Item']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpage': {
            'Meta': {'object_name': 'Webpage', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpageversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'WebpageVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethod': {
            'Meta': {'object_name': 'WebsiteContactMethod', '_ormbases': ['cms.ContactMethod']},
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethodversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'WebsiteContactMethodVersion', '_ormbases': ['cms.ContactMethodVersion']},
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        }
    }

    complete_apps = ['cms']
