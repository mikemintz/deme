
from south.db import db
from django.db import models
from deme_django.modules.symsys.models import *

class Migration:
    
    depends_on = (
        ("imagedocument", "0001_initial"),
    )
    
    def forwards(self, orm):
        
        # Adding model 'HtmlAdvertisement'
        db.create_table('symsys_htmladvertisement', (
            ('advertisement_ptr', orm['symsys.HtmlAdvertisement:advertisement_ptr']),
            ('htmldocument_ptr', orm['symsys.HtmlAdvertisement:htmldocument_ptr']),
        ))
        db.send_create_signal('symsys', ['HtmlAdvertisement'])
        
        # Adding model 'StudentSymsysCareer'
        db.create_table('symsys_studentsymsyscareer', (
            ('symsyscareer_ptr', orm['symsys.StudentSymsysCareer:symsyscareer_ptr']),
            ('class_year', orm['symsys.StudentSymsysCareer:class_year']),
            ('advisor', orm['symsys.StudentSymsysCareer:advisor']),
            ('other_degrees', orm['symsys.StudentSymsysCareer:other_degrees']),
        ))
        db.send_create_signal('symsys', ['StudentSymsysCareer'])
        
        # Adding model 'ResearcherSymsysCareerVersion'
        db.create_table('symsys_researchersymsyscareerversion', (
            ('symsyscareerversion_ptr', orm['symsys.ResearcherSymsysCareerVersion:symsyscareerversion_ptr']),
            ('academic_title', orm['symsys.ResearcherSymsysCareerVersion:academic_title']),
        ))
        db.send_create_signal('symsys', ['ResearcherSymsysCareerVersion'])
        
        # Adding model 'BachelorsSymsysCareerVersion'
        db.create_table('symsys_bachelorssymsyscareerversion', (
            ('studentsymsyscareerversion_ptr', orm['symsys.BachelorsSymsysCareerVersion:studentsymsyscareerversion_ptr']),
            ('concentration', orm['symsys.BachelorsSymsysCareerVersion:concentration']),
            ('indivdesignedconc', orm['symsys.BachelorsSymsysCareerVersion:indivdesignedconc']),
        ))
        db.send_create_signal('symsys', ['BachelorsSymsysCareerVersion'])
        
        # Adding model 'MinorSymsysCareer'
        db.create_table('symsys_minorsymsyscareer', (
            ('studentsymsyscareer_ptr', orm['symsys.MinorSymsysCareer:studentsymsyscareer_ptr']),
        ))
        db.send_create_signal('symsys', ['MinorSymsysCareer'])
        
        # Adding model 'ThesisSymsysCareerVersion'
        db.create_table('symsys_thesissymsyscareerversion', (
            ('symsyscareerversion_ptr', orm['symsys.ThesisSymsysCareerVersion:symsyscareerversion_ptr']),
            ('second_reader', orm['symsys.ThesisSymsysCareerVersion:second_reader']),
            ('thesis', orm['symsys.ThesisSymsysCareerVersion:thesis']),
            ('thesis_title', orm['symsys.ThesisSymsysCareerVersion:thesis_title']),
        ))
        db.send_create_signal('symsys', ['ThesisSymsysCareerVersion'])
        
        # Adding model 'ProgramStaffSymsysCareer'
        db.create_table('symsys_programstaffsymsyscareer', (
            ('symsyscareer_ptr', orm['symsys.ProgramStaffSymsysCareer:symsyscareer_ptr']),
            ('admin_title', orm['symsys.ProgramStaffSymsysCareer:admin_title']),
        ))
        db.send_create_signal('symsys', ['ProgramStaffSymsysCareer'])
        
        # Adding model 'SymsysAffiliateVersion'
        db.create_table('symsys_symsysaffiliateversion', (
            ('personversion_ptr', orm['symsys.SymsysAffiliateVersion:personversion_ptr']),
            ('w_organization', orm['symsys.SymsysAffiliateVersion:w_organization']),
            ('w_position', orm['symsys.SymsysAffiliateVersion:w_position']),
            ('background', orm['symsys.SymsysAffiliateVersion:background']),
            ('doing_now', orm['symsys.SymsysAffiliateVersion:doing_now']),
            ('interests', orm['symsys.SymsysAffiliateVersion:interests']),
            ('publications', orm['symsys.SymsysAffiliateVersion:publications']),
            ('office_hours', orm['symsys.SymsysAffiliateVersion:office_hours']),
            ('about', orm['symsys.SymsysAffiliateVersion:about']),
            ('photo', orm['symsys.SymsysAffiliateVersion:photo']),
        ))
        db.send_create_signal('symsys', ['SymsysAffiliateVersion'])
        
        # Adding model 'SymsysCareerVersion'
        db.create_table('symsys_symsyscareerversion', (
            ('itemversion_ptr', orm['symsys.SymsysCareerVersion:itemversion_ptr']),
            ('suid', orm['symsys.SymsysCareerVersion:suid']),
            ('original_first_name', orm['symsys.SymsysCareerVersion:original_first_name']),
            ('original_middle_names', orm['symsys.SymsysCareerVersion:original_middle_names']),
            ('original_last_name', orm['symsys.SymsysCareerVersion:original_last_name']),
            ('original_suffix', orm['symsys.SymsysCareerVersion:original_suffix']),
            ('original_photo', orm['symsys.SymsysCareerVersion:original_photo']),
            ('finished', orm['symsys.SymsysCareerVersion:finished']),
            ('start_date', orm['symsys.SymsysCareerVersion:start_date']),
            ('end_date', orm['symsys.SymsysCareerVersion:end_date']),
        ))
        db.send_create_signal('symsys', ['SymsysCareerVersion'])
        
        # Adding model 'ResearcherSymsysCareer'
        db.create_table('symsys_researchersymsyscareer', (
            ('symsyscareer_ptr', orm['symsys.ResearcherSymsysCareer:symsyscareer_ptr']),
            ('academic_title', orm['symsys.ResearcherSymsysCareer:academic_title']),
        ))
        db.send_create_signal('symsys', ['ResearcherSymsysCareer'])
        
        # Adding model 'ProgramStaffSymsysCareerVersion'
        db.create_table('symsys_programstaffsymsyscareerversion', (
            ('symsyscareerversion_ptr', orm['symsys.ProgramStaffSymsysCareerVersion:symsyscareerversion_ptr']),
        ))
        db.send_create_signal('symsys', ['ProgramStaffSymsysCareerVersion'])
        
        # Adding model 'MastersSymsysCareerVersion'
        db.create_table('symsys_masterssymsyscareerversion', (
            ('thesissymsyscareerversion_ptr', orm['symsys.MastersSymsysCareerVersion:thesissymsyscareerversion_ptr']),
            ('studentsymsyscareerversion_ptr', orm['symsys.MastersSymsysCareerVersion:studentsymsyscareerversion_ptr']),
            ('track', orm['symsys.MastersSymsysCareerVersion:track']),
            ('indivdesignedtrack', orm['symsys.MastersSymsysCareerVersion:indivdesignedtrack']),
        ))
        db.send_create_signal('symsys', ['MastersSymsysCareerVersion'])
        
        # Adding model 'MinorSymsysCareerVersion'
        db.create_table('symsys_minorsymsyscareerversion', (
            ('studentsymsyscareerversion_ptr', orm['symsys.MinorSymsysCareerVersion:studentsymsyscareerversion_ptr']),
        ))
        db.send_create_signal('symsys', ['MinorSymsysCareerVersion'])
        
        # Adding model 'TextAdvertisementVersion'
        db.create_table('symsys_textadvertisementversion', (
            ('advertisementversion_ptr', orm['symsys.TextAdvertisementVersion:advertisementversion_ptr']),
            ('textdocumentversion_ptr', orm['symsys.TextAdvertisementVersion:textdocumentversion_ptr']),
        ))
        db.send_create_signal('symsys', ['TextAdvertisementVersion'])
        
        # Adding model 'FacultySymsysCareerVersion'
        db.create_table('symsys_facultysymsyscareerversion', (
            ('symsyscareerversion_ptr', orm['symsys.FacultySymsysCareerVersion:symsyscareerversion_ptr']),
            ('academic_title', orm['symsys.FacultySymsysCareerVersion:academic_title']),
        ))
        db.send_create_signal('symsys', ['FacultySymsysCareerVersion'])
        
        # Adding model 'HonorsSymsysCareer'
        db.create_table('symsys_honorssymsyscareer', (
            ('thesissymsyscareer_ptr', orm['symsys.HonorsSymsysCareer:thesissymsyscareer_ptr']),
            ('advisor', orm['symsys.HonorsSymsysCareer:advisor']),
        ))
        db.send_create_signal('symsys', ['HonorsSymsysCareer'])
        
        # Adding model 'HtmlAdvertisementVersion'
        db.create_table('symsys_htmladvertisementversion', (
            ('advertisementversion_ptr', orm['symsys.HtmlAdvertisementVersion:advertisementversion_ptr']),
            ('htmldocumentversion_ptr', orm['symsys.HtmlAdvertisementVersion:htmldocumentversion_ptr']),
        ))
        db.send_create_signal('symsys', ['HtmlAdvertisementVersion'])
        
        # Adding model 'Advertisement'
        db.create_table('symsys_advertisement', (
            ('document_ptr', orm['symsys.Advertisement:document_ptr']),
            ('contact_info', orm['symsys.Advertisement:contact_info']),
            ('expires_at', orm['symsys.Advertisement:expires_at']),
        ))
        db.send_create_signal('symsys', ['Advertisement'])
        
        # Adding model 'StudentSymsysCareerVersion'
        db.create_table('symsys_studentsymsyscareerversion', (
            ('symsyscareerversion_ptr', orm['symsys.StudentSymsysCareerVersion:symsyscareerversion_ptr']),
            ('class_year', orm['symsys.StudentSymsysCareerVersion:class_year']),
            ('advisor', orm['symsys.StudentSymsysCareerVersion:advisor']),
            ('other_degrees', orm['symsys.StudentSymsysCareerVersion:other_degrees']),
        ))
        db.send_create_signal('symsys', ['StudentSymsysCareerVersion'])
        
        # Adding model 'AdvertisementVersion'
        db.create_table('symsys_advertisementversion', (
            ('documentversion_ptr', orm['symsys.AdvertisementVersion:documentversion_ptr']),
            ('contact_info', orm['symsys.AdvertisementVersion:contact_info']),
            ('expires_at', orm['symsys.AdvertisementVersion:expires_at']),
        ))
        db.send_create_signal('symsys', ['AdvertisementVersion'])
        
        # Adding model 'FacultySymsysCareer'
        db.create_table('symsys_facultysymsyscareer', (
            ('symsyscareer_ptr', orm['symsys.FacultySymsysCareer:symsyscareer_ptr']),
            ('academic_title', orm['symsys.FacultySymsysCareer:academic_title']),
        ))
        db.send_create_signal('symsys', ['FacultySymsysCareer'])
        
        # Adding model 'MastersSymsysCareer'
        db.create_table('symsys_masterssymsyscareer', (
            ('thesissymsyscareer_ptr', orm['symsys.MastersSymsysCareer:thesissymsyscareer_ptr']),
            ('studentsymsyscareer_ptr', orm['symsys.MastersSymsysCareer:studentsymsyscareer_ptr']),
            ('track', orm['symsys.MastersSymsysCareer:track']),
            ('indivdesignedtrack', orm['symsys.MastersSymsysCareer:indivdesignedtrack']),
        ))
        db.send_create_signal('symsys', ['MastersSymsysCareer'])
        
        # Adding model 'BachelorsSymsysCareer'
        db.create_table('symsys_bachelorssymsyscareer', (
            ('studentsymsyscareer_ptr', orm['symsys.BachelorsSymsysCareer:studentsymsyscareer_ptr']),
            ('concentration', orm['symsys.BachelorsSymsysCareer:concentration']),
            ('indivdesignedconc', orm['symsys.BachelorsSymsysCareer:indivdesignedconc']),
        ))
        db.send_create_signal('symsys', ['BachelorsSymsysCareer'])
        
        # Adding model 'ThesisSymsysCareer'
        db.create_table('symsys_thesissymsyscareer', (
            ('symsyscareer_ptr', orm['symsys.ThesisSymsysCareer:symsyscareer_ptr']),
            ('second_reader', orm['symsys.ThesisSymsysCareer:second_reader']),
            ('thesis', orm['symsys.ThesisSymsysCareer:thesis']),
            ('thesis_title', orm['symsys.ThesisSymsysCareer:thesis_title']),
        ))
        db.send_create_signal('symsys', ['ThesisSymsysCareer'])
        
        # Adding model 'SymsysCareer'
        db.create_table('symsys_symsyscareer', (
            ('item_ptr', orm['symsys.SymsysCareer:item_ptr']),
            ('symsys_affiliate', orm['symsys.SymsysCareer:symsys_affiliate']),
            ('suid', orm['symsys.SymsysCareer:suid']),
            ('original_first_name', orm['symsys.SymsysCareer:original_first_name']),
            ('original_middle_names', orm['symsys.SymsysCareer:original_middle_names']),
            ('original_last_name', orm['symsys.SymsysCareer:original_last_name']),
            ('original_suffix', orm['symsys.SymsysCareer:original_suffix']),
            ('original_photo', orm['symsys.SymsysCareer:original_photo']),
            ('finished', orm['symsys.SymsysCareer:finished']),
            ('start_date', orm['symsys.SymsysCareer:start_date']),
            ('end_date', orm['symsys.SymsysCareer:end_date']),
        ))
        db.send_create_signal('symsys', ['SymsysCareer'])
        
        # Adding model 'HonorsSymsysCareerVersion'
        db.create_table('symsys_honorssymsyscareerversion', (
            ('thesissymsyscareerversion_ptr', orm['symsys.HonorsSymsysCareerVersion:thesissymsyscareerversion_ptr']),
            ('advisor', orm['symsys.HonorsSymsysCareerVersion:advisor']),
        ))
        db.send_create_signal('symsys', ['HonorsSymsysCareerVersion'])
        
        # Adding model 'TextAdvertisement'
        db.create_table('symsys_textadvertisement', (
            ('advertisement_ptr', orm['symsys.TextAdvertisement:advertisement_ptr']),
            ('textdocument_ptr', orm['symsys.TextAdvertisement:textdocument_ptr']),
        ))
        db.send_create_signal('symsys', ['TextAdvertisement'])
        
        # Adding model 'SymsysAffiliate'
        db.create_table('symsys_symsysaffiliate', (
            ('person_ptr', orm['symsys.SymsysAffiliate:person_ptr']),
            ('w_organization', orm['symsys.SymsysAffiliate:w_organization']),
            ('w_position', orm['symsys.SymsysAffiliate:w_position']),
            ('background', orm['symsys.SymsysAffiliate:background']),
            ('doing_now', orm['symsys.SymsysAffiliate:doing_now']),
            ('interests', orm['symsys.SymsysAffiliate:interests']),
            ('publications', orm['symsys.SymsysAffiliate:publications']),
            ('office_hours', orm['symsys.SymsysAffiliate:office_hours']),
            ('about', orm['symsys.SymsysAffiliate:about']),
            ('photo', orm['symsys.SymsysAffiliate:photo']),
        ))
        db.send_create_signal('symsys', ['SymsysAffiliate'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'HtmlAdvertisement'
        db.delete_table('symsys_htmladvertisement')
        
        # Deleting model 'StudentSymsysCareer'
        db.delete_table('symsys_studentsymsyscareer')
        
        # Deleting model 'ResearcherSymsysCareerVersion'
        db.delete_table('symsys_researchersymsyscareerversion')
        
        # Deleting model 'BachelorsSymsysCareerVersion'
        db.delete_table('symsys_bachelorssymsyscareerversion')
        
        # Deleting model 'MinorSymsysCareer'
        db.delete_table('symsys_minorsymsyscareer')
        
        # Deleting model 'ThesisSymsysCareerVersion'
        db.delete_table('symsys_thesissymsyscareerversion')
        
        # Deleting model 'ProgramStaffSymsysCareer'
        db.delete_table('symsys_programstaffsymsyscareer')
        
        # Deleting model 'SymsysAffiliateVersion'
        db.delete_table('symsys_symsysaffiliateversion')
        
        # Deleting model 'SymsysCareerVersion'
        db.delete_table('symsys_symsyscareerversion')
        
        # Deleting model 'ResearcherSymsysCareer'
        db.delete_table('symsys_researchersymsyscareer')
        
        # Deleting model 'ProgramStaffSymsysCareerVersion'
        db.delete_table('symsys_programstaffsymsyscareerversion')
        
        # Deleting model 'MastersSymsysCareerVersion'
        db.delete_table('symsys_masterssymsyscareerversion')
        
        # Deleting model 'MinorSymsysCareerVersion'
        db.delete_table('symsys_minorsymsyscareerversion')
        
        # Deleting model 'TextAdvertisementVersion'
        db.delete_table('symsys_textadvertisementversion')
        
        # Deleting model 'FacultySymsysCareerVersion'
        db.delete_table('symsys_facultysymsyscareerversion')
        
        # Deleting model 'HonorsSymsysCareer'
        db.delete_table('symsys_honorssymsyscareer')
        
        # Deleting model 'HtmlAdvertisementVersion'
        db.delete_table('symsys_htmladvertisementversion')
        
        # Deleting model 'Advertisement'
        db.delete_table('symsys_advertisement')
        
        # Deleting model 'StudentSymsysCareerVersion'
        db.delete_table('symsys_studentsymsyscareerversion')
        
        # Deleting model 'AdvertisementVersion'
        db.delete_table('symsys_advertisementversion')
        
        # Deleting model 'FacultySymsysCareer'
        db.delete_table('symsys_facultysymsyscareer')
        
        # Deleting model 'MastersSymsysCareer'
        db.delete_table('symsys_masterssymsyscareer')
        
        # Deleting model 'BachelorsSymsysCareer'
        db.delete_table('symsys_bachelorssymsyscareer')
        
        # Deleting model 'ThesisSymsysCareer'
        db.delete_table('symsys_thesissymsyscareer')
        
        # Deleting model 'SymsysCareer'
        db.delete_table('symsys_symsyscareer')
        
        # Deleting model 'HonorsSymsysCareerVersion'
        db.delete_table('symsys_honorssymsyscareerversion')
        
        # Deleting model 'TextAdvertisement'
        db.delete_table('symsys_textadvertisement')
        
        # Deleting model 'SymsysAffiliate'
        db.delete_table('symsys_symsysaffiliate')
        
    
    
    models = {
        'cms.agent': {
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'last_online_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'cms.agentversion': {
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'})
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
        'cms.person': {
            'agent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Agent']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.personversion': {
            'agentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.AgentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'cms.textdocument': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'})
        },
        'cms.textdocumentversion': {
            'body': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'imagedocument.imagedocument': {
            'filedocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.FileDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.advertisement': {
            'contact_info': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Document']", 'unique': 'True', 'primary_key': 'True'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'symsys.advertisementversion': {
            'contact_info': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'documentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.DocumentVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'symsys.bachelorssymsyscareer': {
            'concentration': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'indivdesignedconc': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'studentsymsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.bachelorssymsyscareerversion': {
            'concentration': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'indivdesignedconc': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'studentsymsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.facultysymsyscareer': {
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'symsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.facultysymsyscareerversion': {
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'symsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.honorssymsyscareer': {
            'advisor': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'honors_advisor_group'", 'null': 'True', 'blank': 'True', 'to': "orm['symsys.SymsysAffiliate']"}),
            'thesissymsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.ThesisSymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.honorssymsyscareerversion': {
            'advisor': ('django.db.models.ForeignKey', [], {'related_name': "'version_honors_advisor_group'", 'default': 'None', 'to': "orm['symsys.SymsysAffiliate']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'thesissymsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.ThesisSymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.htmladvertisement': {
            'advertisement_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.Advertisement']", 'unique': 'True'}),
            'htmldocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.htmladvertisementversion': {
            'advertisementversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.AdvertisementVersion']", 'unique': 'True'}),
            'htmldocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.HtmlDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.masterssymsyscareer': {
            'indivdesignedtrack': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'studentsymsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareer']", 'unique': 'True', 'primary_key': 'True'}),
            'thesissymsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.ThesisSymsysCareer']", 'unique': 'True'}),
            'track': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'symsys.masterssymsyscareerversion': {
            'indivdesignedtrack': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'studentsymsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'thesissymsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.ThesisSymsysCareerVersion']", 'unique': 'True'}),
            'track': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'symsys.minorsymsyscareer': {
            'studentsymsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.minorsymsyscareerversion': {
            'studentsymsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.StudentSymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.programstaffsymsyscareer': {
            'admin_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'symsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.programstaffsymsyscareerversion': {
            'symsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.researchersymsyscareer': {
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'symsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.researchersymsyscareerversion': {
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'symsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.studentsymsyscareer': {
            'advisor': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'advisor_group'", 'null': 'True', 'blank': 'True', 'to': "orm['symsys.SymsysAffiliate']"}),
            'class_year': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'other_degrees': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'symsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareer']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.studentsymsyscareerversion': {
            'advisor': ('django.db.models.ForeignKey', [], {'related_name': "'version_advisor_group'", 'default': 'None', 'to': "orm['symsys.SymsysAffiliate']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'class_year': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'other_degrees': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'symsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.symsysaffiliate': {
            'about': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'background': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'doing_now': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'interests': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'office_hours': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'symsysaffiliates_with_photo'", 'null': 'True', 'blank': 'True', 'to': "orm['imagedocument.ImageDocument']"}),
            'publications': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'w_organization': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'w_position': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'symsys.symsysaffiliateversion': {
            'about': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'background': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'doing_now': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'interests': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'office_hours': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'personversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.PersonVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'photo': ('django.db.models.ForeignKey', [], {'related_name': "'version_symsysaffiliates_with_photo'", 'default': 'None', 'to': "orm['imagedocument.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'publications': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'w_organization': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'w_position': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'symsys.symsyscareer': {
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'item_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.Item']", 'unique': 'True', 'primary_key': 'True'}),
            'original_first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'original_last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'original_middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'original_photo': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'symsyscareers_with_original_photo'", 'null': 'True', 'blank': 'True', 'to': "orm['imagedocument.ImageDocument']"}),
            'original_suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'suid': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'}),
            'symsys_affiliate': ('django.db.models.ForeignKey', [], {'default': "''", 'related_name': "'symsys_careers'", 'null': 'True', 'to': "orm['symsys.SymsysAffiliate']"})
        },
        'symsys.symsyscareerversion': {
            'end_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True'}),
            'itemversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.ItemVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'original_first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'original_last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True'}),
            'original_middle_names': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'original_photo': ('django.db.models.ForeignKey', [], {'related_name': "'version_symsyscareers_with_original_photo'", 'default': 'None', 'to': "orm['imagedocument.ImageDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'original_suffix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'default': "''", 'null': 'True'}),
            'suid': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True'})
        },
        'symsys.textadvertisement': {
            'advertisement_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.Advertisement']", 'unique': 'True'}),
            'textdocument_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocument']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.textadvertisementversion': {
            'advertisementversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.AdvertisementVersion']", 'unique': 'True'}),
            'textdocumentversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cms.TextDocumentVersion']", 'unique': 'True', 'primary_key': 'True'})
        },
        'symsys.thesissymsyscareer': {
            'second_reader': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'second_reader_group'", 'null': 'True', 'blank': 'True', 'to': "orm['symsys.SymsysAffiliate']"}),
            'symsyscareer_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareer']", 'unique': 'True', 'primary_key': 'True'}),
            'thesis': ('django.db.models.ForeignKey', [], {'default': 'None', 'related_name': "'careers_with_thesis'", 'null': 'True', 'blank': 'True', 'to': "orm['cms.FileDocument']"}),
            'thesis_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'symsys.thesissymsyscareerversion': {
            'second_reader': ('django.db.models.ForeignKey', [], {'related_name': "'version_second_reader_group'", 'default': 'None', 'to': "orm['symsys.SymsysAffiliate']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'symsyscareerversion_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['symsys.SymsysCareerVersion']", 'unique': 'True', 'primary_key': 'True'}),
            'thesis': ('django.db.models.ForeignKey', [], {'related_name': "'version_careers_with_thesis'", 'default': 'None', 'to': "orm['cms.FileDocument']", 'blank': 'True', 'null': 'True', 'db_index': 'False'}),
            'thesis_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['symsys']
