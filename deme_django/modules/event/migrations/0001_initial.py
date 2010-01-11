
from south.db import db
from django.db import models
from deme_django.modules.event.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Event'
        db.create_table('event_event', (
            ('htmldocument_ptr', orm['event.Event:htmldocument_ptr']),
            ('start_date', orm['event.Event:start_date']),
            ('start_time', orm['event.Event:start_time']),
            ('end_date', orm['event.Event:end_date']),
            ('end_time', orm['event.Event:end_time']),
            ('location', orm['event.Event:location']),
            ('time_zone', orm['event.Event:time_zone']),
        ))
        db.send_create_signal('event', ['Event'])
        
        # Adding model 'Calendar'
        db.create_table('event_calendar', (
            ('collection_ptr', orm['event.Calendar:collection_ptr']),
        ))
        db.send_create_signal('event', ['Calendar'])
        
        # Adding model 'EventVersion'
        db.create_table('event_eventversion', (
            ('htmldocumentversion_ptr', orm['event.EventVersion:htmldocumentversion_ptr']),
            ('start_date', orm['event.EventVersion:start_date']),
            ('start_time', orm['event.EventVersion:start_time']),
            ('end_date', orm['event.EventVersion:end_date']),
            ('end_time', orm['event.EventVersion:end_time']),
            ('location', orm['event.EventVersion:location']),
            ('time_zone', orm['event.EventVersion:time_zone']),
        ))
        db.send_create_signal('event', ['EventVersion'])
        
        # Adding model 'CalendarVersion'
        db.create_table('event_calendarversion', (
            ('collectionversion_ptr', orm['event.CalendarVersion:collectionversion_ptr']),
        ))
        db.send_create_signal('event', ['CalendarVersion'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Event'
        db.delete_table('event_event')
        
        # Deleting model 'Calendar'
        db.delete_table('event_calendar')
        
        # Deleting model 'EventVersion'
        db.delete_table('event_eventversion')
        
        # Deleting model 'CalendarVersion'
        db.delete_table('event_calendarversion')
        
    
    
    models = {
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.collection': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collectionversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.document': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.documentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'cms.textdocument': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentversion': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'event.calendar': {
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'event.calendarversion': {
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'event.event': {
            'end_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': "''", 'null': 'True'}),
            'htmldocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocument']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': "''", 'null': 'True'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'default': "'America/Los_Angeles'", 'max_length': '255', 'null': 'True'})
        },
        'event.eventversion': {
            'end_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'default': "''", 'null': 'True'}),
            'htmldocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocumentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {'default': "''", 'null': 'True'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'default': "'America/Los_Angeles'", 'max_length': '255', 'null': 'True'})
        }
    }
    
    complete_apps = ['event']
