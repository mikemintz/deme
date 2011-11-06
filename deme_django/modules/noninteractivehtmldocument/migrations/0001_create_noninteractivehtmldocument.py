# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'NonInteractiveHtmlDocument'
        db.create_table('noninteractivehtmldocument_noninteractivehtmldocument', (
            ('htmldocument_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocument'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('noninteractivehtmldocument', ['NonInteractiveHtmlDocument'])

        # Adding model 'NonInteractiveHtmlDocumentVersion'
        db.create_table('noninteractivehtmldocument_noninteractivehtmldocumentversion', (
            ('htmldocumentversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocumentVersion'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('noninteractivehtmldocument', ['NonInteractiveHtmlDocumentVersion'])


    def backwards(self, orm):
        
        # Deleting model 'NonInteractiveHtmlDocument'
        db.delete_table('noninteractivehtmldocument_noninteractivehtmldocument')

        # Deleting model 'NonInteractiveHtmlDocumentVersion'
        db.delete_table('noninteractivehtmldocument_noninteractivehtmldocumentversion')


    models = {
        'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DocumentVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocument': {
            'Meta': {'object_name': 'HtmlDocument', '_ormbases': ['cms.TextDocument']},
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.htmldocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'HtmlDocumentVersion', '_ormbases': ['cms.TextDocumentVersion']},
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'cms.textdocument': {
            'Meta': {'object_name': 'TextDocument', '_ormbases': ['cms.Document']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentVersion', '_ormbases': ['cms.DocumentVersion']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'noninteractivehtmldocument.noninteractivehtmldocument': {
            'Meta': {'object_name': 'NonInteractiveHtmlDocument', '_ormbases': ['cms.HtmlDocument']},
            'htmldocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'noninteractivehtmldocument.noninteractivehtmldocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'NonInteractiveHtmlDocumentVersion', '_ormbases': ['cms.HtmlDocumentVersion']},
            'htmldocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['noninteractivehtmldocument']
