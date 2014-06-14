from django import forms
from modules.symsys.models import BS_CONCENTRATIONS, MS_TRACKS
from modules.demeaccount.models import DemeAccount
import datetime

class SymsysAffiliateWizardForm(forms.Form):
    first_name = forms.CharField()
    middle_names = forms.CharField(required=False)
    last_name = forms.CharField()
    suid = forms.IntegerField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    start_date = forms.DateField(initial=datetime.date.today)
    # TODO: image

    def clean_email(self):
        data = self.cleaned_data['email']
        try:
            DemeAccount.objects.get(username=data)
            raise forms.ValidationError("This email is already associated with a user")
        except DemeAccount.DoesNotExist:
            return data


class StudentSymsysAffiliateWizardForm(SymsysAffiliateWizardForm):
    class_year = forms.IntegerField(min_value=1900, max_value=9999, help_text="As YYYY") # not 10k proof


class BachelorsSymsysAffiliateWizardForm(StudentSymsysAffiliateWizardForm):
    concentration = forms.ChoiceField(widget=forms.Select, choices=[(x,x) for x in BS_CONCENTRATIONS])
    custom_concentration = forms.CharField(required=False, label="Individually Designed Concentration")


class MastersSymsysAffiliateWizardForm(StudentSymsysAffiliateWizardForm):
    track = forms.ChoiceField(widget=forms.Select, choices=[(x,x) for x in MS_TRACKS])
    custom_track = forms.CharField(required=False, label="Individually Designed Track")


class FacultySymsysAffiliateWizardForm(SymsysAffiliateWizardForm):
    academic_title = forms.CharField()


class StaffSymsysAffiliateWizardForm(SymsysAffiliateWizardForm):
    admin_title = forms.CharField()
