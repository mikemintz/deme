
from south.db import db
from django.db import models
from deme_django.modules.demeaccount.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'DemeAccountVersion'
        db.create_table('demeaccount_demeaccountversion', (
            ('authenticationmethodversion_ptr', orm['demeaccount.DemeAccountVersion:authenticationmethodversion_ptr']),
            ('username', orm['demeaccount.DemeAccountVersion:username']),
            ('password', orm['demeaccount.DemeAccountVersion:password']),
            ('password_question', orm['demeaccount.DemeAccountVersion:password_question']),
            ('password_answer', orm['demeaccount.DemeAccountVersion:password_answer']),
        ))
        db.send_create_signal('demeaccount', ['DemeAccountVersion'])
        
        # Adding model 'DemeAccount'
        db.create_table('demeaccount_demeaccount', (
            ('authenticationmethod_ptr', orm['demeaccount.DemeAccount:authenticationmethod_ptr']),
            ('username', orm['demeaccount.DemeAccount:username']),
            ('password', orm['demeaccount.DemeAccount:password']),
            ('password_question', orm['demeaccount.DemeAccount:password_question']),
            ('password_answer', orm['demeaccount.DemeAccount:password_answer']),
        ))
        db.send_create_signal('demeaccount', ['DemeAccount'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'DemeAccountVersion'
        db.delete_table('demeaccount_demeaccountversion')
        
        # Deleting model 'DemeAccount'
        db.delete_table('demeaccount_demeaccount')
        
    
    
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
        'demeaccount.demeaccount': {
            'authenticationmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True'}),
            'password_answer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password_question': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'})
        },
        'demeaccount.demeaccountversion': {
            'authenticationmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AuthenticationMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True'}),
            'password_answer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password_question': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        }
    }
    
    complete_apps = ['demeaccount']
