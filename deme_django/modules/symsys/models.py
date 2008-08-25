from cms.models import *
from django.db import models

#TODO last_login
#TODO permissions for who can view which fields (staff, symsysaffiliates, or everyone)
#TODO here are some general privs
# if (flag.equals("GENERAL")) return hasFlag(FLAGS_ADMIN_GENERAL);
# if (flag.equals("CREATE")) return hasFlag(FLAGS_ADMIN_CREATE);
# if (flag.equals("MESSAGE")) return hasFlag(FLAGS_ADMIN_MESSAGE);
# if (flag.equals("EVENTS")) return hasFlag(FLAGS_ADMIN_EVENTS);
# if (flag.equals("ACCOUNTS")) return hasFlag(FLAGS_ADMIN_ACCOUNTS);
# if (flag.equals("BOOKLET")) return hasFlag(FLAGS_ADMIN_BOOKLET);
# if (flag.equals("RESEARCH")) return hasFlag(FLAGS_ADMIN_RESEARCH);
# if (flag.equals("JOBS")) return hasFlag(FLAGS_ADMIN_JOBS);
# if (flag.equals("COURSES")) return hasFlag(FLAGS_ADMIN_COURSES);
# if (flag.equals("TASKS")) return hasFlag(FLAGS_ADMIN_TASKS);

class SymsysAffiliate(Person):
    suid = models.IntegerField(default=0)

    original_first_name = models.CharField(max_length=255)
    original_middle_names = models.CharField(max_length=255, blank=True)
    original_last_name = models.CharField(max_length=255)

    class_year = models.CharField(max_length=255, blank=True)
    first_affiliation_year = models.IntegerField(null=True, blank=True)

    title = models.CharField(max_length=255, blank=True)
    admin_title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    graduation = models.CharField(max_length=255, blank=True)
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
    bs = models.CharField(max_length=20, blank=True)
    ms = models.CharField(max_length=20, blank=True)
    minor = models.CharField(max_length=20, blank=True)
    ms_track = models.CharField(max_length=255, blank=True)
    ms_graduation = models.IntegerField(blank=True, null=True)

    honors_thesis_title = models.CharField(max_length=255, blank=True)
    honors_thesis_filename = models.CharField(max_length=255, blank=True)
    honors_thesis_url = models.CharField(max_length=255, blank=True)

    ms_thesis_title = models.CharField(max_length=255, blank=True)
    ms_thesis_filename = models.CharField(max_length=255, blank=True)
    ms_thesis_url = models.CharField(max_length=255, blank=True)
    ms_idt = models.CharField(max_length=255, blank=True)

    faculty = models.CharField(max_length=20, blank=True)
    af = models.CharField(max_length=20, blank=True)
    progadmin = models.CharField(max_length=20, blank=True)
    siteadmin = models.CharField(max_length=20, blank=True)
    respos_job_email_subscribe = models.CharField(max_length=20, blank=True)

    honors_status = models.IntegerField(blank=True, null=True)
    honors_advisor = models.CharField(max_length=255, blank=True)
    honors_second_reader = models.CharField(max_length=255, blank=True)

    then_image = models.ForeignKey(FileDocument, related_name='symsysaffiliates_with_then_image')
    now_image = models.ForeignKey(FileDocument, related_name='symsysaffiliates_with_now_image')

    def get_name(self):
        return '%s %s' % (self.first_name, self.last_name)

class Event(Item):
    event_time = models.DateTimeField()
    event_name = models.CharField(max_length=255)
    event_details = models.TextField(blank=True)
    location = models.TextField(blank=True)
    url = models.TextField(blank=True)

    def get_name(self):
        return self.event_name
