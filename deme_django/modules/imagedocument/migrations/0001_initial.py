
from south.db import db
from django.db import models
from deme_django.modules.imagedocument.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'ImageDocument'
        db.create_table('imagedocument_imagedocument', (
            ('filedocument_ptr', orm['imagedocument.ImageDocument:filedocument_ptr']),
        ))
        db.send_create_signal('imagedocument', ['ImageDocument'])
        
        # Adding model 'ImageDocumentVersion'
        db.create_table('imagedocument_imagedocumentversion', (
            ('filedocumentversion_ptr', orm['imagedocument.ImageDocumentVersion:filedocumentversion_ptr']),
        ))
        db.send_create_signal('imagedocument', ['ImageDocumentVersion'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'ImageDocument'
        db.delete_table('imagedocument_imagedocument')
        
        # Deleting model 'ImageDocumentVersion'
        db.delete_table('imagedocument_imagedocumentversion')
        
    
    
    models = {
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.document': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocument': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.filedocumentversion': {
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'imagedocument.imagedocument': {
            'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'imagedocument.imagedocumentversion': {
            'filedocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['imagedocument']
