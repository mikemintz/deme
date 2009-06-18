from cms.models import *
from modules.imagedocument.models import *
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

__all__ = ['SymsysCareer', 'ThesisSymsysCareer', 'StudentSymsysCareer',
        'MinorSymsysCareer', 'BachelorsSymsysCareer', 'MastersSymsysCareer',
        'HonorsSymsysCareer', 'ResearcherSymsysCareer', 'FacultySymsysCareer',
        'ProgramStaffSymsysCareer', 'SymsysAffiliate', 'Event',
        'Advertisement', 'TextAdvertisement', 'HtmlAdvertisement']

BS_CONCENTRATIONS = [
    'Applied Logic',
    'Artificial Intelligence',
    'Cognition',
    'Cognitive Science',
    'Computation',
    'Computer Music',
    'Decision Making and Rationality',
    'Education and Learning',
    'HCI',
    'Individually Designed Concentration',
    'Learning',
    'Natural Language',
    'Neural Systems',
    'Neurosciences',
    'Philosophical Foundations',
    'Rationality',
    'Undecided',
]

MS_TRACKS = [
    'HCI',
    'Individually Designed Track',
    'Natural Language Technology',
]

FACULTY_ACADEMIC_TITLES = [
    "Assistant Professor",
    "Associate Professor",
    "Consulting Assistant Professor",
    "Consulting Associate Professor",
    "Consulting Professor",
    "Engineering Research Associate",
    "Executive Director",
    "Lecturer",
    "Professor",
    "Professor Emeritus",
    "Senior Lecturer",
    "Senior Research Engineer",
    "Student Services Officer",
    "University Affiliate",
    "Wasow Visiting Lecturer",
]

ADMIN_TITLES = [
    "Advising Fellow",
    "Associate Director",
    "Director Emeritus",
    "Graduate Studies Director",
    "Program Director",
    "Student Services Officer",
    "Webmaster",
]

def get_or_create_group(key, name, group_creator):
    deme_setting_key = 'symsys.groups.%s' % key
    group_pk = DemeSetting.get(deme_setting_key)
    if group_pk:
        group = Group.objects.get(pk=group_pk)
    else:
        group = Group(name=name)
        group.save_versioned(action_agent=group_creator)
        DemeSetting.set(deme_setting_key, group.pk, group_creator)
    return group


def symsys_bot():
    try:
        return Agent.objects.get(pk=DemeSetting.get("symsys.symsys_bot"))
    except ObjectDoesNotExist:
        raise Exception("Symsys module not properly installed (there is no symsys_bot)")

class SymsysCareer(Item):
    # Setup
    introduced_immutable_fields = frozenset(['symsys_affiliate'])
    introduced_abilities = frozenset(['view SymsysCareer.symsys_affiliate', 'view SymsysCareer.suid',
                                      'view SymsysCareer.original_first_name', 'view SymsysCareer.original_middle_names',
                                      'view SymsysCareer.original_last_name', 'view SymsysCareer.original_suffix',
                                      'view SymsysCareer.original_photo', 'view SymsysCareer.start_date',
                                      'view SymsysCareer.end_date', 'view SymsysCareer.finished', 'edit SymsysCareer.suid',
                                      'edit SymsysCareer.original_first_name', 'edit SymsysCareer.original_middle_names',
                                      'edit SymsysCareer.original_last_name', 'edit SymsysCareer.original_suffix',
                                      'edit SymsysCareer.original_photo', 'edit SymsysCareer.start_date',
                                      'edit SymsysCareer.end_date', 'edit SymsysCareer.finished'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('Symsys career')
        verbose_name_plural = _('Symsys careers')

    # Fields
    symsys_affiliate      = FixedForeignKey('SymsysAffiliate', verbose_name=_('Symsys affiliate'), related_name='symsys_careers')
    suid                  = models.PositiveIntegerField(_('SUID'), default=0)
    original_first_name   = models.CharField(_('original first name'), max_length=255)
    original_middle_names = models.CharField(_('original middle names'), max_length=255, blank=True)
    original_last_name    = models.CharField(_('original last name'), max_length=255)
    original_suffix       = models.CharField(_('original suffix'), max_length=255, blank=True)
    original_photo        = FixedForeignKey(ImageDocument, related_name='symsyscareers_with_original_photo', verbose_name=_('original photo'), null=True, blank=True, default=None)
    finished              = FixedBooleanField(_('finished'), default=False)
    start_date            = models.DateField(_('start date'))
    end_date              = models.DateField(_('end date'), blank=True, null=True, default=None)

    def _after_create(self, action_agent, action_summary, action_time):
        super(SymsysCareer, self)._after_create(action_agent, action_summary, action_time)
        self._guarantee_consistency_after_changes()

    def _after_edit(self, action_agent, action_summary, action_time):
        super(SymsysCareer, self)._after_edit(action_agent, action_summary, action_time)
        self._guarantee_consistency_after_changes()

    def _after_deactivate(self, action_agent, action_summary, action_time):
        super(SymsysCareer, self)._after_deactivate(action_agent, action_summary, action_time)
        self._guarantee_consistency_after_changes()

    def _after_reactivate(self, action_agent, action_summary, action_time):
        super(SymsysCareer, self)._after_reactivate(action_agent, action_summary, action_time)
        self._guarantee_consistency_after_changes()

    def _guarantee_consistency_after_changes(self):
        #TODO perhaps this should be called after modifying permissions, although it doesn't seem necessary.
        # although it would be necessary to ensure AFs can always edit stuff, but that's kind of a hack

        #TODO cleanup this function
        #TODO get the final hierarchy of symsys groups in here
        #TODO figure out "%s Concentration Faculty"

        group_creator = symsys_bot()

        agent = self.symsys_affiliate
        all_possible_group_ids = DemeSetting.objects.filter(active=True, key__startswith="symsys.groups.").values_list('value', flat=True)
        all_possible_groups = Group.objects.filter(pk__in=map(int, all_possible_group_ids))
        groups = []

        groups.append(get_or_create_group('all_ssp_affiliates', 'Affiliates', group_creator))

        my_careers = SymsysCareer.objects.filter(symsys_affiliate=agent, active=True)

        if any(x.actual_item_type() == MinorSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_minors', 'Minors Alumni', group_creator))
        if any(x.actual_item_type() == MinorSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_minors', 'Minors Students', group_creator))

        if any(x.actual_item_type() == BachelorsSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_bs', 'Bachelors Alumni', group_creator))
        if any(x.actual_item_type() == BachelorsSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_bs', 'Bachelors Students', group_creator))

        if any(x.actual_item_type() == MastersSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_ms', 'Masters Alumni', group_creator))
        if any(x.actual_item_type() == MastersSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_ms', 'Masters Students', group_creator))

        if any(x.actual_item_type() == HonorsSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_honors', 'Honors Alumni', group_creator))
        if any(x.actual_item_type() == HonorsSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_honors', 'Honors Students', group_creator))

        if any(x.actual_item_type() == ResearcherSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('past_researchers', 'Past Researchers', group_creator))
        if any(x.actual_item_type() == ResearcherSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('present_researchers', 'Researchers', group_creator))

        if any(x.actual_item_type() == FacultySymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('past_faculty', 'Past Faculty', group_creator))
        if any(x.actual_item_type() == FacultySymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('present_faculty', 'Faculty', group_creator))

        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == True and x.programstaffsymsyscareer.admin_title == 'Advising Fellow' for x in my_careers):
            groups.append(get_or_create_group('past_af', 'Past Advising Fellows', group_creator))
        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == False and x.programstaffsymsyscareer.admin_title == 'Advising Fellow' for x in my_careers):
            groups.append(get_or_create_group('present_af', 'Present Advising Fellows', group_creator))

        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == True and x.programstaffsymsyscareer.admin_title != 'Advising Fellow' for x in my_careers):
            groups.append(get_or_create_group('past_administrators', 'Past Administrators', group_creator))
        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == False and x.programstaffsymsyscareer.admin_title != 'Advising Fellow' for x in my_careers):
            groups.append(get_or_create_group('present_administrators', 'Administrators', group_creator))

        conferred_concentrations = set(BachelorsSymsysCareer.objects.filter(symsys_affiliate=agent, active=True, finished=True).values_list('concentration', flat=True))
        active_concentrations = set(BachelorsSymsysCareer.objects.filter(symsys_affiliate=agent, active=True, finished=False).values_list('concentration', flat=True))
        for concentration in conferred_concentrations:
            groups.append(get_or_create_group('conferred_concentration.%s' % concentration, '%s Concentration Alumni' % concentration, group_creator))
        for concentration in active_concentrations:
            groups.append(get_or_create_group('active_concentration.%s' % concentration, '%s Concentration Students' % concentration, group_creator))

        for career in StudentSymsysCareer.objects.filter(symsys_affiliate=agent, active=True):
            if career.class_year:
                groups.append(get_or_create_group('class%d' % career.class_year, 'Class of %d' % career.class_year, group_creator))

        for group in groups:
            try:
                membership = Membership.objects.get(item=agent, collection=group)
                if not membership.active:
                    membership.reactivate(action_agent=group_creator)
            except ObjectDoesNotExist:
                membership = Membership(item=agent, collection=group)
                # There are no permissions we need to set on these memberships
                membership.save_versioned(action_agent=group_creator)
        for membership_to_remove in Membership.objects.filter(active=True, item=agent, collection__in=all_possible_groups.exclude(pk__in=[x.pk for x in groups])):
            membership_to_remove.deactivate(action_agent=group_creator)

        # Based on current status, set the permissions for the agent to modify fields of this career
        agents_own_abilities = []
        if isinstance(self, ThesisSymsysCareer):
            if not self.finished:
                agents_own_abilities.append('edit ThesisSymsysCareer.second_reader')
                agents_own_abilities.append('edit ThesisSymsysCareer.thesis_title')
        if isinstance(self, StudentSymsysCareer):
            if self.finished:
                agents_own_abilities.append('edit StudentSymsysCareer.class_year')
            else:
                agents_own_abilities.append('edit StudentSymsysCareer.advisor')
            agents_own_abilities.append('edit StudentSymsysCareer.other_degrees')
        if isinstance(self, BachelorsSymsysCareer):
            if not self.finished:
                agents_own_abilities.append('edit BachelorsSymsysCareer.concentration')
        if isinstance(self, ResearcherSymsysCareer):
            agents_own_abilities.append('edit ResearcherSymsysCareer.academic_title')
        if isinstance(self, FacultySymsysCareer):
            agents_own_abilities.append('edit FacultySymsysCareer.academic_title')
        OneToOnePermission.objects.filter(source=agent, target=self, ability__startswith='edit ').delete()
        for ability in agents_own_abilities:
            OneToOnePermission(source=agent, target=self, is_allowed=True, ability=ability).save()

    _guarantee_consistency_after_changes.alters_data = True


class ThesisSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ThesisSymsysCareer.second_reader', 'view ThesisSymsysCareer.thesis',
                                      'view ThesisSymsysCareer.thesis_title', 'edit ThesisSymsysCareer.second_reader',
                                      'edit ThesisSymsysCareer.thesis', 'edit ThesisSymsysCareer.thesis_title'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('thesis Symsys career')
        verbose_name_plural = _('thesis Symsys careers')

    # Fields
    second_reader = FixedForeignKey('SymsysAffiliate', null=True, blank=True, related_name="second_reader_group", verbose_name=_('second reader'), default=None)
    thesis        = FixedForeignKey(FileDocument, null=True, blank=True, related_name="careers_with_thesis", verbose_name=_('thesis'), default=None)
    thesis_title  = models.CharField(_('thesis title'), max_length=255, blank=True)
    #TODO: make a special viewer for the student to upload a file into a FileDocument have have this field point to it (only if blank right now?)


class StudentSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view StudentSymsysCareer.class_year', 'view StudentSymsysCareer.advisor',
                                      'view StudentSymsysCareer.other_degrees', 'edit StudentSymsysCareer.class_year',
                                      'edit StudentSymsysCareer.advisor', 'edit StudentSymsysCareer.other_degrees'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('student Symsys career')
        verbose_name_plural = _('student Symsys careers')

    # Fields
    class_year      = models.PositiveIntegerField(_('class year'), null=True, blank=True, default=None)
    advisor         = FixedForeignKey('SymsysAffiliate', null=True, blank=True, related_name="advisor_group", verbose_name=_('advisor'), default=None)
    other_degrees   = models.CharField(_('other degrees'), max_length=255, blank=True)


class MinorSymsysCareer(StudentSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset([])
    introduced_global_abilities = frozenset(['create MinorSymsysCareer'])
    class Meta:
        verbose_name = _('minor Symsys career')
        verbose_name_plural = _('minor Symsys careers')


class BachelorsSymsysCareer(StudentSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view BachelorsSymsysCareer.indivdesignedconc', 'view BachelorsSymsysCareer.concentration',
                                      'edit BachelorsSymsysCareer.indivdesignedconc', 'edit BachelorsSymsysCareer.concentration'])
    introduced_global_abilities = frozenset(['create BachelorsSymsysCareer'])
    class Meta:
        verbose_name = _('bachelors Symsys career')
        verbose_name_plural = _('bachelors Symsys careers')

    # Fields
    concentration     = models.CharField(_('concentration'), max_length=255, blank=True, choices=[(x,x) for x in BS_CONCENTRATIONS])
    indivdesignedconc = models.CharField(_('individually designed concentration'), max_length=255, blank=True)


class MastersSymsysCareer(StudentSymsysCareer, ThesisSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view MastersSymsysCareer.indivdesignedtrack', 'view MastersSymsysCareer.track',
                                      'edit MastersSymsysCareer.indivdesignedtrack', 'edit MastersSymsysCareer.track'])
    introduced_global_abilities = frozenset(['create MastersSymsysCareer'])
    class Meta:
        verbose_name = _('masters Symsys career')
        verbose_name_plural = _('masters Symsys careers')

    # Fields
    track  = models.CharField(_('track'), max_length=255, blank=True, choices=[(x,x) for x in MS_TRACKS])
    indivdesignedtrack = models.CharField(_('individually designed track'), max_length=255, blank=True)


class HonorsSymsysCareer(ThesisSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HonorsSymsysCareer'])
    class Meta:
        verbose_name = _('honors Symsys career')
        verbose_name_plural = _('honors Symsys careers')

    # Fields
    advisor = FixedForeignKey('SymsysAffiliate', null=True, blank=True, related_name="honors_advisor_group", verbose_name=_('advisor'), default=None)


class ResearcherSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ResearcherSymsysCareer.academic_title', 'edit ResearcherSymsysCareer.academic_title'])
    introduced_global_abilities = frozenset(['create ResearcherSymsysCareer'])
    class Meta:
        verbose_name = _('researcher Symsys career')
        verbose_name_plural = _('researcher Symsys careers')

    # Fields
    academic_title = models.CharField(_('academic title'), max_length=255) # always editable by the researcher


class FacultySymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view FacultySymsysCareer.academic_title', 'edit FacultySymsysCareer.academic_title'])
    introduced_global_abilities = frozenset(['create FacultySymsysCareer'])
    class Meta:
        verbose_name = _('faculty Symsys career')
        verbose_name_plural = _('faculty Symsys careers')

    # Fields
    academic_title = models.CharField(_('academic title'), max_length=255, choices=[(x,x) for x in FACULTY_ACADEMIC_TITLES]) # always editable by the faculty


class ProgramStaffSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset(['admin_title'])
    introduced_abilities = frozenset(['view ProgramStaffSymsysCareer.admin_title', 'view ProgramStaffSymsysCareer.admin_title'])
    introduced_global_abilities = frozenset(['create ProgramStaffSymsysCareer'])
    class Meta:
        verbose_name = _('program staff Symsys career')
        verbose_name_plural = _('program staff Symsys careers')

    # Fields
    admin_title = models.CharField(_('admin title'), max_length=255, choices=[(x,x) for x in ADMIN_TITLES])


class SymsysAffiliate(Person):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view SymsysAffiliate.w_organization', 'view SymsysAffiliate.w_position',
                                      'view SymsysAffiliate.background', 'view SymsysAffiliate.doing_now',
                                      'view SymsysAffiliate.interests', 'view SymsysAffiliate.publications',
                                      'view SymsysAffiliate.office_hours', 'view SymsysAffiliate.about',
                                      'view SymsysAffiliate.photo', 'edit SymsysAffiliate.w_organization',
                                      'edit SymsysAffiliate.w_position', 'edit SymsysAffiliate.background',
                                      'edit SymsysAffiliate.doing_now', 'edit SymsysAffiliate.interests',
                                      'edit SymsysAffiliate.publications', 'edit SymsysAffiliate.office_hours',
                                      'edit SymsysAffiliate.about', 'edit SymsysAffiliate.photo'])
    introduced_global_abilities = frozenset(['create SymsysAffiliate'])
    class Meta:
        verbose_name = _('Symsys affiliate')
        verbose_name_plural = _('Symsys affiliates')

    # Fields
    w_organization = models.CharField(_('work organization'), max_length=255, blank=True)
    w_position     = models.CharField(_('work position'), max_length=255, blank=True)
    background     = models.TextField(_('background'), blank=True)
    doing_now      = models.TextField(_('doing now'), blank=True)
    interests      = models.TextField(_('interests'), blank=True)
    publications   = models.TextField(_('publications'), blank=True)
    office_hours   = models.TextField(_('office hours'), blank=True)
    about          = models.TextField(_('about'), blank=True)
    photo          = FixedForeignKey(ImageDocument, related_name='symsysaffiliates_with_photo', verbose_name=_('photo'), null=True, blank=True, default=None)

    def _after_create(self, action_agent, action_summary, action_time):
        super(SymsysAffiliate, self)._after_create(action_agent, action_summary, action_time)
        group_creator = symsys_bot()
        all_ssp_users = get_or_create_group('all_ssp_users', 'All SSP Users', group_creator)
        membership = Membership(item=self, collection=all_ssp_users)
        # There are no permissions we need to set on this membership
        membership.save_versioned(action_agent=group_creator)


class Event(HtmlDocument):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Event.event_time', 'view Event.location', 'view Event.url',
                                      'edit Event.event_time', 'edit Event.location', 'edit Event.url'])
    introduced_global_abilities = frozenset(['create Event'])
    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('event')

    # Fields
    event_time = models.DateTimeField() #TODO why can this be blank?
    location   = models.TextField(blank=True)
    url        = models.TextField(blank=True)


class Advertisement(Document):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Advertisement.contact_info', 'view Advertisement.expires_at',
                                      'edit Advertisement.contact_info', 'edit Advertisement.expires_at'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('advertisement')
        verbose_name_plural = _('advertisements')

    # Fields
    contact_info = models.TextField(_('contact info'))
    expires_at   = models.DateTimeField(_('expires at'), null=True, blank=True, default=None)


class TextAdvertisement(TextDocument, Advertisement):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create TextAdvertisement'])
    class Meta:
        verbose_name = _('text advertisement')
        verbose_name_plural = _('text advertisements')


class HtmlAdvertisement(HtmlDocument, Advertisement):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HtmlAdvertisement'])
    class Meta:
        verbose_name = _('HTML advertisement')
        verbose_name_plural = _('HTML advertisements')

