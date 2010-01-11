
from south.db import db
from django.db import models
from deme_django.modules.openid.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'OpenidAccountVersion'
        db.create_table('openid_openidaccountversion', (
            ('authenticationmethodversion_ptr', orm['openid.OpenidAccountVersion:authenticationmethodversion_ptr']),
        ))
        db.send_create_signal('openid', ['OpenidAccountVersion'])
        
        # Adding model 'OpenidAccount'
        db.create_table('openid_openidaccount', (
            ('authenticationmethod_ptr', orm['openid.OpenidAccount:authenticationmethod_ptr']),
            ('openid_url', orm['openid.OpenidAccount:openid_url']),
        ))
        db.send_create_signal('openid', ['OpenidAccount'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'OpenidAccountVersion'
        db.delete_table('openid_openidaccountversion')
        
        # Deleting model 'OpenidAccount'
        db.delete_table('openid_openidaccount')
        
    
    
    models = {
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.authenticationmethod': {
            'agent': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'authentication_methods'", 'null': 'True', 'to': "orm['cms.Agent']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.authenticationmethodversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'openid.openidaccount': {
            'authenticationmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'openid_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2047', 'unique': 'True', 'null': 'True'})
        },
        'openid.openidaccountversion': {
            'authenticationmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethodVersion']", 'unique': 'True', 'primary_key': 'True'})
        }
    }
    
    complete_apps = ['openid']
