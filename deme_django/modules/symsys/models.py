from cms.models import *
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ['SymsysCareer', 'ThesisSymsysCareer', 'StudentSymsysCareer', 'BachelorsSymsysCareer', 'MastersSymsysCareer', 'HonorsSymsysCareer', 'FacultySymsysCareer', 'ProgramStaffSymsysCareer', 'AdministratorSymsysCareer', 'AFSymsysCareer', 'SymsysAffiliate', 'Event', 'Advertisement', 'TextAdvertisement', 'HtmlAdvertisement']


class SymsysCareer(Item):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view student', 'view suid', 'view original_first_name', 'view original_middle_names',
                                      'view original_last_name', 'view original_suffix', 'view first_affiliation_year', 'view original_photo',
                                      'edit student', 'edit suid', 'edit original_first_name', 'edit original_middle_names',
                                      'edit original_last_name', 'edit original_suffix', 'edit first_affiliation_year', 'edit original_photo'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('Symsys career')
        verbose_name_plural = _('Symsys careers')

    # Fields
    symsys_affiliate       = models.ForeignKey('SymsysAffiliate', verbose_name=_('Symsys affiliate'))
    suid                   = models.PositiveIntegerField(_('SUID'), default=0)
    original_first_name    = models.CharField(_('original first name'), max_length=255)
    original_middle_names  = models.CharField(_('original middle names'), max_length=255, blank=True)
    original_last_name     = models.CharField(_('original last name'), max_length=255)
    original_suffix        = models.CharField(_('original suffix'), max_length=255, blank=True)
    first_affiliation_year = models.PositiveIntegerField(_('first affiliation year'), null=True, blank=True, default=None)
    original_photo         = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_then_image', verbose_name=_('original photo'), null=True, blank=True, default=None)

class ThesisSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view second_reader', 'view thesis', 'edit second_reader', 'edit thesis'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('thesis Symsys career')
        verbose_name_plural = _('thesis Symsys careers')

    # Fields
    second_reader = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="second_reader_group", verbose_name=_('second reader'), default=None) # editable by the student BEFORE conferred
    thesis        = models.ForeignKey(FileDocument, null=True, blank=True, related_name="careers_with_thesis", verbose_name=_('thesis'), default=None) # the student cannot edit this field, but as long as this field is blank, the student can upload a file using a special viewer which will generate a FileDocument that this points to

#TODO continue after this line

class StudentSymsysCareer(SymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view class_year', 'view graduation_year', 'view advisor', 'view other_degrees', 'view conferred',
                                      'edit class_year', 'edit graduation_year', 'edit advisor', 'edit other_degrees', 'edit conferred'])
    introduced_global_abilities = frozenset()
    class Meta:
        verbose_name = _('student Symsys career')
        verbose_name_plural = _('student Symsys careers')

    # Fields
    class_year      = models.PositiveIntegerField(_('class year'), null=True, blank=True, default=None) # editable by the student AFTER conferred
    graduation_year = models.PositiveIntegerField(_('graduation year'), null=True, blank=True, default=None) # editable by the student BEFORE conferred
    advisor         = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="advisor_group", verbose_name=_('advisor'), default=None) # editable by the student BEFORE conferred
    other_degrees   = models.CharField(_('other degrees'), max_length=255, blank=True) # always editable
    conferred       = models.BooleanField(_('conferred'), default=False) # never editable

class BachelorsSymsysCareer(StudentSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view indivdesignedconc', 'view concentration', 'edit indivdesignedconc', 'edit concentration'])
    introduced_global_abilities = frozenset(['create BachelorsSymsysCareer'])
    class Meta:
        verbose_name = _('bachelors Symsys career')
        verbose_name_plural = _('bachelors Symsys careers')

    # Fields
    concentration     = models.CharField(_('concentration'), max_length=255, blank=True, choices=[('Applied Logic', 'Applied Logic'), ('Artificial Intelligence', 'Artificial Intelligence'), ('Cognition', 'Cognition'), ('Cognitive Science', 'Cognitive Science'), ('Computation', 'Computation'), ('Computer Music', 'Computer Music'), ('Decision Making and Rationality', 'Decision Making and Rationality'), ('Education and Learning', 'Education and Learning'), ('HCI', 'HCI'), ('Individually Designed Concentration', 'Individually Designed Concentration'), ('Learning', 'Learning'), ('Natural Language', 'Natural Language'), ('Neural Systems', 'Neural Systems'), ('Neurosciences', 'Neurosciences'), ('Philosophical Foundations', 'Philosophical Foundations'), ('Rationality', 'Rationality'), ('Undecided', 'Undecided')]) # editable by the student BEFORE conferred
    indivdesignedconc = models.CharField(_('individually designed concentration'), max_length=255, blank=True) # never editable

class MastersSymsysCareer(StudentSymsysCareer, ThesisSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view indivdesignedconc', 'view concentration', 'edit indivdesignedconc', 'edit concentration'])
    introduced_global_abilities = frozenset(['create MastersSymsysCareer'])
    class Meta:
        verbose_name = _('masters Symsys career')
        verbose_name_plural = _('masters Symsys careers')

    # Fields
    track  = models.CharField(_('track'), max_length=255, blank=True, choices=[('HCI', 'HCI'), ('Individually Designed Track', 'Individually Designed Track'), ('Natural Language Technology', 'Natural Language Technology')]) # never editable
    indivdesignedtrack = models.CharField(_('individually designed track'), max_length=255, blank=True) # never editable

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
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view admin_title', 'edit admin_title'])
    introduced_global_abilities = frozenset(['create ProgramStaffSymsysCareer'])
    class Meta:
        verbose_name = _('program staff Symsys career')
        verbose_name_plural = _('program staff Symsys careers')

    # Fields
    admin_title = models.CharField(_('admin title'), max_length=255, choices=[("Advising Fellow", "Advising Fellow"), ("Associate Director", "Associate Director"), ("Director Emeritus", "Director Emeritus"), ("Graduate Studies Director", "Graduate Studies Director"), ("Program Director", "Program Director"), ("Student Services Officer", "Student Services Officer"), ("Webmaster", "Webmaster")]) # never editable by the staff person, but editable by admins

class AdministratorSymsysCareer(ProgramStaffSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create AdministratorSymsysCareer'])
    class Meta:
        verbose_name = _('administrator Symsys career')
        verbose_name_plural = _('administrator Symsys careers')

class AFSymsysCareer(ProgramStaffSymsysCareer):
    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view year', 'edit year'])
    introduced_global_abilities = frozenset(['create AFSymsysCareer'])
    class Meta:
        verbose_name = _('AF Symsys career')
        verbose_name_plural = _('AF Symsys careers')

    # Fields
    year = models.CharField(_('year'), max_length=255, choices=[('2008-2009', '2008-2009')]) # never editable by the AF, but editable by admins


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


class Event(HtmlDocument):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view event_time', 'view location', 'view url', 'edit event_time', 'edit location', 'edit url'])
    introduced_global_abilities = frozenset(['create Event'])
    event_time = models.DateTimeField()
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

