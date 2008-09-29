from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from cms.views import ItemViewer
from cms import permission_functions
import cms.models
import modules.symsys.models

class SymsysAffiliateViewer(ItemViewer):
    item_type = modules.symsys.models.SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def entry_show(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_view = ('view', 'id') in abilities_for_item
        if not (can_do_everything or can_view):
            return HttpResponseBadRequest("you do not have permission to view this item")
        template = loader.get_template('symsysaffiliate/show.html')
        self.context['item'] = self.item
        return HttpResponse(template.render(self.context))


class SuperViewer(ItemViewer):
    item_type = cms.models.Account
    viewer_name = 'blarg'

    def collection_list(self):
        return HttpResponse('ka BLAM!')

