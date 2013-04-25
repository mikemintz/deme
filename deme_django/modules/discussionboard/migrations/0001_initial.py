# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DiscussionBoard'
        db.create_table('discussionboard_discussionboard', (
            ('item_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.Item'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('discussionboard', ['DiscussionBoard'])

        # Adding model 'DiscussionBoardVersion'
        db.create_table('discussionboard_discussionboardversion', (
            ('itemversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.ItemVersion'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('discussionboard', ['DiscussionBoardVersion'])


    def backwards(self, orm):
        
        # Deleting model 'DiscussionBoard'
        db.delete_table('discussionboard_discussionboard')

        # Deleting model 'DiscussionBoardVersion'
        db.delete_table('discussionboard_discussionboardversion')


    models = {
        'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'agents_with_photo'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.ImageDocument']"})
        },
        'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocument': {
            'Meta': {'object_name': 'FileDocument', '_ormbases': ['cms.Document']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.imagedocument': {
            'Meta': {'object_name': 'ImageDocument', '_ormbases': ['cms.FileDocument']},
            'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
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
        'discussionboard.discussionboard': {
            'Meta': {'object_name': 'DiscussionBoard', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'discussionboard.discussionboardversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DiscussionBoardVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['discussionboard']
