
from south.db import db
from django.db import models
from deme_django.cms.models import *

class Migration:
    
    def forwards(self, orm):
        db.alter_column('cms_subscription', 'subscribe_relations', FixedBooleanField(default=False))
        db.alter_column('cms_subscriptionversion', 'subscribe_relations', FixedBooleanField(default=False))
    
    
    def backwards(self, orm):
        db.alter_column('cms_subscriptionversion', 'subscribe_relations', FixedBooleanField(default=True))
    
    
    models = {
        'cms.actionnotice': {
            'action_agent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices_created'", 'to': "orm['cms.Agent']"}),
            'action_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'action_notices'", 'to': "orm['cms.Item']"}),
            'action_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'action_summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'action_time': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'cms.addresscontactmethod': {
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.addresscontactmethodversion': {
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'street2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.agentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.aimcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.aimcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'screen_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.alltoallpermission': {
            'Meta': {'unique_together': "(('ability',),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'cms.alltoonepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.alltosomepermission': {
            'Meta': {'unique_together': "(('ability', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'all_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.anonymousagent': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.anonymousagentversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethod': {
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'authentication_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethodversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collection': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collectionversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.comment': {
            'from_contact_method': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'comments_from_contactmethod'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ContactMethod']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'comments'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'})
        },
        'cms.commentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethod': {
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'contact_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.contactmethodversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.createactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurl': {
            'Meta': {'unique_together': "(('parent_url', 'path'),)"},
            'parent_url': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_urls'", 'null': 'True', 'to': "orm['cms.ViewerRequest']"}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.customurlversion': {
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.deactivateactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.demesetting': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.demesettingversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.destroyactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocument': {
            'layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'django_template_documents_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.djangotemplatedocumentversion': {
            'layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_django_template_documents_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'override_default_layout': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.document': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.editactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.emailcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.emailcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '320', 'null': 'True'})
        },
        'cms.excerpt': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.excerptversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.faxcontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.faxcontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.filedocument': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocumentversion': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.folio': {
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'folios'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.folioversion': {
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.group': {
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.groupagent': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'group': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'group_agents'", 'unique': 'True', 'null': 'True', 'to': "orm['cms.Group']"})
        },
        'cms.groupagentversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.groupversion': {
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocument': {
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocumentversion': {
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.item': {
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True'}),
            'creator': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'items_created'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'destroyed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_type_string': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'cms.itemversion': {
            'Meta': {'unique_together': "(('current_item', 'version_number'),)"},
            'current_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['cms.Item']"}),
            'default_viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'version_number': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'cms.membership': {
            'Meta': {'unique_together': "(('item', 'collection'),)"},
            'collection': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'child_memberships'", 'null': 'True', 'to': "orm['cms.Collection']"}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'memberships'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.membershipversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'permission_enabled': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.onetoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_all_permissions_as_source'", 'to': "orm['cms.Agent']"})
        },
        'cms.onetoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.onetosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_source'", 'to': "orm['cms.Agent']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'one_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.person': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.personversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.phonecontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.phonecontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'null': 'True'})
        },
        'cms.reactivateactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.recursivecomment': {
            'Meta': {'unique_together': "(('parent', 'child'),)"},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_child'", 'to': "orm['cms.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_comments_as_parent'", 'to': "orm['cms.Item']"})
        },
        'cms.recursivemembership': {
            'Meta': {'unique_together': "(('parent', 'child'),)"},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_child'", 'to': "orm['cms.Item']"}),
            'child_memberships': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cms.Membership']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recursive_memberships_as_parent'", 'to': "orm['cms.Collection']"}),
            'permission_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'cms.relationactionnotice': {
            'actionnotice_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ActionNotice']", 'unique': 'True', 'primary_key': 'True'}),
            'from_field_model': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'relation_action_notices_from'", 'to': "orm['cms.Item']"}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'relation_added': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'cms.site': {
            'default_layout': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'sites_with_layout'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.DjangoTemplateDocument']"}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'viewerrequest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequest']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.siteversion': {
            'default_layout': ('django.db.models.ForeignKey', [], {'related_name': "'version_sites_with_layout'", 'default': 'None', 'to': "orm['cms.DjangoTemplateDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'viewerrequestversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ViewerRequestVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.sometoallpermission': {
            'Meta': {'unique_together': "(('ability', 'source'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_all_permissions_as_source'", 'to': "orm['cms.Collection']"})
        },
        'cms.sometoonepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_one_permissions_as_target'", 'to': "orm['cms.Item']"})
        },
        'cms.sometosomepermission': {
            'Meta': {'unique_together': "(('ability', 'source', 'target'),)"},
            'ability': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_source'", 'to': "orm['cms.Collection']"}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'some_to_some_permissions_as_target'", 'to': "orm['cms.Collection']"})
        },
        'cms.subscription': {
            'Meta': {'unique_together': "(('contact_method', 'item'),)"},
            'contact_method': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions'", 'null': 'True', 'to': "orm['cms.ContactMethod']"}),
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'subscriptions_to'", 'null': 'True', 'to': "orm['cms.Item']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.subscriptionversion': {
            'deep': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'subscribe_comments': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_delete': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_edit': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_members': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True'}),
            'subscribe_relations': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'})
        },
        'cms.textcomment': {
            'comment_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Comment']", 'unique': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textcommentversion': {
            'commentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CommentVersion']", 'unique': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocument': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentexcerpt': {
            'excerpt_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Excerpt']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'text_document_excerpts'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True'})
        },
        'cms.textdocumentexcerptversion': {
            'excerptversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ExcerptVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'length': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'start_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'text_document_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True'})
        },
        'cms.textdocumentversion': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.transclusion': {
            'from_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_from'", 'null': 'True', 'to': "orm['cms.TextDocument']"}),
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'from_item_version_number': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'to_item': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'transclusions_to'", 'null': 'True', 'to': "orm['cms.Item']"})
        },
        'cms.transclusionversion': {
            'from_item_index': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.viewerrequest': {
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'viewer_requests'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.Item']"}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.viewerrequestversion': {
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'aliased_item': ('django.db.models.ForeignKey', [], {'related_name': "'version_viewer_requests'", 'default': 'None', 'to': "orm['cms.Item']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'format': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '255', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'viewer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpage': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.webpageversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethod': {
            'contactmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        },
        'cms.websitecontactmethodversion': {
            'contactmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ContactMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "'http://'", 'max_length': '255', 'null': 'True'})
        }
    }
    
    complete_apps = ['cms']
