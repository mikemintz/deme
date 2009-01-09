from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from cms.views import ItemViewer
from cms import permissions
from cms.models import *
from modules.symsys.models import *
from django.db.models import Q

class SymsysAffiliateViewer(ItemViewer):
    item_type = SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def entry_show(self):
        template = loader.get_template('symsysaffiliate/show.html')
        visible_memberships = Membership.objects.filter(permissions.filter_items_by_permission(self.cur_agent, 'view collection'), permissions.filter_items_by_permission(self.cur_agent, 'view item'))
        if self.cur_agent_can_global('do_everything'):
            recursive_filter = None
        else:
            visible_memberships = Membership.objects.filter(permissions.filter_items_by_permission(self.cur_agent, 'view collection'), permissions.filter_items_by_permission(self.cur_agent, 'view item'))
            recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
        self.context['containing_collections'] = self.item.all_containing_collections(recursive_filter)
        self.context['contact_methods'] = self.item.contactmethods_as_agent.filter(trashed=False)
        if not self.cur_agent_can_global('do_everything'):
            self.context['contact_methods'] = self.context['contact_methods'].filter(permissions.filter_items_by_permission(self.cur_agent, 'view agent'))
        return HttpResponse(template.render(self.context))

