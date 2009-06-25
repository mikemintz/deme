from django.template import Context, loader
from django.http import HttpResponse
from cms.views import ItemViewer, PersonViewer, DocumentViewer, TextDocumentViewer, HtmlDocumentViewer
from cms.models import *
from modules.symsys.models import *
from django.db.models import Q

class SymsysCareerViewer(ItemViewer):
    accepted_item_type = SymsysCareer
    viewer_name = 'symsyscareer'


class ThesisSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = ThesisSymsysCareer
    viewer_name = 'thesissymsyscareer'


class StudentSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = StudentSymsysCareer
    viewer_name = 'studentsymsyscareer'


class MinorSymsysCareerViewer(StudentSymsysCareerViewer):
    accepted_item_type = MinorSymsysCareer
    viewer_name = 'minorsymsyscareer'


class BachelorsSymsysCareerViewer(StudentSymsysCareerViewer):
    accepted_item_type = BachelorsSymsysCareer
    viewer_name = 'bachelorssymsyscareer'


class MastersSymsysCareerViewer(StudentSymsysCareerViewer, ThesisSymsysCareerViewer):
    accepted_item_type = MastersSymsysCareer
    viewer_name = 'masterssymsyscareer'


class HonorsSymsysCareerViewer(ThesisSymsysCareerViewer):
    accepted_item_type = HonorsSymsysCareer
    viewer_name = 'honorssymsyscareer'


class ResearcherSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = ResearcherSymsysCareer
    viewer_name = 'researchersymsyscareer'


class FacultySymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = FacultySymsysCareer
    viewer_name = 'facultysymsyscareer'


class ProgramStaffSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = ProgramStaffSymsysCareer
    viewer_name = 'programstaffsymsyscareer'


class SymsysAffiliateViewer(PersonViewer):
    accepted_item_type = SymsysAffiliate
    viewer_name = 'symsysaffiliate'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('symsysaffiliate/show.html')
        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        self.context['containing_collections'] = self.item.ancestor_collections(recursive_filter)
        self.context['contact_methods'] = self.permission_cache.filter_items('view ContactMethod.agent', self.item.contact_methods).filter(active=True)
        self.context['symsys_careers'] = self.permission_cache.filter_items('view SymsysCareer.symsys_affiliate', self.item.symsys_careers).filter(active=True)
        return HttpResponse(template.render(self.context))


class AdvertisementViewer(DocumentViewer):
    accepted_item_type = Advertisement
    viewer_name = 'advertisement'


class TextAdvertisementViewer(TextDocumentViewer, AdvertisementViewer):
    accepted_item_type = TextAdvertisement
    viewer_name = 'textadvertisement'


class HtmlAdvertisementViewer(HtmlDocumentViewer, AdvertisementViewer):
    accepted_item_type = HtmlAdvertisement
    viewer_name = 'htmladvertisement'
