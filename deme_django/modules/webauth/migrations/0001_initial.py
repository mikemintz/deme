
from south.db import db
from django.db import models
from deme_django.modules.webauth.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'WebauthAccountVersion'
        db.create_table('webauth_webauthaccountversion', (
            ('authenticationmethodversion_ptr', orm['webauth.WebauthAccountVersion:authenticationmethodversion_ptr']),
            ('username', orm['webauth.WebauthAccountVersion:username']),
        ))
        db.send_create_signal('webauth', ['WebauthAccountVersion'])
        
        # Adding model 'WebauthAccount'
        db.create_table('webauth_webauthaccount', (
            ('authenticationmethod_ptr', orm['webauth.WebauthAccount:authenticationmethod_ptr']),
            ('username', orm['webauth.WebauthAccount:username']),
        ))
        db.send_create_signal('webauth', ['WebauthAccount'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'WebauthAccountVersion'
        db.delete_table('webauth_webauthaccountversion')
        
        # Deleting model 'WebauthAccount'
        db.delete_table('webauth_webauthaccount')
        
    
    
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
        'webauth.webauthaccount': {
            'authenticationmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'})
        },
        'webauth.webauthaccountversion': {
            'authenticationmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        }
    }
    
    complete_apps = ['webauth']
