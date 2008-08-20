#TODO permissions for who can view which fields (staff, symsysaffiliates, or everyone)
#TODO here are some general privs
#TODO last_login
#TODO what does the 'type' field do?
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
    suid = models.IntegerField(null=True, blank=True)
    site_administrator = models.BooleanField(default=False)
    program_administrator = models.BooleanField(default=False)
    advising_fellow = models.BooleanField(default=False)
    background = models.TextField(blank=True)
    doing_now = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    office_hours = models.TextField(blank=True)
    original_first_name = models.CharField(max_length=100)
    original_middle_names = models.CharField(max_length=100, blank=True)
    original_last_name = models.CharField(max_length=100)
    class_year = models.IntegerField(null=True, blank=True)
    first_affiliation_year = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    admin_title = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    graduation = models.IntegerField(null=True, blank=True)
    concentration = models.CharField(max_length=255, blank=True)
    advisor = models.CharField(max_length=255, blank=True)

    p_address1 = models.CharField(max_length=255, blank=True)
    p_address2 = models.CharField(max_length=255, blank=True)
    p_city = models.CharField(max_length=255, blank=True)
    p_state = models.CharField(max_length=5, blank=True)
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
    w_state = models.CharField(max_length=5, blank=True)
    w_zip = models.CharField(max_length=20, blank=True)
    w_phone1 = models.CharField(max_length=20, blank=True)
    w_phone2 = models.CharField(max_length=20, blank=True)
    w_fax = models.CharField(max_length=20, blank=True)
    w_email = models.CharField(max_length=255, blank=True)
    w_website = models.CharField(max_length=255, blank=True)
    w_im = models.CharField(max_length=255, blank=True)

