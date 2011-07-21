from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.recursiveproject.models import RecursiveProject, RecursiveProjectDependency
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time


class RecursiveProjectViewer(CollectionViewer, HtmlDocumentViewer):
    accepted_item_type = RecursiveProject
    viewer_name = 'recursiveproject' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        dependencies = RecursiveProjectDependency.objects.all()
        self.context['is_dependent'] = dependencies.filter(dependent_RecursiveProject=self.item.pk)
        self.context['is_required'] = dependencies.filter(required_RecursiveProject=self.item.pk)
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
        template = loader.get_template('project/recursiveproject.html')
        return HttpResponse(template.render(self.context))


class RecursiveProjectDependencyViewer(ItemViewer):
    accepted_item_type = RecursiveProjectDependency
    viewer_name = 'recursiveprojectdependency' 


    def item_show_html(self):
        self.context['action_title'] = 'Show'

        self.context['item'] = self.item



        template = loader.get_template('project/recursiveproject_dependency.html')
        return HttpResponse(template.render(self.context))



