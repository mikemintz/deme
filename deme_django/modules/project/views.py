from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.project.models import Project, Task,TaskDependency
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time


class ProjectViewer(CollectionViewer):
    accepted_item_type = Project
    viewer_name = 'project' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        template = loader.get_template('project/show.html')
        return HttpResponse(template.render(self.context))

class TaskViewer(HtmlDocumentViewer):
    accepted_item_type = Task
    viewer_name = 'task' 


    def item_show_html(self):
        self.context['action_title'] = 'Show'
        dependencies = TaskDependency.objects.all()
        
        self.context['is_dependent'] = dependencies.filter(dependent_task=self.item.pk)
        self.context['is_required'] = dependencies.filter(required_task=self.item.pk)      

        self.context['task'] = self.item



        template = loader.get_template('project/task.html')
        return HttpResponse(template.render(self.context))


class TaskDependencyViewer(ItemViewer):
    accepted_item_type = TaskDependency
    viewer_name = 'taskdependency' 


    def item_show_html(self):
        self.context['action_title'] = 'Show'

        self.context['item'] = self.item



        template = loader.get_template('project/task_dependency.html')
        return HttpResponse(template.render(self.context))


