class SymsysAffiliateViewer(ItemViewer):
    item_type = cms.models.SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def entry_show(self):
        return HttpResponse('this is a symsys affiliate!')



