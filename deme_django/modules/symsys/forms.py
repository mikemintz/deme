from django import forms
from modules.symsys.models import BS_CONCENTRATIONS
from modules.demeaccount.models import DemeAccount

class SymsysAffiliateWizardForm(forms.Form):
    first_name = forms.CharField()
    middle_names = forms.CharField(required=False)
    last_name = forms.CharField()
    suid = forms.IntegerField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    concentration = forms.ChoiceField(widget=forms.Select, choices=[(x,x) for x in BS_CONCENTRATIONS])
    declaration_date = forms.DateField(help_text="As MM/DD/YYYY")
    class_year = forms.IntegerField(min_value=1900, max_value=9999, help_text="As YYYY") # not 10k proof
    # TODO: image

    def clean_email(self):
        data = self.cleaned_data['email']
        try:
            DemeAccount.objects.get(username=data)
            raise forms.ValidationError("This email is already associated with a user")
        except DemeAccount.DoesNotExist:
            return data
