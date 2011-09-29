from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.project.models import Project, ProjectDependency
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time


class ProjectViewer(CollectionViewer, HtmlDocumentViewer):
    accepted_item_type = Project
    viewer_name = 'project' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        dependencies = ProjectDependency.objects.all()
        self.context['is_dependent'] = dependencies.filter(dependent_Project=self.item.pk)
        self.context['is_required'] = dependencies.filter(required_Project=self.item.pk)
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        self.context['child_projects'] = Project.objects.filter(memberships__in=memberships)
        template = loader.get_template('project/project.html')
        return HttpResponse(template.render(self.context))

    def change_status_to_assigned(self):
        self.require_ability('edit Project.status', self.item)
        self.Project.status = 'Not Completed'

    def item_setstatustocompleted_html(self):
        try:
            member = Project.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error('Invalid URL', "You must specify the member you are adding")
        self.require_ability('edit Project.status', self.item)
        member.status = 'Completed'
        member.save_versioned(action_agent=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

class ProjectDependencyViewer(ItemViewer):
    accepted_item_type = ProjectDependency
    viewer_name = 'projectdependency' 


    def item_show_html(self):
        self.context['action_title'] = 'Show'

        self.context['item'] = self.item



        template = loader.get_template('project/project_dependency.html')
        return HttpResponse(template.render(self.context))



