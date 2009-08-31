from django.template import Context, loader
from django.http import HttpResponse
from cms.views import ItemViewer, PersonViewer, DocumentViewer, TextDocumentViewer, HtmlDocumentViewer
from cms.models import *
from modules.symsys.models import *
from django.db.models import Q

class SymsysGroupViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'symsysgroup'

    def item_show_html(self):
        from django.core.paginator import Paginator, InvalidPage, EmptyPage
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('symsysgroup/show.html')

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        collection_members = self.item.all_contained_collection_members(recursive_filter)

        members = []
        for member in collection_members:
            if issubclass(member.actual_item_type(), SymsysAffiliate):
                member = member.downcast()
                member_details = {}
                member_details['item'] = member
                if member.photo:
                    member_details['photo'] = member.photo
                careers = self.permission_cache.filter_items('view SymsysCareer.symsys_affiliate', member.symsys_careers).filter(active=True)
                for career in careers:
                    if not ('photo' in member_details.keys()) and career.original_photo:
                        member_details['photo'] = career.original_photo
                    if issubclass(career.actual_item_type(), StudentSymsysCareer):
                        career = career.downcast()
                        member_details['class_year'] = career.class_year
                    if issubclass(career.actual_item_type(), BachelorsSymsysCareer):
                        career = career.downcast()
                        member_details['concentration'] = career.concentration
                
                members.append(member_details)

        p = Paginator(members, 10)

        try:
            page = int(self.request.GET.get('page','1'))
        except ValueError:
            page = 1

        try:
            entries = p.page(page)
        except (EmptyPage, InvalidPage):
            entries = p.page(p.num_pages)

        page_ranges = p.page_range
        displayed_page_range = []
        for possible_page in page_ranges:
            if (possible_page < page + 10) and (possible_page > page-10):
                displayed_page_range.append(possible_page)

        self.context['members'] = entries
        self.context['page_range'] = displayed_page_range
        return HttpResponse(template.render(self.context))

class SymsysCareerViewer(ItemViewer):
    accepted_item_type = SymsysCareer
    viewer_name = 'symsyscareer'

    def item_show_html(self):
        #from django.utils.safestring import mark_safe
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('symsyscareer/show.html')
        if issubclass(self.item.actual_item_type(), ProgramStaffSymsysCareer):
            self.item = self.item.downcast()
            self.context['admin_title'] = self.item.admin_title
        if issubclass(self.item.actual_item_type(), ResearcherSymsysCareer):
            self.item = self.item.downcast()
            self.context['researcher_academic_title'] = self.item.academic_title
        if issubclass(self.item.actual_item_type(), FacultySymsysCareer):
            self.item = self.item.downcast()
            self.context['faculty_academic_title'] = self.item.academic_title
        self.context['item'] = self.item
        return HttpResponse(template.render(self.context))


class ThesisSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = ThesisSymsysCareer
    viewer_name = 'thesissymsyscareer'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('thesissymsyscareer/show.html')

        if issubclass(self.item.actual_item_type(), HonorsSymsysCareer):
            self.item = self.item.downcast()
            self.context['advisor'] = self.item.advisor

        return HttpResponse(template.render(self.context))


class StudentSymsysCareerViewer(SymsysCareerViewer):
    accepted_item_type = StudentSymsysCareer
    viewer_name = 'studentsymsyscareer'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('studentsymsyscareer/show.html')

        if issubclass(self.item.actual_item_type(), BachelorsSymsysCareer):
            self.item = self.item.downcast()
            self.context['concentration'] = self.item.concentration
            self.context['indiv_designed_conc'] = self.item.indivdesignedconc

        if issubclass(self.item.actual_item_type(), MastersSymsysCareer):
            self.item = self.item.downcast()
            self.context['track'] = self.item.track
            self.context['indiv_designed_track'] = self.item.indivdesignedtrack 
            self.context['thesis'] = self.item.thesis
            self.context['thesis_title'] = self.item.thesis_title
            self.context['second_reader'] = self.item.second_reader

        return HttpResponse(template.render(self.context))

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
        from django.utils.safestring import mark_safe
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('symsysaffiliate/show.html')
        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        self.context['containing_collections'] = self.item.ancestor_collections(recursive_filter)
    
        contact_method_fields = []
        contact_methods = self.permission_cache.filter_items('view ContactMethod.agent', self.item.contact_methods).filter(active=True)
        for contact_method in contact_methods:
            if issubclass(contact_method.actual_item_type(), EmailContactMethod):
                contact_method = contact_method.downcast()
                contact_method_fields.append(contact_method.email)
            if issubclass(contact_method.actual_item_type(), WebsiteContactMethod):
                contact_method = contact_method.downcast()
                link = ("""<a href="%s">%s</a>""" % (contact_method.url, contact_method.url))
                contact_method_fields.append(mark_safe(link))
            if issubclass(contact_method.actual_item_type(), PhoneContactMethod):
                contact_method = contact_method.downcast()
                contact_method_fields.append(contact_method.phone)
            if issubclass(contact_method.actual_item_type(), FaxContactMethod):
                contact_method = contact_method.downcast()
                contact_method_fields.append('(Fax) ' + contact_method.fax)
            if issubclass(contact_method.actual_item_type(), AIMContactMethod):
                contact_method = contact_method.downcast()
                contact_method_fields.append('(AIM Screename) ' + contact_method.screen_name)
            if issubclass(contact_method.actual_item_type(), AddressContactMethod):
                contact_method = contact_method.downcast()
                if contact_method.street2:
                    address = (""" %s <br> %s <br>%s, %s %s  %s """ % (contact_method.street1, contact_method.street2, contact_method.city, contact_method.state, contact_method.country, contact_method.zip))
                else:
                    address = (""" %s <br>%s, %s %s  %s """ % (contact_method.street1, contact_method.city, contact_method.state, contact_method.country, contact_method.zip))
                contact_method_fields.append(mark_safe(address))

        self.context['contact_methods'] = contact_method_fields
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
