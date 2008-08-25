from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from cms.views import *
import cms.models
import modules.symsys.models

class SymsysAffiliateViewer(ItemViewer):
    item_type = modules.symsys.models.SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def collection_list(self):
        template = loader.get_template('symsysaffiliate/list.html')
        self.context['layout'] = 'base_symsys.html'
        return HttpResponse(template.render(self.context))

    def entry_show(self):
        template = loader.get_template('symsysaffiliate/show.html')
        self.context['layout'] = 'base_symsys.html'
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        return HttpResponse(template.render(self.context))


class SuperViewer(ItemViewer):
    item_type = cms.models.Account
    viewer_name = 'blarg'

    def collection_list(self):
        return HttpResponse('ka BLAM!')

