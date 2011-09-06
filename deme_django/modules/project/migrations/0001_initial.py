# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from cms.models import AllToAllPermission
from cms.permissions import all_possible_permission_models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Project'
        db.create_table('project_project', (
            ('collection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.Collection'], unique=True, primary_key=True)),
            ('due_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('due_time', self.gf('django.db.models.fields.TimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('project', ['Project'])

        # Adding model 'ProjectVersion'
        db.create_table('project_projectversion', (
            ('collectionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CollectionVersion'], unique=True, primary_key=True)),
            ('due_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('due_time', self.gf('django.db.models.fields.TimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('project', ['ProjectVersion'])

        # Adding model 'Task'
        db.create_table('project_task', (
            ('htmldocument_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocument'], unique=True, primary_key=True)),
            ('due_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('beginning_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('due_time', self.gf('django.db.models.fields.TimeField')(default=None, null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.CharField')(default='Low', max_length=10, null=True)),
            ('length', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=6, decimal_places=2)),
            ('status', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=16, null=True)),
            ('is_repeating', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('task_handler', self.gf('django.db.models.ForeignKey')(default=None, related_name='task_handler', null=True, blank=True, to=orm['cms.Agent'])),
        ))
        db.send_create_signal('project', ['Task'])

        # Adding model 'TaskVersion'
        db.create_table('project_taskversion', (
            ('htmldocumentversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocumentVersion'], unique=True, primary_key=True)),
            ('due_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('beginning_date', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('due_time', self.gf('django.db.models.fields.TimeField')(default=None, null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.CharField')(default='Low', max_length=10, null=True)),
            ('length', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=6, decimal_places=2)),
            ('status', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=16, null=True)),
            ('is_repeating', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('task_handler', self.gf('django.db.models.ForeignKey')(related_name='version_task_handler', default=None, to=orm['cms.Agent'], blank=True, null=True, db_index=False)),
        ))
        db.send_create_signal('project', ['TaskVersion'])

        # Adding model 'TaskDependency'
        db.create_table('project_taskdependency', (
            ('item_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.Item'], unique=True, primary_key=True)),
            ('dependent_task', self.gf('django.db.models.ForeignKey')(default=None, related_name='dependent_task', null=True, blank=True, to=orm['project.Task'])),
            ('required_task', self.gf('django.db.models.ForeignKey')(default=None, related_name='required_task', null=True, blank=True, to=orm['project.Task'])),
        ))
        db.send_create_signal('project', ['TaskDependency'])

        # Adding model 'TaskDependencyVersion'
        db.create_table('project_taskdependencyversion', (
            ('itemversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.ItemVersion'], unique=True, primary_key=True)),
            ('dependent_task', self.gf('django.db.models.ForeignKey')(related_name='version_dependent_task', default=None, to=orm['project.Task'], blank=True, null=True, db_index=False)),
            ('required_task', self.gf('django.db.models.ForeignKey')(related_name='version_required_task', default=None, to=orm['project.Task'], blank=True, null=True, db_index=False)),
        ))
        db.send_create_signal('project', ['TaskDependencyVersion'])

        # Adding default permissions for the new item types
        introduced_abilities = ['create Project', 'create Task', 'create TaskDependency', 'view Task.due_date', 'edit Task.due_date', 'view Task.beginning_date', 'edit Task.beginning_date', 'view Task.due_time', 'edit Task.due_time', 'view Task.priority', 'edit Task.priority', 'view Task.length', 'edit Task.length', 'view Task.status', 'edit Task.status', 'view Task.is_repeating', 'edit Task.is_repeating', 'view Task.task_handler', 'edit Task.task_handler', 'view TaskDependency.dependent_task', 'view TaskDependency.required_task']
        for ability in introduced_abilities:
            is_allowed = ability.startswith('view ')
            AllToAllPermission(ability=ability, is_allowed=is_allowed).save()


    def backwards(self, orm):
        
        # Deleting model 'Project'
        db.delete_table('project_project')

        # Deleting model 'ProjectVersion'
        db.delete_table('project_projectversion')

        # Deleting model 'Task'
        db.delete_table('project_task')

        # Deleting model 'TaskVersion'
        db.delete_table('project_taskversion')

        # Deleting model 'TaskDependency'
        db.delete_table('project_taskdependency')

        # Deleting model 'TaskDependencyVersion'
        db.delete_table('project_taskdependencyversion')

        # Deleting permissions for the new fields
        introduced_abilities = ['create Project', 'create Task', 'create TaskDependency', 'view Task.due_date', 'edit Task.due_date', 'view Task.beginning_date', 'edit Task.beginning_date', 'view Task.due_time', 'edit Task.due_time', 'view Task.priority', 'edit Task.priority', 'view Task.length', 'edit Task.length', 'view Task.status', 'edit Task.status', 'view Task.is_repeating', 'edit Task.is_repeating', 'view Task.task_handler', 'edit Task.task_handler', 'view TaskDependency.dependent_task', 'view TaskDependency.required_task']
        for ability in introduced_abilities:
            for permission_model in all_possible_permission_models():
                permission_model.objects.filter(ability=ability).delete()

    models = {
        'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.collection': {
            'Meta': {'object_name': 'Collection', '_ormbases': ['cms.Item']},
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.collectionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CollectionVersion', '_ormbases': ['cms.ItemVersion']},
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'project.project': {
            'Meta': {'object_name': 'Project', '_ormbases': ['cms.Collection']},
            'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_time': ('django.db.models.fields.TimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'project.projectversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ProjectVersion', '_ormbases': ['cms.CollectionVersion']},
            'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_time': ('django.db.models.fields.TimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'project.task': {
            'Meta': {'object_name': 'Task', '_ormbases': ['cms.HtmlDocument']},
            'beginning_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_time': ('django.db.models.fields.TimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'htmldocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocument']", 'unique': 'True', 'primary_key': 'True'}),
            'is_repeating': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'length': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '6', 'decimal_places': '2'}),
            'priority': ('django.db.models.fields.CharField', [], {'default': "'Low'", 'max_length': '10', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '16', 'null': 'True'}),
            'task_handler': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'task_handler'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.Agent']"})
        },
        'project.taskdependency': {
            'Meta': {'object_name': 'TaskDependency', '_ormbases': ['cms.Item']},
            'dependent_task': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'dependent_task'", 'null': 'True', 'blank': 'True', 'to': "orm['project.Task']"}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'required_task': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'required_task'", 'null': 'True', 'blank': 'True', 'to': "orm['project.Task']"})
        },
        'project.taskdependencyversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TaskDependencyVersion', '_ormbases': ['cms.ItemVersion']},
            'dependent_task': ('django.db.models.ForeignKey', [], {'related_name': "'version_dependent_task'", 'default': 'None', 'to': "orm['project.Task']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'required_task': ('django.db.models.ForeignKey', [], {'related_name': "'version_required_task'", 'default': 'None', 'to': "orm['project.Task']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        },
        'project.taskversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TaskVersion', '_ormbases': ['cms.HtmlDocumentVersion']},
            'beginning_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'due_time': ('django.db.models.fields.TimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'htmldocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocumentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'is_repeating': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'length': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '6', 'decimal_places': '2'}),
            'priority': ('django.db.models.fields.CharField', [], {'default': "'Low'", 'max_length': '10', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '16', 'null': 'True'}),
            'task_handler': ('django.db.models.ForeignKey', [], {'related_name': "'version_task_handler'", 'default': 'None', 'to': "orm['cms.Agent']", 'blank': 'True', 'null': 'True', 'db_index': 'False'})
        }
    }

    complete_apps = ['project']
