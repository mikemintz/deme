from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from cms.views import ItemViewer, PersonViewer, DocumentViewer, TextDocumentViewer, HtmlDocumentViewer, GroupViewer, CollectionViewer
from cms.models import *
from modules.symsys.models import *
from django.db.models import Q
from django.core.urlresolvers import reverse
import re
import urllib


#class SymsysFacultyGroupViewer(SymsysGroupViewer):
 #   accepted_item_type = Collection
  #  viewer_name = 'symsysfacultygroup'


class SymsysGroupViewer(CollectionViewer):
    accepted_item_type = Group
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
        collection_members = self.item.all_contained_collection_members(recursive_filter).order_by("name")

        p = Paginator(collection_members, 10)

        try:
            page = int(self.request.GET.get('page','1'))
        except ValueError:
            page = 1

        try:
            entries = p.page(page)
        except (EmptyPage, InvalidPage):
            entries = p.page(p.num_pages)

        members = []

        for member in entries.object_list:
            if issubclass(member.actual_item_type(), SymsysAffiliate):
                member = member.downcast()
                member_details = {}
                member_details['item'] = member
                if member.photo:
                    if self.cur_agent_can('view SymsysAffiliate.photo', member) and self.cur_agent_can('view FileDocument.datafile', member.photo):
                        member_details['photo'] = member.photo
                careers = self.permission_cache.filter_items('view SymsysCareer.symsys_affiliate', member.symsys_careers).filter(active=True)
                for career in careers:
                    if not ('photo' in member_details.keys()) and career.original_photo:
                        if self.cur_agent_can('view SymsysCareer.original_photo', career) and self.cur_agent_can('view FileDocument.datafile', career.original_photo):
                            member_details['photo'] = career.original_photo
                    if issubclass(career.actual_item_type(), StudentSymsysCareer):
                        career = career.downcast()
                        member_details['class_year'] = career.class_year
                    if issubclass(career.actual_item_type(), BachelorsSymsysCareer):
                        career = career.downcast()
                        member_details['concentration'] = career.concentration

                    if issubclass(career.actual_item_type(), FacultySymsysCareer):
                        career = career.downcast()
                        member_details['is_staff'] = True
                        member_details['academic_title'] = career.academic_title 
                        member_details['publications'] = member.publications
                        member_details['interests'] = member.interests
                    if issubclass(career.actual_item_type(), ProgramStaffSymsysCareer):
                        career = career.downcast()
                        #member_details['is_staff'] = True
                        member_details['academic_title'] = career.admin_title 
                        
                
                members.append(member_details)

        page_ranges = p.page_range
        displayed_page_range = []
        for possible_page in page_ranges:
            if (possible_page < page + 10) and (possible_page > page-10):
                displayed_page_range.append(possible_page)

        self.context['members'] = members
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
                if self.permission_cache.agent_can('view EmailContactMethod.email', contact_method):
                    contact_method_fields.append(contact_method.email)
            if issubclass(contact_method.actual_item_type(), WebsiteContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view WebsiteContactMethod.url', contact_method):
                    link = ("""<a href="%s">%s</a>""" % (contact_method.url, contact_method.url))
                    contact_method_fields.append(mark_safe(link))
            if issubclass(contact_method.actual_item_type(), PhoneContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view PhoneContactMethod.phone', contact_method):
                    contact_method_fields.append(contact_method.phone)
            if issubclass(contact_method.actual_item_type(), FaxContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view FaxContactMethod.fax', contact_method):
                    contact_method_fields.append('(Fax) ' + contact_method.fax)
            if issubclass(contact_method.actual_item_type(), AIMContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view AIMContactMethod.screen_name', contact_method):
                    contact_method_fields.append('(AIM Screename) ' + contact_method.screen_name)
            if issubclass(contact_method.actual_item_type(), AddressContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view AddressContactMethod.street1', contact_method):
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



#A helper class for students to create resumes that others can't view
class SymsysResumeViewer(TextDocumentViewer):
    accepted_item_type = HtmlDocument
    viewer_name = 'symsysresume'

    def type_new_html(self, form=None):
        self.context['action_title'] = ''
        template = loader.get_template('symsysresume/new.html')

        #ensure the user is a symsysaffiliate and then get the right info
        if not issubclass(self.cur_agent.actual_item_type(), SymsysAffiliate):
            return self.render_error('Error', "You must be a SymsysAffiliate to post a resume")

        #check that this symsysaffiliate is a member of the Students group
        student_pk = Collection.objects.get(name="Students").pk
        containing_collections = self.cur_agent.ancestor_collections()
        is_student = False
        for collection in containing_collections:
            if collection.pk == student_pk:
                is_student = True
                break

        if not is_student:
            return self.render_error('Error', "You must be a current student to post a resume")
            

        symsys_aff = self.cur_agent.downcast()
        resume_name = ('%s %s Resume' % (symsys_aff.first_name, symsys_aff.last_name))
        #make sure this user hasn't already entered a resume
        resume = Document.objects.filter(name=resume_name)
        if resume:
            rpk = 0
            for r in resume:
                rpk = r.pk
                break

            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': 'htmldocument', 'noun': rpk}))
            return HttpResponseRedirect(redirect)

        self.context['resume_name'] = resume_name
        
        #you need to specify the collection of resumes to add this resume to
        add_coll = self.request.GET.get('add_to_collection')
        if not add_coll:
            return self.render_error('Error', "Bad link to the resume uploader")

        self.context['add_to_collection'] = add_coll 
        self.context['create_url'] = reverse('item_type_url', kwargs={'viewer':'symsysresume', 'action':'resumecreate'})


        return HttpResponse(template.render(self.context))


    def type_resumecreate_html(self):
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        
        #check and make sure everything is there
        resume = self.request.POST.get('resume')
        if resume == '':
            return self.render_error('Invalid Resume', "You must enter in your resume")
        resume_name = self.request.POST.get('resume_name')
        if resume_name == '':
            return self.render_error('Invalid Resume Name', "You must enter in a title for your resume")
        add_to_collection = self.request.POST.get('add_to_collection')
        if add_to_collection == '':
            return self.render_error('No add to collection field', "This shouldn't have happened")


        new_res = HtmlDocument(body=resume, name=resume_name)
        permissions = [AllToOnePermission(ability='do_anything', is_allowed=False), 
                OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
        new_res.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)

        new_membership = Membership(item=new_res, collection=Collection.objects.get(pk=add_to_collection), permission_enabled=True)
        membership_permissions = [AllToOnePermission(ability='do_anything', is_allowed=False)]
        new_membership.save_versioned(action_agent=self.cur_agent, initial_permissions=membership_permissions) 

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': 'htmldocument', 'noun': new_res.pk}))
        return HttpResponseRedirect(redirect)


#A helper class for faculty to create interships that others can't view
class SymsysInternshipViewer(HtmlDocumentViewer, AdvertisementViewer):
    accepted_item_type = HtmlAdvertisement
    viewer_name = 'symsysinternship'

    def type_new_html(self, form=None):
        self.context['action_title'] = ''
        template = loader.get_template('symsysinternship/new.html')

        #ensure the user is a symsysaffiliate or admin and then get the right info
        if not (issubclass(self.cur_agent.actual_item_type(), SymsysAffiliate) or self.cur_agent.pk == 1):
            return self.render_error('Error', "You must be a SymsysAffiliate to post an internship")

        #TODO: check that this symsysaffiliate is a member of the Faculty group
        faculty_pk = Collection.objects.get(name="Faculty").pk
        containing_collections = self.cur_agent.ancestor_collections()
        is_faculty = False
        for collection in containing_collections:
            if collection.pk == faculty_pk:
                is_faculty = True
                break

        #admin can do everything
        if self.cur_agent.pk == 1:
            is_faculty = True

        if not is_faculty:
            return self.render_error('Error', "You must be a current Symsys faculty member to post an internship")


        #you need to specify the collection of resumes to add this resume to
        add_coll = self.request.GET.get('add_to_collection')
        if not add_coll:
            return self.render_error('Error', "Bad link to the internship uploader")

        self.context['add_to_collection'] = add_coll 
        self.context['create_url'] = reverse('item_type_url', kwargs={'viewer':'symsysinternship', 'action':'internshipcreate'})


        return HttpResponse(template.render(self.context))


    def type_internshipcreate_html(self):
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        
        #check and make sure everything is there
        body = self.request.POST.get('body')
        if body == '':
            return self.render_error('Invalid Body', "You must enter in a description of the internship")
        contact_info = self.request.POST.get('contact_info')
        if contact_info == '':
            return self.render_error('Invalid Contact Info', "You must enter in contact information")
        ad_name = self.request.POST.get('ad_name')
        if ad_name == '':
            return self.render_error('Invalid Internship Name', "You must enter in a title for your internship")
        add_to_collection = self.request.POST.get('add_to_collection')
        if add_to_collection == '':
            return self.render_error('No add to collection field', "This shouldn't have happened")

        #expiration = self.request.POST.get('expiration', '')


        new_ad = HtmlAdvertisement(body=body, name=ad_name, contact_info=contact_info)
        permissions = [AllToOnePermission(ability='do_anything', is_allowed=False), 
                OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
        new_ad.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)

        new_membership = Membership(item=new_ad, collection=Collection.objects.get(pk=add_to_collection), permission_enabled=True)
        membership_permissions = [AllToOnePermission(ability='do_anything', is_allowed=False)]
        new_membership.save_versioned(action_agent=self.cur_agent, initial_permissions=membership_permissions) 

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': 'htmladvertisement', 'noun': new_ad.pk}))
        return HttpResponseRedirect(redirect)

#NEW MATERIAL 7/31
class SymsysCourseListViewer(TextDocumentViewer):
#To be used for core class listing, concentration listings, and any other course listings
    accepted_item_type = HtmlDocument
    viewer_name = 'symsyscourselist'

    def item_show_html(self):
        from functools import partial
        #Next lines taken from cms/views.py, class TextDocumentViewer, item_show_html
        self.context['action_title'] = ''
        self.context['in_textdocument_show'] = True
        self.context['highlighted_transclusion_id'] = self.request.GET.get('highlighted_transclusion')
        self.context['highlighted_comment_id'] = self.request.GET.get('highlighted_comment')
        self.require_ability('view ', self.item, wildcard_suffix=True)
        #Replace basic markup with clickable markup for each class listed
            #depts list is alphabetized!
        depts = ['ANTHRO', '(?<!N)(?<!HUM)BIO', 'BIOE', 'BIOMEDIN', 'CEE', 'CME', 'COMM', 'CS', 'ECON', 'EDUC', '(?<!C)EE', 'ENGR', 'ETHICSOC', 'GENE', 'HRP', 'HUMBIO', 'IHUM', 'IPS', 'LAW', 'LINGUIST', 'MATH', '(?<!C)ME', 'MED', 'MS&amp;E', 'MUSIC', 'NBIO', 'NENS', 'PHIL', 'POLISCI', 'PSYCH', 'PUBLPOL', 'SLE', '(?<!ETHIC)SOC', 'STATS', 'STS', 'SYMSYS', 'URBANST']
        regex = '(%s [0-9]+[A-Z]*\.[^</*]+)' 
        #index must be a list because integers are not mutable (see its use in replFunc for more info)
        index = [0]

        def replFunc(index, dept, matchobj):
            #index and temp used to create a unique id for the div that will hold course info for each course
            index[0] += 1
            temp = "a"+str(index[0])
            classEx = '(%s [0-9]+[A-Z]*)' % dept
            className = re.search(classEx, matchobj.group(0)).group(0) 
            #Click '+' or 'show/hide info'
            #return replace % (matchobj.group(1), className, temp, re.sub(' ', '', className), temp)
            #Click whole course name etc.
            return replace % (className, temp, matchobj.group(1), re.sub(' ', '', className), temp)

        #Highlight '+'   
        #replace = '%s <a href="#" title="Click to see course info including schedule and description." onclick="courseLink(\'%s\', \'%s\'); return false;"> + </a><div class="courselink %s" id="%s" style="display:none; border:5px solid; padding:5px;"></div>'
        #Highlight whole course name
        replace = '<a href="#" title="Click to see course info including schedule and description." onclick="courseLink(\'%s\', \'%s\'); return false;">%s</a><div class="courselink %s" id="%s" style="display:none; border:5px solid; padding:5px;"></div>'
        #Highlight 'show/hide info'
        #replace = '%s <a href="#" title="Click to see course info including schedule and description." style="font-weight:normal;" onclick="courseLink(\'%s\', \'%s\'); return false;"> show/hide info </a><div class="courselink %s" id="%s" style="display:none; border:5px solid; padding:5px; font-weight:normal;"></div>'
       
        new_body = self.item.body
        for dept in depts:
            pattern = regex % dept
            new_body = re.sub(pattern, partial(replFunc, index, dept), new_body)
        self.context['body'] = new_body
        template = loader.get_template('symsyscourselist/show.html')
        self.context['is_html'] = True
        return HttpResponse(template.render(self.context))

    def type_show_ajax(self):
        #Formulate url based on query, make ajax call, return xml doc
        query = self.request.GET['query']
        #Replace call below handles MS&E
        query = query.upper().replace(' ', '').replace('&', '%26')
        url = 'http://explorecourses.stanford.edu/CourseSearch/search?view=xml-20120105&q=%s'
        url = url % query
        #Make ajax call for url data
        opener = urllib.FancyURLopener({})
        f = opener.open(url)
        return HttpResponse(f)
        
