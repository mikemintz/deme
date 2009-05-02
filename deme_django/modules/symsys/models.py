from cms.models import *
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

__all__ = ['SymsysCareer', 'ThesisSymsysCareer', 'StudentSymsysCareer', 'MinorSymsysCareer', 'BachelorsSymsysCareer', 'MastersSymsysCareer', 'HonorsSymsysCareer', 'FacultySymsysCareer', 'ProgramStaffSymsysCareer', 'SymsysAffiliate', 'Event', 'Advertisement', 'TextAdvertisement', 'HtmlAdvertisement']


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


class SymsysCareer(Item):
    # Setup
    introduced_immutable_fields = frozenset(['symsys_affiliate'])
    introduced_abilities = frozenset(['view symsys_affiliate', 'view suid', 'view original_first_name', 'view original_middle_names',
                                      'view original_last_name', 'view original_suffix', 'view original_photo', 'view start_date', 'view end_date', 'view finished',
                                      'edit suid', 'edit original_first_name', 'edit original_middle_names',
                                      'edit original_last_name', 'edit original_suffix', 'edit original_photo', 'edit start_date', 'edit end_date', 'edit finished'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('Symsys career')
        verbose_name_plural = _('Symsys careers')

    # Fields
    symsys_affiliate      = models.ForeignKey('SymsysAffiliate', verbose_name=_('Symsys affiliate'), related_name='symsys_careers')
    suid                  = models.PositiveIntegerField(_('SUID'), default=0)
    original_first_name   = models.CharField(_('original first name'), max_length=255)
    original_middle_names = models.CharField(_('original middle names'), max_length=255, blank=True)
    original_last_name    = models.CharField(_('original last name'), max_length=255)
    original_suffix       = models.CharField(_('original suffix'), max_length=255, blank=True)
    original_photo        = models.ForeignKey(ImageDocument, related_name='symsyscareers_with_original_photo', verbose_name=_('original photo'), null=True, blank=True, default=None)
    finished              = models.BooleanField(_('finished'), default=False)
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
        #TODO perhaps this should be called after modifying permissions, although it doesn't seem necessary

        group_creator = Agent.objects.get(pk=DemeSetting.get("symsys.symsys_bot"))

        agent = self.symsys_affiliate
        all_possible_groups = Group.objects.filter(pk__in=map(int, DemeSetting.objects.filter(active=True, key__startswith="symsys.groups.").values_list('value', flat=True)))
        groups = []

        groups.append(get_or_create_group('all_ssp_users', 'All SSP Users', group_creator))

        my_careers = SymsysCareer.objects.filter(symsys_affiliate=agent, active=True)

        if any(x.actual_item_type() == MinorSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_minors', 'Conferred Minors', group_creator))
        if any(x.actual_item_type() == MinorSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_minors', 'Active Minors', group_creator))

        if any(x.actual_item_type() == BachelorsSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_bs', 'Conferred Bachelors', group_creator))
        if any(x.actual_item_type() == BachelorsSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_bs', 'Active Bachelors', group_creator))

        if any(x.actual_item_type() == MastersSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_ms', 'Conferred Masters', group_creator))
        if any(x.actual_item_type() == MastersSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_ms', 'Active Masters', group_creator))

        if any(x.actual_item_type() == HonorsSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('conferred_honors', 'Conferred Honors', group_creator))
        if any(x.actual_item_type() == HonorsSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('active_honors', 'Active Honors', group_creator))

        if any(x.actual_item_type() == FacultySymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('past_faculty', 'Past Faculty', group_creator))
        if any(x.actual_item_type() == FacultySymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('present_faculty', 'Present Faculty', group_creator))

        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == True for x in my_careers):
            groups.append(get_or_create_group('past_staff', 'Past Staff', group_creator))
        if any(x.actual_item_type() == ProgramStaffSymsysCareer and x.finished == False for x in my_careers):
            groups.append(get_or_create_group('present_staff', 'Present Staff', group_creator))

        concentrations = set(BachelorsSymsysCareer.objects.filter(symsys_affiliate=agent, active=True).values_list('concentration', flat=True))
        tracks = set(MastersSymsysCareer.objects.filter(symsys_affiliate=agent, active=True).values_list('track', flat=True))
        for concentration in concentrations:
            groups.append(get_or_create_group('bs_concentration.%s' % concentration, '%s B.S. Concentration' % concentration, group_creator))
        for track in tracks:
            groups.append(get_or_create_group('ms_track.%s' % track, '%s M.S. Track' % track, group_creator))

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
                agents_own_abilities.append('edit second_reader')
        if isinstance(self, StudentSymsysCareer):
            if self.finished:
                agents_own_abilities.append('edit class_year')
            else:
                agents_own_abilities.append('edit advisor')
            agents_own_abilities.append('edit other_degrees')
        if isinstance(self, BachelorsSymsysCareer):
            if not self.finished:
                agents_own_abilities.append('edit concentration')
        AgentItemPermission.objects.filter(agent=agent, item=self, ability__startswith='edit ').delete()
        for ability in agents_own_abilities:
            AgentItemPermission(agent=agent, item=self, is_allowed=True, ability=ability).save()

    _guarantee_consistency_after_changes.alters_data = True

class ThesisSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view second_reader', 'view thesis', 'edit second_reader', 'edit thesis'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('thesis Symsys career')
        verbose_name_plural = _('thesis Symsys careers')

    # Fields
    second_reader = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="second_reader_group", verbose_name=_('second reader'), default=None)
    thesis        = models.ForeignKey(FileDocument, null=True, blank=True, related_name="careers_with_thesis", verbose_name=_('thesis'), default=None)
    #TODO: make a special viewer for the student to upload a file into a FileDocument have have this field point to it (only if blank right now?)

class StudentSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view class_year', 'view advisor', 'view other_degrees',
                                      'edit class_year', 'edit advisor', 'edit other_degrees'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('student Symsys career')
        verbose_name_plural = _('student Symsys careers')

    # Fields
    class_year      = models.PositiveIntegerField(_('class year'), null=True, blank=True, default=None)
    advisor         = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="advisor_group", verbose_name=_('advisor'), default=None)
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
    introduced_abilities = frozenset(['view indivdesignedconc', 'view concentration', 'edit indivdesignedconc', 'edit concentration'])
    introduced_global_abilities = frozenset(['create BachelorsSymsysCareer'])
    class Meta:
        verbose_name = _('bachelors Symsys career')
        verbose_name_plural = _('bachelors Symsys careers')

    # Fields
    concentration     = models.CharField(_('concentration'), max_length=255, blank=True, choices=[('Applied Logic', 'Applied Logic'), ('Artificial Intelligence', 'Artificial Intelligence'), ('Cognition', 'Cognition'), ('Cognitive Science', 'Cognitive Science'), ('Computation', 'Computation'), ('Computer Music', 'Computer Music'), ('Decision Making and Rationality', 'Decision Making and Rationality'), ('Education and Learning', 'Education and Learning'), ('HCI', 'HCI'), ('Individually Designed Concentration', 'Individually Designed Concentration'), ('Learning', 'Learning'), ('Natural Language', 'Natural Language'), ('Neural Systems', 'Neural Systems'), ('Neurosciences', 'Neurosciences'), ('Philosophical Foundations', 'Philosophical Foundations'), ('Rationality', 'Rationality'), ('Undecided', 'Undecided')])
    indivdesignedconc = models.CharField(_('individually designed concentration'), max_length=255, blank=True)

class MastersSymsysCareer(StudentSymsysCareer, ThesisSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view indivdesignedconc', 'view concentration', 'edit indivdesignedconc', 'edit concentration'])
    introduced_global_abilities = frozenset(['create MastersSymsysCareer'])
    class Meta:
        verbose_name = _('masters Symsys career')
        verbose_name_plural = _('masters Symsys careers')

    # Fields
    track  = models.CharField(_('track'), max_length=255, blank=True, choices=[('HCI', 'HCI'), ('Individually Designed Track', 'Individually Designed Track'), ('Natural Language Technology', 'Natural Language Technology')])
    indivdesignedtrack = models.CharField(_('individually designed track'), max_length=255, blank=True)

class HonorsSymsysCareer(ThesisSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HonorsSymsysCareer'])
    class Meta:
        verbose_name = _('honors Symsys career')
        verbose_name_plural = _('honors Symsys careers')

class FacultySymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view academic_title', 'edit academic_title'])
    introduced_global_abilities = frozenset(['create FacultySymsysCareer'])
    class Meta:
        verbose_name = _('faculty Symsys career')
        verbose_name_plural = _('faculty Symsys careers')

    # Fields
    academic_title = models.CharField(_('academic title'), max_length=255, choices=[("Assistant Professor", "Assistant Professor"), ("Associate Professor", "Associate Professor"), ("Consulting Assistant Professor", "Consulting Assistant Professor"), ("Consulting Associate Professor", "Consulting Associate Professor"), ("Consulting Professor", "Consulting Professor"), ("Engineering Research Associate", "Engineering Research Associate"), ("Executive Director", "Executive Director"), ("Lecturer", "Lecturer"), ("Professor", "Professor"), ("Professor Emeritus", "Professor Emeritus"), ("Senior Lecturer", "Senior Lecturer"), ("Senior Research Engineer", "Senior Research Engineer"), ("Student Services Officer", "Student Services Officer"), ("University Affiliate", "University Affiliate"), ("Wasow Visiting Lecturer", "Wasow Visiting Lecturer")]) # always editable by the faculty

class ProgramStaffSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset(['admin_title'])
    introduced_abilities = frozenset(['view admin_title', 'view start_date', 'view end_date',
                                      'view admin_title', 'view start_date', 'view end_date'])
    introduced_global_abilities = frozenset(['create ProgramStaffSymsysCareer'])
    class Meta:
        verbose_name = _('program staff Symsys career')
        verbose_name_plural = _('program staff Symsys careers')

    # Fields
    admin_title = models.CharField(_('admin title'), max_length=255, choices=[("Advising Fellow", "Advising Fellow"), ("Associate Director", "Associate Director"), ("Director Emeritus", "Director Emeritus"), ("Graduate Studies Director", "Graduate Studies Director"), ("Program Director", "Program Director"), ("Student Services Officer", "Student Services Officer"), ("Webmaster", "Webmaster")])


class SymsysAffiliate(Person):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view w_organization', 'view w_position', 'view background', 'view doing_now', 'view interests', 'view publications', 'view office_hours', 'view about', 'view photo', 'edit w_organization', 'edit w_position', 'edit background', 'edit doing_now', 'edit interests', 'edit publications', 'edit office_hours', 'edit about', 'edit photo'])
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
    photo          = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_photo', verbose_name=_('photo'), null=True, blank=True, default=None)

    def _after_create(self, action_agent, action_summary, action_time):
        super(SymsysAffiliate, self)._after_create(action_agent, action_summary, action_time)
        group_creator = Agent.objects.get(pk=DemeSetting.get("symsys.symsys_bot"))
        all_ssp_users = get_or_create_group('all_ssp_users', 'All SSP Users', group_creator)
        membership = Membership(item=self, collection=all_ssp_users)
        # There are no permissions we need to set on this membership
        membership.save_versioned(action_agent=group_creator)


class Event(HtmlDocument):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view event_time', 'view location', 'view url', 'edit event_time', 'edit location', 'edit url'])
    introduced_global_abilities = frozenset(['create Event'])
    event_time = models.DateTimeField() #TODO why can this be blank?
    location = models.TextField(blank=True)
    url = models.TextField(blank=True)


class Advertisement(Document):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view contact_info', 'view expires_at', 'edit contact_info', 'edit expires_at'])
    introduced_global_abilities = frozenset()
    contact_info = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True, default=None)


class TextAdvertisement(TextDocument, Advertisement):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create TextAdvertisement'])


class HtmlAdvertisement(HtmlDocument, Advertisement):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create HtmlAdvertisement'])

