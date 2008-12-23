from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from cms.views import ItemViewer
from cms import permission_functions
import cms.models
import modules.symsys.models
from django.db.models import Q

class SymsysAffiliateViewer(ItemViewer):
    item_type = modules.symsys.models.SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def entry_show(self):
        template = loader.get_template('symsysaffiliate/show.html')
        visible_memberships = cms.models.ItemSetMembership.objects.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'itemset'), permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'item'))
        if ('do_everything', 'Item') in self.get_global_abilities_for_agent(self.cur_agent):
            recursive_filter = None
        else:
            visible_memberships = cms.models.ItemSetMembership.objects.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'itemset'), permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'item'))
            recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
        self.context['containing_itemsets'] = self.item.all_containing_itemsets(recursive_filter)
        self.context['contact_methods'] = self.item.contactmethods_as_agent.filter(trashed=False)
        if ('do_everything', 'Item') not in self.get_global_abilities_for_agent(self.cur_agent):
            self.context['contact_methods'] = self.context['contact_methods'].filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'agent'))
        return HttpResponse(template.render(self.context))

