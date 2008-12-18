from cms.models import *
from django.db import models

class SymsysAffiliate(Person):
    suid = models.IntegerField(default=0)

    original_first_name = models.CharField(max_length=255)
    original_middle_names = models.CharField(max_length=255, blank=True)
    original_last_name = models.CharField(max_length=255)
    original_suffix = models.CharField(max_length=255, blank=True)

    class_year = models.IntegerField(null=True, blank=True)
    first_affiliation_year = models.IntegerField(null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)

    academic_title = models.CharField(max_length=255, blank=True)
    admin_title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    concentration = models.CharField(max_length=255, blank=True)
    advisor = models.CharField(max_length=255, blank=True)

    p_address1 = models.CharField(max_length=255, blank=True)
    p_address2 = models.CharField(max_length=255, blank=True)
    p_city = models.CharField(max_length=255, blank=True)
    p_state = models.CharField(max_length=255, blank=True)
    p_country = models.CharField(max_length=255, blank=True)
    p_zip = models.CharField(max_length=20, blank=True)
    p_phone1 = models.CharField(max_length=20, blank=True)
    p_phone2 = models.CharField(max_length=20, blank=True)
    p_fax = models.CharField(max_length=20, blank=True)
    p_email = models.CharField(max_length=255, blank=True)
    p_website = models.CharField(max_length=255, blank=True)
    p_im = models.CharField(max_length=255, blank=True)

    w_organization = models.CharField(max_length=255, blank=True)
    w_position = models.CharField(max_length=255, blank=True)
    w_address1 = models.CharField(max_length=255, blank=True)
    w_address2 = models.CharField(max_length=255, blank=True)
    w_city = models.CharField(max_length=255, blank=True)
    w_state = models.CharField(max_length=255, blank=True)
    w_country = models.CharField(max_length=255, blank=True)
    w_zip = models.CharField(max_length=20, blank=True)
    w_phone1 = models.CharField(max_length=20, blank=True)
    w_phone2 = models.CharField(max_length=20, blank=True)
    w_fax = models.CharField(max_length=20, blank=True)
    w_email = models.CharField(max_length=255, blank=True)
    w_website = models.CharField(max_length=255, blank=True)
    w_im = models.CharField(max_length=255, blank=True)

    background = models.TextField(blank=True)
    doing_now = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    office_hours = models.TextField(blank=True)
    about = models.TextField(blank=True)

    symsys_degree = models.CharField(max_length=255, blank=True)
    other_degrees = models.CharField(max_length=255, blank=True)
    indivdesignedconc = models.CharField(max_length=255, blank=True)
    department2 = models.CharField(max_length=255, blank=True)
    ms_track = models.CharField(max_length=255, blank=True)
    ms_graduation = models.IntegerField(blank=True, null=True)

    honors_thesis_title = models.CharField(max_length=255, blank=True)
    honors_thesis_filename = models.CharField(max_length=255, blank=True)
    honors_thesis_url = models.CharField(max_length=255, blank=True)

    ms_thesis_title = models.CharField(max_length=255, blank=True)
    ms_thesis_filename = models.CharField(max_length=255, blank=True)
    ms_thesis_url = models.CharField(max_length=255, blank=True)
    ms_idt = models.CharField(max_length=255, blank=True)

    respos_job_email_subscribe = models.CharField(max_length=20, blank=True)

    honors_status = models.IntegerField(blank=True, null=True)
    honors_advisor = models.CharField(max_length=255, blank=True)
    honors_second_reader = models.CharField(max_length=255, blank=True)

    then_image = models.ForeignKey(FileDocument, related_name='symsysaffiliates_with_then_image', blank=True, null=True)
    now_image = models.ForeignKey(FileDocument, related_name='symsysaffiliates_with_now_image', blank=True, null=True)


class Event(HtmlDocument):
    event_time = models.DateTimeField()
    location = models.TextField(blank=True)
    url = models.TextField(blank=True)


class Advertisement(Document):
    contact_info = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)


class TextAdvertisement(Advertisement, TextDocument):
    pass


class HtmlAdvertisement(Advertisement, HtmlDocument):
    pass

