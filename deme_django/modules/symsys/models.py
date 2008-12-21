from cms.models import *
from django.db import models

class SymsysAffiliate(Person):
    suid = models.IntegerField(default=0)

    original_first_name = models.CharField(max_length=255)
    original_middle_names = models.CharField(max_length=255, blank=True)
    original_last_name = models.CharField(max_length=255)
    original_suffix = models.CharField(max_length=255, blank=True)

    first_affiliation_year = models.IntegerField(null=True, blank=True)
    bs_graduation_year = models.IntegerField(null=True, blank=True)

    academic_title = models.CharField(max_length=255, blank=True, choices=[("Assistant Professor", "Assistant Professor"), ("Associate Professor", "Associate Professor"), ("Associate Professor (Research)", "Associate Professor (Research)"), ("Consulting Assistant Professor", "Consulting Assistant Professor"), ("Consulting Associate Professor", "Consulting Associate Professor"), ("Consulting Professor", "Consulting Professor"), ("Engineering Research Associate", "Engineering Research Associate"), ("Executive Director", "Executive Director"), ("Lecturer", "Lecturer"), ("Professor", "Professor"), ("Professor Emeritus", "Professor Emeritus"), ("Senior Lecturer", "Senior Lecturer"), ("Senior Research Engineer", "Senior Research Engineer"), ("Student Services Officer", "Student Services Officer"), ("University Affiliate", "University Affiliate"), ("Wasow Visiting Lecturer", "Wasow Visiting Lecturer"), ("Web Design", "Web Design"),])
    admin_title = models.CharField(max_length=255, blank=True, choices=[("Advising Fellow", "Advising Fellow"), ("AF", "AF"), ("Associate Director", "Associate Director"), ("Director Emeritus", "Director Emeritus"), ("Graduate Studies Director", "Graduate Studies Director"), ("Program Director", "Program Director"), ("Student Services Officer", "Student Services Officer"), ("Student Services Officer (on leave)", "Student Services Officer (on leave)"), ("Web Developer", "Web Developer"), ("Webmaster", "Webmaster"), ("Webmaster (2003-2004)", "Webmaster (2003-2004)"),])
    advisor = models.CharField(max_length=255, blank=True)

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
    ms_graduation_year = models.IntegerField(blank=True, null=True)

    honors_thesis_title = models.CharField(max_length=255, blank=True)
    honors_thesis_filename = models.CharField(max_length=255, blank=True)
    honors_thesis_url = models.CharField(max_length=255, blank=True)

    ms_thesis_title = models.CharField(max_length=255, blank=True)
    ms_thesis_filename = models.CharField(max_length=255, blank=True)
    ms_thesis_url = models.CharField(max_length=255, blank=True)
    ms_idt = models.CharField(max_length=255, blank=True)

    honors_advisor = models.CharField(max_length=255, blank=True)
    honors_second_reader = models.CharField(max_length=255, blank=True)

    then_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_then_image', blank=True, null=True)
    now_image = models.ForeignKey(ImageDocument, related_name='symsysaffiliates_with_now_image', blank=True, null=True)


class Event(HtmlDocument):
    event_time = models.DateTimeField()
    location = models.TextField(blank=True)
    url = models.TextField(blank=True)


class Advertisement(Document):
    contact_info = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)


class TextAdvertisement(TextDocument, Advertisement):
    pass


class HtmlAdvertisement(HtmlDocument, Advertisement):
    pass

