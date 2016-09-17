# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'DemeAccountVersion.last_login'
        db.add_column(u'demeaccount_demeaccountversion', 'last_login',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0), null=True, blank=True),
                      keep_default=False)

        # Adding field 'DemeAccount.last_login'
        db.add_column(u'demeaccount_demeaccount', 'last_login',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1970, 1, 1, 0, 0), null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'DemeAccountVersion.last_login'
        db.delete_column(u'demeaccount_demeaccountversion', 'last_login')

        # Deleting field 'DemeAccount.last_login'
        db.delete_column(u'demeaccount_demeaccount', 'last_login')


    models = {
        u'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'agents_with_photo'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"})
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
        u'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.filedocument': {
            'Meta': {'object_name': 'FileDocument', '_ormbases': [u'cms.Document']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.imagedocument': {
            'Meta': {'object_name': 'ImageDocument', '_ormbases': [u'cms.FileDocument']},
            u'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
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
        u'demeaccount.demeaccount': {
            'Meta': {'object_name': 'DemeAccount', '_ormbases': [u'cms.AuthenticationMethod']},
            u'authenticationmethod_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.AuthenticationMethod']", 'unique': 'True', 'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True'}),
            'password_answer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password_question': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'unique': 'True', 'null': 'True'})
        },
        u'demeaccount.demeaccountversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DemeAccountVersion', '_ormbases': [u'cms.AuthenticationMethodVersion']},
            u'authenticationmethodversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.AuthenticationMethodVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1970, 1, 1, 0, 0)', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True'}),
            'password_answer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password_question': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'})
        }
    }

    complete_apps = ['demeaccount']