from cms.models import *
from django.db import models

class SymsysAffiliate(Person):
    immutable_fields = Person.immutable_fields
    relevant_abilities = Person.relevant_abilities | set(['view suid', 'view original_first_name', 'view original_middle_names', 'view original_last_name', 'view original_suffix', 'view first_affiliation_year', 'view bs_graduation_year', 'view ms_graduation_year', 'view academic_title', 'view admin_title', 'view advisor', 'view honors_advisor', 'view honors_second_reader', 'view w_organization', 'view w_position', 'view background', 'view doing_now', 'view interests', 'view publications', 'view office_hours', 'view about', 'view other_degrees', 'view indivdesignedconc', 'view honors_thesis_title', 'view honors_thesis_filename', 'view honors_thesis_url', 'view ms_thesis_title', 'view ms_thesis_filename', 'view ms_thesis_url', 'view ms_idt', 'view then_image', 'view now_image', 'edit suid', 'edit original_first_name', 'edit original_middle_names', 'edit original_last_name', 'edit original_suffix', 'edit first_affiliation_year', 'edit bs_graduation_year', 'edit ms_graduation_year', 'edit academic_title', 'edit admin_title', 'edit advisor', 'edit honors_advisor', 'edit honors_second_reader', 'edit w_organization', 'edit w_position', 'edit background', 'edit doing_now', 'edit interests', 'edit publications', 'edit office_hours', 'edit about', 'edit other_degrees', 'edit indivdesignedconc', 'edit honors_thesis_title', 'edit honors_thesis_filename', 'edit honors_thesis_url', 'edit ms_thesis_title', 'edit ms_thesis_filename', 'edit ms_thesis_url', 'edit ms_idt', 'edit then_image', 'edit now_image'])

    suid = models.PositiveIntegerField(default=0)

    original_first_name = models.CharField(max_length=255)
    original_middle_names = models.CharField(max_length=255, blank=True)
    original_last_name = models.CharField(max_length=255)
    original_suffix = models.CharField(max_length=255, blank=True)

    first_affiliation_year = models.PositiveIntegerField(null=True, blank=True)
    bs_graduation_year = models.PositiveIntegerField(null=True, blank=True)
    ms_graduation_year = models.PositiveIntegerField(blank=True, null=True)

    academic_title = models.CharField(max_length=255, blank=True, choices=[("Assistant Professor", "Assistant Professor"), ("Associate Professor", "Associate Professor"), ("Associate Professor (Research)", "Associate Professor (Research)"), ("Consulting Assistant Professor", "Consulting Assistant Professor"), ("Consulting Associate Professor", "Consulting Associate Professor"), ("Consulting Professor", "Consulting Professor"), ("Engineering Research Associate", "Engineering Research Associate"), ("Executive Director", "Executive Director"), ("Lecturer", "Lecturer"), ("Professor", "Professor"), ("Professor Emeritus", "Professor Emeritus"), ("Senior Lecturer", "Senior Lecturer"), ("Senior Research Engineer", "Senior Research Engineer"), ("Student Services Officer", "Student Services Officer"), ("University Affiliate", "University Affiliate"), ("Wasow Visiting Lecturer", "Wasow Visiting Lecturer"), ("Web Design", "Web Design"),])
    admin_title = models.CharField(max_length=255, blank=True, choices=[("Advising Fellow", "Advising Fellow"), ("AF", "AF"), ("Associate Director", "Associate Director"), ("Director Emeritus", "Director Emeritus"), ("Graduate Studies Director", "Graduate Studies Director"), ("Program Director", "Program Director"), ("Student Services Officer", "Student Services Officer"), ("Student Services Officer (on leave)", "Student Services Officer (on leave)"), ("Web Developer", "Web Developer"), ("Webmaster", "Webmaster"), ("Webmaster (2003-2004)", "Webmaster (2003-2004)"),])

    advisor = models.CharField(max_length=255, blank=True)
    honors_advisor = models.CharField(max_length=255, blank=True)
    honors_second_reader = models.CharField(max_length=255, blank=True)

    w_organization = models.CharField(max_length=255, blank=True)
    w_position = models.CharField(max_length=255, blank=True)

    background = models.TextField(blank=True)
    doing_now = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    office_hours = models.TextField(blank=True)
    about = models.TextField(blank=True)

    other_degrees = models.CharField(max_length=255, blank=True)
    indivdesignedconc = models.CharField(max_length=255, blank=True)

    honors_thesis_title = models.CharField(max_length=255, blank=True)
    honors_thesis_filename = models.CharField(max_length=255, blank=True)
    honors_thesis_url = models.CharField(max_length=255, blank=True)

    ms_thesis_title = models.CharField(max_length=255, blank=True)
    ms_thesis_filename = models.CharField(max_length=255, blank=True)
    ms_thesis_url = models.CharField(max_length=255, blank=True)
    ms_idt = models.CharField(max_length=255, blank=True)

    then_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_then_image', blank=True, null=True)
    now_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_now_image', blank=True, null=True)


class Event(HtmlDocument):
    immutable_fields = HtmlDocument.immutable_fields
    relevant_abilities = HtmlDocument.relevant_abilities | set(['view event_time', 'view location', 'view url', 'edit event_time', 'edit location', 'edit url'])
    event_time = models.DateTimeField()
    location = models.TextField(blank=True)
    url = models.TextField(blank=True)


class Advertisement(Document):
    immutable_fields = Document.immutable_fields
    relevant_abilities = Document.relevant_abilities | set(['view contact_info', 'view expires_at', 'edit contact_info', 'edit expires_at'])
    contact_info = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)


class TextAdvertisement(TextDocument, Advertisement):
    immutable_fields = TextDocument.immutable_fields | Advertisement.immutable_fields
    relevant_abilities = TextDocument.relevant_abilities | Advertisement.relevant_abilities


class HtmlAdvertisement(HtmlDocument, Advertisement):
    immutable_fields = HtmlDocument.immutable_fields | Advertisement.immutable_fields
    relevant_abilities = HtmlDocument.relevant_abilities | Advertisement.relevant_abilities

