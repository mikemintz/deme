from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from cms.views import ItemViewer
from cms import permissions
from cms.models import *
from modules.symsys.models import *
from django.db.models import Q

class SymsysAffiliateViewer(ItemViewer):
    accepted_item_type = SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def item_show(self):
        template = loader.get_template('symsysaffiliate/show.html')
        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items(self.cur_agent, 'view item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        self.context['containing_collections'] = self.item.ancestor_collections(recursive_filter)
        self.context['contact_methods'] = self.permission_cache.filter_items(self.cur_agent, 'view agent', self.item.contact_methods).filter(active=True)
        return HttpResponse(template.render(self.context))

