class SymsysAffiliateViewer(ItemViewer):
    item_type = cms.models.SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def entry_show(self):
        template = loader.get_template('symsysaffiliate/show.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        return HttpResponse(template.render(self.context))




