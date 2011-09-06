# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('cms', '0005_move_imagedocument_create'),
    )

    def forwards(self, orm):
        pass


    def backwards(self, orm):
        pass


    models = {
        
    }

    complete_apps = ['imagedocument']
