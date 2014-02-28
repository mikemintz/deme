# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Poll'
        db.create_table(u'poll_poll', (
            (u'collection_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.Collection'], unique=True, primary_key=True)),
            ('question', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('begins', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('deadline', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('time_zone', self.gf('django.db.models.fields.CharField')(default='America/Los_Angeles', max_length=255, null=True)),
            ('eligibles', self.gf('django.db.models.ForeignKey')(default=None, related_name='poll_participant', null=True, blank=True, to=orm['cms.Group'])),
            ('visibility', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=36, null=True)),
            ('allow_editing_responses', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['Poll'])

        # Adding model 'PollVersion'
        db.create_table(u'poll_pollversion', (
            (u'collectionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.CollectionVersion'], unique=True, primary_key=True)),
            ('question', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('begins', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('deadline', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('time_zone', self.gf('django.db.models.fields.CharField')(default='America/Los_Angeles', max_length=255, null=True)),
            ('eligibles', self.gf('django.db.models.ForeignKey')(related_name='version_poll_participant', default=None, to=orm['cms.Group'], blank=True, null=True, db_index=False)),
            ('visibility', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=36, null=True)),
            ('allow_editing_responses', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PollVersion'])

        # Adding model 'ChooseNPoll'
        db.create_table(u'poll_choosenpoll', (
            (u'poll_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Poll'], unique=True, primary_key=True)),
            ('n', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ChooseNPoll'])

        # Adding model 'ChooseNPollVersion'
        db.create_table(u'poll_choosenpollversion', (
            (u'pollversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.PollVersion'], unique=True, primary_key=True)),
            ('n', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ChooseNPollVersion'])

        # Adding model 'AgreeDisagreePoll'
        db.create_table(u'poll_agreedisagreepoll', (
            (u'poll_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Poll'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'poll', ['AgreeDisagreePoll'])

        # Adding model 'AgreeDisagreePollVersion'
        db.create_table(u'poll_agreedisagreepollversion', (
            (u'pollversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.PollVersion'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'poll', ['AgreeDisagreePollVersion'])

        # Adding model 'Proposition'
        db.create_table(u'poll_proposition', (
            (u'htmldocument_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocument'], unique=True, primary_key=True)),
            ('summary_text', self.gf('django.db.models.fields.CharField')(default='', max_length=140, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['Proposition'])

        # Adding model 'PropositionVersion'
        db.create_table(u'poll_propositionversion', (
            (u'htmldocumentversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.HtmlDocumentVersion'], unique=True, primary_key=True)),
            ('summary_text', self.gf('django.db.models.fields.CharField')(default='', max_length=140, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PropositionVersion'])

        # Adding model 'PropositionResponse'
        db.create_table(u'poll_propositionresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poll', self.gf('django.db.models.ForeignKey')(default=None, related_name='poll_response', null=True, blank=True, to=orm['poll.Poll'])),
            ('participant', self.gf('django.db.models.ForeignKey')(default=None, related_name='poll_participant', null=True, blank=True, to=orm['cms.Agent'])),
            ('proposition', self.gf('django.db.models.ForeignKey')(default=None, related_name='poll_proposition', null=True, blank=True, to=orm['poll.Proposition'])),
        ))
        db.send_create_signal(u'poll', ['PropositionResponse'])

        # Adding model 'PropositionResponseChoose'
        db.create_table(u'poll_propositionresponsechoose', (
            (u'propositionresponse_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.PropositionResponse'], unique=True, primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=36)),
        ))
        db.send_create_signal(u'poll', ['PropositionResponseChoose'])

        # Adding model 'PropositionResponseApprove'
        db.create_table(u'poll_propositionresponseapprove', (
            (u'propositionresponse_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.PropositionResponse'], unique=True, primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(default='Unassigned', max_length=36)),
        ))
        db.send_create_signal(u'poll', ['PropositionResponseApprove'])

        # Adding model 'Decision'
        db.create_table(u'poll_decision', (
            (u'item_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.Item'], unique=True, primary_key=True)),
            ('quorum', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('poll', self.gf('django.db.models.ForeignKey')(default=None, related_name='polls_decision', null=True, blank=True, to=orm['poll.Poll'])),
        ))
        db.send_create_signal(u'poll', ['Decision'])

        # Adding model 'DecisionVersion'
        db.create_table(u'poll_decisionversion', (
            (u'itemversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cms.ItemVersion'], unique=True, primary_key=True)),
            ('quorum', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('poll', self.gf('django.db.models.ForeignKey')(related_name='version_polls_decision', default=None, to=orm['poll.Poll'], blank=True, null=True, db_index=False)),
        ))
        db.send_create_signal(u'poll', ['DecisionVersion'])

        # Adding model 'PluralityChooseNDecision'
        db.create_table(u'poll_pluralitychoosendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PluralityChooseNDecision'])

        # Adding model 'PluralityChooseNDecisionVersion'
        db.create_table(u'poll_pluralitychoosendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PluralityChooseNDecisionVersion'])

        # Adding model 'ThresholdChooseNDecision'
        db.create_table(u'poll_thresholdchoosendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('p_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdChooseNDecision'])

        # Adding model 'ThresholdChooseNDecisionVersion'
        db.create_table(u'poll_thresholdchoosendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('p_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdChooseNDecisionVersion'])

        # Adding model 'ThresholdEChooseNDecision'
        db.create_table(u'poll_thresholdechoosendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('e_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdEChooseNDecision'])

        # Adding model 'ThresholdEChooseNDecisionVersion'
        db.create_table(u'poll_thresholdechoosendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('e_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdEChooseNDecisionVersion'])

        # Adding model 'UnanimousChooseNDecision'
        db.create_table(u'poll_unanimouschoosendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('m_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['UnanimousChooseNDecision'])

        # Adding model 'UnanimousChooseNDecisionVersion'
        db.create_table(u'poll_unanimouschoosendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('m_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['UnanimousChooseNDecisionVersion'])

        # Adding model 'PluralityApproveNDecision'
        db.create_table(u'poll_pluralityapprovendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PluralityApproveNDecision'])

        # Adding model 'PluralityApproveNDecisionVersion'
        db.create_table(u'poll_pluralityapprovendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['PluralityApproveNDecisionVersion'])

        # Adding model 'ThresholdApproveNDecision'
        db.create_table(u'poll_thresholdapprovendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('p_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdApproveNDecision'])

        # Adding model 'ThresholdApproveNDecisionVersion'
        db.create_table(u'poll_thresholdapprovendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('p_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdApproveNDecisionVersion'])

        # Adding model 'ThresholdEApproveNDecision'
        db.create_table(u'poll_thresholdeapprovendecision', (
            (u'decision_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.Decision'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('e_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdEApproveNDecision'])

        # Adding model 'ThresholdEApproveNDecisionVersion'
        db.create_table(u'poll_thresholdeapprovendecisionversion', (
            (u'decisionversion_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['poll.DecisionVersion'], unique=True, primary_key=True)),
            ('num_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('e_decision', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'poll', ['ThresholdEApproveNDecisionVersion'])


    def backwards(self, orm):
        # Deleting model 'Poll'
        db.delete_table(u'poll_poll')

        # Deleting model 'PollVersion'
        db.delete_table(u'poll_pollversion')

        # Deleting model 'ChooseNPoll'
        db.delete_table(u'poll_choosenpoll')

        # Deleting model 'ChooseNPollVersion'
        db.delete_table(u'poll_choosenpollversion')

        # Deleting model 'AgreeDisagreePoll'
        db.delete_table(u'poll_agreedisagreepoll')

        # Deleting model 'AgreeDisagreePollVersion'
        db.delete_table(u'poll_agreedisagreepollversion')

        # Deleting model 'Proposition'
        db.delete_table(u'poll_proposition')

        # Deleting model 'PropositionVersion'
        db.delete_table(u'poll_propositionversion')

        # Deleting model 'PropositionResponse'
        db.delete_table(u'poll_propositionresponse')

        # Deleting model 'PropositionResponseChoose'
        db.delete_table(u'poll_propositionresponsechoose')

        # Deleting model 'PropositionResponseApprove'
        db.delete_table(u'poll_propositionresponseapprove')

        # Deleting model 'Decision'
        db.delete_table(u'poll_decision')

        # Deleting model 'DecisionVersion'
        db.delete_table(u'poll_decisionversion')

        # Deleting model 'PluralityChooseNDecision'
        db.delete_table(u'poll_pluralitychoosendecision')

        # Deleting model 'PluralityChooseNDecisionVersion'
        db.delete_table(u'poll_pluralitychoosendecisionversion')

        # Deleting model 'ThresholdChooseNDecision'
        db.delete_table(u'poll_thresholdchoosendecision')

        # Deleting model 'ThresholdChooseNDecisionVersion'
        db.delete_table(u'poll_thresholdchoosendecisionversion')

        # Deleting model 'ThresholdEChooseNDecision'
        db.delete_table(u'poll_thresholdechoosendecision')

        # Deleting model 'ThresholdEChooseNDecisionVersion'
        db.delete_table(u'poll_thresholdechoosendecisionversion')

        # Deleting model 'UnanimousChooseNDecision'
        db.delete_table(u'poll_unanimouschoosendecision')

        # Deleting model 'UnanimousChooseNDecisionVersion'
        db.delete_table(u'poll_unanimouschoosendecisionversion')

        # Deleting model 'PluralityApproveNDecision'
        db.delete_table(u'poll_pluralityapprovendecision')

        # Deleting model 'PluralityApproveNDecisionVersion'
        db.delete_table(u'poll_pluralityapprovendecisionversion')

        # Deleting model 'ThresholdApproveNDecision'
        db.delete_table(u'poll_thresholdapprovendecision')

        # Deleting model 'ThresholdApproveNDecisionVersion'
        db.delete_table(u'poll_thresholdapprovendecisionversion')

        # Deleting model 'ThresholdEApproveNDecision'
        db.delete_table(u'poll_thresholdeapprovendecision')

        # Deleting model 'ThresholdEApproveNDecisionVersion'
        db.delete_table(u'poll_thresholdeapprovendecisionversion')


    models = {
        u'cms.agent': {
            'Meta': {'object_name': 'Agent', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'agents_with_photo'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"})
        },
        u'cms.collection': {
            'Meta': {'object_name': 'Collection', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.collectionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'CollectionVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.document': {
            'Meta': {'object_name': 'Document', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.documentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DocumentVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.filedocument': {
            'Meta': {'object_name': 'FileDocument', '_ormbases': [u'cms.Document']},
            'datafile': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.group': {
            'Meta': {'object_name': 'Group', '_ormbases': [u'cms.Collection']},
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'image': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'groups_with_image'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.ImageDocument']"})
        },
        u'cms.htmldocument': {
            'Meta': {'object_name': 'HtmlDocument', '_ormbases': [u'cms.TextDocument']},
            u'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.htmldocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'HtmlDocumentVersion', '_ormbases': [u'cms.TextDocumentVersion']},
            u'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        u'cms.textdocument': {
            'Meta': {'object_name': 'TextDocument', '_ormbases': [u'cms.Document']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'cms.textdocumentversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'TextDocumentVersion', '_ormbases': [u'cms.DocumentVersion']},
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'poll.agreedisagreepoll': {
            'Meta': {'object_name': 'AgreeDisagreePoll', '_ormbases': [u'poll.Poll']},
            u'poll_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Poll']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'poll.agreedisagreepollversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'AgreeDisagreePollVersion', '_ormbases': [u'poll.PollVersion']},
            u'pollversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.PollVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'poll.choosenpoll': {
            'Meta': {'object_name': 'ChooseNPoll', '_ormbases': [u'poll.Poll']},
            'n': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            u'poll_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Poll']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'poll.choosenpollversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ChooseNPollVersion', '_ormbases': [u'poll.PollVersion']},
            'n': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            u'pollversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.PollVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'poll.decision': {
            'Meta': {'object_name': 'Decision', '_ormbases': [u'cms.Item']},
            u'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'poll': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'polls_decision'", 'null': 'True', 'blank': 'True', 'to': u"orm['poll.Poll']"}),
            'quorum': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.decisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'DecisionVersion', '_ormbases': [u'cms.ItemVersion']},
            u'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'poll': ('django.db.models.ForeignKey', [], {'related_name': "'version_polls_decision'", 'default': 'None', 'to': u"orm['poll.Poll']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'quorum': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.pluralityapprovendecision': {
            'Meta': {'object_name': 'PluralityApproveNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.pluralityapprovendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PluralityApproveNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.pluralitychoosendecision': {
            'Meta': {'object_name': 'PluralityChooseNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.pluralitychoosendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PluralityChooseNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.poll': {
            'Meta': {'object_name': 'Poll', '_ormbases': [u'cms.Collection']},
            'allow_editing_responses': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'begins': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'collection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.Collection']", 'unique': 'True', 'primary_key': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'eligibles': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'poll_participant'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.Group']"}),
            'question': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'default': "'America/Los_Angeles'", 'max_length': '255', 'null': 'True'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '36', 'null': 'True'})
        },
        u'poll.pollversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PollVersion', '_ormbases': [u'cms.CollectionVersion']},
            'allow_editing_responses': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'begins': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'collectionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.CollectionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'eligibles': ('django.db.models.ForeignKey', [], {'related_name': "'version_poll_participant'", 'default': 'None', 'to': u"orm['cms.Group']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'question': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'default': "'America/Los_Angeles'", 'max_length': '255', 'null': 'True'}),
            'visibility': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '36', 'null': 'True'})
        },
        u'poll.proposition': {
            'Meta': {'object_name': 'Proposition', '_ormbases': [u'cms.HtmlDocument']},
            u'htmldocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.HtmlDocument']", 'unique': 'True', 'primary_key': 'True'}),
            'summary_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '140', 'null': 'True', 'blank': 'True'})
        },
        u'poll.propositionresponse': {
            'Meta': {'object_name': 'PropositionResponse'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'poll_participant'", 'null': 'True', 'blank': 'True', 'to': u"orm['cms.Agent']"}),
            'poll': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'poll_response'", 'null': 'True', 'blank': 'True', 'to': u"orm['poll.Poll']"}),
            'proposition': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'poll_proposition'", 'null': 'True', 'blank': 'True', 'to': u"orm['poll.Proposition']"})
        },
        u'poll.propositionresponseapprove': {
            'Meta': {'object_name': 'PropositionResponseApprove', '_ormbases': [u'poll.PropositionResponse']},
            u'propositionresponse_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.PropositionResponse']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '36'})
        },
        u'poll.propositionresponsechoose': {
            'Meta': {'object_name': 'PropositionResponseChoose', '_ormbases': [u'poll.PropositionResponse']},
            u'propositionresponse_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.PropositionResponse']", 'unique': 'True', 'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'default': "'Unassigned'", 'max_length': '36'})
        },
        u'poll.propositionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'PropositionVersion', '_ormbases': [u'cms.HtmlDocumentVersion']},
            u'htmldocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['cms.HtmlDocumentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'summary_text': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '140', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdapprovendecision': {
            'Meta': {'object_name': 'ThresholdApproveNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'p_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdapprovendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ThresholdApproveNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'p_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdchoosendecision': {
            'Meta': {'object_name': 'ThresholdChooseNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'p_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdchoosendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ThresholdChooseNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'p_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdeapprovendecision': {
            'Meta': {'object_name': 'ThresholdEApproveNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'e_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdeapprovendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ThresholdEApproveNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'e_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdechoosendecision': {
            'Meta': {'object_name': 'ThresholdEChooseNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'e_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.thresholdechoosendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'ThresholdEChooseNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'e_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.unanimouschoosendecision': {
            'Meta': {'object_name': 'UnanimousChooseNDecision', '_ormbases': [u'poll.Decision']},
            u'decision_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.Decision']", 'unique': 'True', 'primary_key': 'True'}),
            'm_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        },
        u'poll.unanimouschoosendecisionversion': {
            'Meta': {'ordering': "['version_number']", 'object_name': 'UnanimousChooseNDecisionVersion', '_ormbases': [u'poll.DecisionVersion']},
            u'decisionversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['poll.DecisionVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'm_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'num_decision': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['poll']