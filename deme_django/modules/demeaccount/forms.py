from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from cms.models import EmailContactMethod
from .models import DemeAccount


class DemeAccountForgotForm(forms.Form):
    username_or_email = forms.CharField(label="Email address or username")

    # http://ruddra.com/2015/09/18/implementation-of-forgot-reset-password-feature-in-django/
    @staticmethod
    def validate_email_address(email):
        '''
        This method here validates the if the input is an email address or not. Its return type is boolean, True if the input is a email address or False if its not.
        '''
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    def clean(self):
        cleaned_data = super(DemeAccountForgotForm, self).clean()
        data = cleaned_data['username_or_email']

        demeaccounts = []
        to = [] # email we are sending to

        if self.validate_email_address(data):
            # if data looks like an email, try finding associated accounts
            to.append(data)
            emails = EmailContactMethod.objects.filter(email=data, active=True)
            for email in emails:
                # attempt to find a matching DemeAccount via email
                for auth_method in email.agent.authentication_methods.filter(active=True, demeaccount__isnull=False):
                    demeaccounts.append(auth_method.demeaccount)

        # Look for account based on username (even if it looked like an email)
        try:
            demeaccount = DemeAccount.objects.get(username=data, active=True)
            if demeaccount not in demeaccounts:
                demeaccounts.append(demeaccount)

            if not to:
                # if we don't have an email
                methods = demeaccount.agent.contact_methods.filter(active=True, emailcontactmethod__isnull=False)
                for method in methods:
                    to.append(method.emailcontactmethod.email)

        except DemeAccount.DoesNotExist:
            pass

        # Don't reveal whether or not there is an account
        # if len(to) == 0 or len(demeaccounts) == 0:
        #     raise forms.ValidationError("Sorry, but we cannot find an account with that username or email address")

        cleaned_data['to'] = to
        cleaned_data['demeaccounts'] = demeaccounts
        return cleaned_data
