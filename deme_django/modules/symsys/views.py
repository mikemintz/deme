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
        template = loader.get_template('symsysaffiliate/show.html')
        return HttpResponse(template.render(self.context))


class SuperViewer(ItemViewer):
    item_type = cms.models.Account
    viewer_name = 'blarg'

    def collection_list(self):
        return HttpResponse('ka BLAM!')

