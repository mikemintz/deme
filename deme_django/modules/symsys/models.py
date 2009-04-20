from cms.models import *
from django.db import models

__all__ = ['SymsysAffiliate', 'Event', 'Advertisement', 'TextAdvertisement', 'HtmlAdvertisement']

class SymsysCareer(Item):
    student = models.ForeignKey('SymsysAffiliate')
    suid = models.PositiveIntegerField(default=0)
    original_first_name = models.CharField(max_length=255)
    original_middle_names = models.CharField(max_length=255, blank=True)
    original_last_name = models.CharField(max_length=255)
    original_suffix = models.CharField(max_length=255, blank=True)
    first_affiliation_year = models.PositiveIntegerField(null=True, blank=True, default=None)
    then_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_then_image', null=True, blank=True, default=None)

class ThesisSymsysCareer(SymsysCareer):
    second_reader = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="second_reader_group", default=None) # editable by the student BEFORE conferred
    thesis = models.ForeignKey(FileDocument, null=True, blank=True, related_name="careers_with_thesis", default=None) # the student cannot edit this field, but as long as this field is blank, the student can upload a file using a special viewer which will generate a FileDocument that this points to

class StudentSymsysCareer(SymsysCareer):
    class_year = models.PositiveIntegerField(null=True, blank=True, default=None) # editable by the student AFTER conferred
    graduation_year = models.PositiveIntegerField(null=True, blank=True, default=None) # editable by the student BEFORE conferred
    advisor = models.ForeignKey('SymsysAffiliate', null=True, blank=True, related_name="advisor_group", default=None) # editable by the student BEFORE conferred
    other_degrees = models.CharField(max_length=255, blank=True) # always editable
    conferred = models.BooleanField(default=False) # never editable

class BachelorsSymsysCareer(StudentSymsysCareer):
    indivdesignedconc = models.CharField(max_length=255, blank=True) # never editable
    concentration = models.CharField(max_length=255, blank=True) # editable by the student BEFORE conferred
    #TODO add choices for concentration

class MastersSymsysCareer(StudentSymsysCareer):
    track = models.CharField(max_length=255, blank=True) # never editable
    #TODO add choices for track
    ms_idt = models.CharField(max_length=255, blank=True) # never editable

class HonorsSymsysCareer(StudentSymsysCareer):
    pass

class FacultySymsysCareer(SymsysCareer):
    academic_title = models.CharField(max_length=255, choices=[("Assistant Professor", "Assistant Professor"), ("Associate Professor", "Associate Professor"), ("Consulting Assistant Professor", "Consulting Assistant Professor"), ("Consulting Associate Professor", "Consulting Associate Professor"), ("Consulting Professor", "Consulting Professor"), ("Engineering Research Associate", "Engineering Research Associate"), ("Executive Director", "Executive Director"), ("Lecturer", "Lecturer"), ("Professor", "Professor"), ("Professor Emeritus", "Professor Emeritus"), ("Senior Lecturer", "Senior Lecturer"), ("Senior Research Engineer", "Senior Research Engineer"), ("Student Services Officer", "Student Services Officer"), ("University Affiliate", "University Affiliate"), ("Wasow Visiting Lecturer", "Wasow Visiting Lecturer")]) # always editable by the faculty

class ProgramStaffSymsysCareer(SymsysCareer):
    admin_title = models.CharField(max_length=255, choices=[("Advising Fellow", "Advising Fellow"), ("Associate Director", "Associate Director"), ("Director Emeritus", "Director Emeritus"), ("Graduate Studies Director", "Graduate Studies Director"), ("Program Director", "Program Director"), ("Student Services Officer", "Student Services Officer"), ("Webmaster", "Webmaster")]) # never editable by the staff person, but editable by admins

class AdministratorSymsysCareer(ProgramStaffSymsysCareer):
    pass

class AFSymsysCareer(ProgramStaffSymsysCareer):
    year = models.CharField(max_length=255, choices=[('2008-2009', '2008-2009')]) # never editable by the AF, but editable by admins


class SymsysAffiliate(Person):
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view suid', 'view original_first_name', 'view original_middle_names', 'view original_last_name', 'view original_suffix', 'view first_affiliation_year', 'view bs_graduation_year', 'view ms_graduation_year', 'view academic_title', 'view admin_title', 'view bs_advisor', 'view honors_advisor', 'view ms_advisor', 'view honors_second_reader', 'view ms_second_reader', 'view w_organization', 'view w_position', 'view background', 'view doing_now', 'view interests', 'view publications', 'view office_hours', 'view about', 'view other_degrees', 'view indivdesignedconc', 'view honors_thesis_title', 'view honors_thesis_filename', 'view honors_thesis_url', 'view ms_thesis_title', 'view ms_thesis_filename', 'view ms_thesis_url', 'view ms_idt', 'view then_image', 'view now_image', 'edit suid', 'edit original_first_name', 'edit original_middle_names', 'edit original_last_name', 'edit original_suffix', 'edit first_affiliation_year', 'edit bs_graduation_year', 'edit ms_graduation_year', 'edit academic_title', 'edit admin_title', 'edit bs_advisor', 'edit honors_advisor', 'edit ms_advisor', 'edit honors_second_reader', 'edit ms_second_reader', 'edit w_organization', 'edit w_position', 'edit background', 'edit doing_now', 'edit interests', 'edit publications', 'edit office_hours', 'edit about', 'edit other_degrees', 'edit indivdesignedconc', 'edit honors_thesis_title', 'edit honors_thesis_filename', 'edit honors_thesis_url', 'edit ms_thesis_title', 'edit ms_thesis_filename', 'edit ms_thesis_url', 'edit ms_idt', 'edit then_image', 'edit now_image'])
    introduced_global_abilities = frozenset(['create SymsysAffiliate'])

    w_organization = models.CharField(max_length=255, blank=True)
    w_position = models.CharField(max_length=255, blank=True)

    background = models.TextField(blank=True)
    doing_now = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    office_hours = models.TextField(blank=True)
    about = models.TextField(blank=True)

    now_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_now_image', null=True, blank=True, default=None)


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

