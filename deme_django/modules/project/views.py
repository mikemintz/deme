from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.project.models import Project
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time


class ProjectViewer(CollectionViewer):
    accepted_item_type = Project
    viewer_name = 'project' 


    def item_show_html(self):
        self.context['action_title'] = 'Show'

        self.context['project'] = self.item



        template = loader.get_template('project/show.html')
        return HttpResponse(template.render(self.context))
    

