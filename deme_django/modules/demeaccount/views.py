#TODO completely clean up code

from django.http import HttpResponse, HttpResponseRedirect
from cms.views import AuthenticationMethodViewer
from modules.demeaccount.models import DemeAccount
from django.template import loader, Context
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import simplejson, timezone
from django.views.decorators.http import require_POST
from .forms import DemeAccountForgotForm
import html2text
from django.utils.text import wrap
from django.core.mail import EmailMultiAlternatives
from cms.base_viewer import get_current_site
from django.utils.http import base36_to_int
from django.contrib import messages


class DemeAccountViewer(AuthenticationMethodViewer):
    accepted_item_type = DemeAccount
    viewer_name = 'demeaccount'

    def send_reset_password_email(self, emails, demeaccounts):
        if len(emails) > 0 or len(demeaccounts) > 0:
            site = get_current_site(self.request)
            title = site.title
            if not title:
                title = "Deme account"
            subject = "Reset your %s password" % (title) # TODO: customize the site name
            headers = {}
            context = Context({
                "emails": emails,
                "demeaccounts": demeaccounts,
                "url_prefix": 'http://%s' % settings.DEFAULT_HOSTNAME
            })
            template = loader.get_template("demeaccount/notification/forgot_email.html")
            body_html = template.render(context)
            body_text = html2text.html2text_file(body_html, None)
            body_text = wrap(body_text, 78)
            from_email = '%s@%s' % ('noreply', settings.NOTIFICATION_EMAIL_HOSTNAME)
            email_message = EmailMultiAlternatives(subject, body_text, from_email, bcc=emails, headers=headers)
            email_message.attach_alternative(body_html, 'text/html')
            email_message.send()

    def login_user(self, demeaccount, redirect):
        # Save last login information to DemeAccount
        demeaccount.last_login = timezone.now()
        demeaccount.save(update_fields=['last_login'])
        self.request.session['cur_agent_id'] = demeaccount.agent.pk
        return HttpResponseRedirect(redirect)

    def type_forgot_html(self):
        self.context['action_title'] = 'Reset your password?'
        if self.request.method == "POST":
            form = DemeAccountForgotForm(self.request.POST)
            if form.is_valid():
                to = form.cleaned_data['to']
                demeaccounts = form.cleaned_data['demeaccounts']

                self.send_reset_password_email(to, demeaccounts)
                self.context['form_success'] = 'If you have a valid account and email, you should soon be receiving a password reset code.'

        else:
            form = DemeAccountForgotForm()

        template = loader.get_template('demeaccount/forgot.html')
        self.context['form'] = form
        return HttpResponse(template.render(self.context))

    def type_reset_html(self):
        # check token if set
        token = self.request.GET.get('token')
        uid36 = self.request.GET.get('uid')
        if uid36 and token:
            uid = base36_to_int(uid36)
            account = DemeAccount.objects.get(pk=uid)
            valid = account.check_token(token)
            if valid:
                # add a message
                messages.add_message(self.request, messages.INFO, "Login Successful")
                # login and take to edit page
                account_url = reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': account.pk, 'action': 'edit'})
                return self.login_user(account, account_url)

        messages.add_message(self.request, messages.WARNING, "Password reset code invalid. Please try again")

        # redirect if fail
        return HttpResponseRedirect(reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'forgot'}))


    @require_POST
    def type_login_html(self):
        redirect = self.request.GET['redirect']
        nonce = self.request.session['login_nonce']
        del self.request.session['login_nonce']
        username = self.request.POST['username']
        hashed_password = self.request.POST['hashed_password']
        try:
            demeaccount = DemeAccount.objects.get(username=username, active=True, agent__active=True)
            if demeaccount.check_nonced_password(hashed_password, nonce):
                full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
                return self.login_user(demeaccount, full_redirect)
        except ObjectDoesNotExist:
            # No active DemeAccount has this username.
            pass

        return self.render_error("Authentication Failed", "Invalid username/password")

    def type_getencryptionmethod_html(self):
        # Return a JSON response with the details about the DemeAccount
        # necessary for JavaScript to encrypt the password.
        username = self.request.POST['username']
        nonce = DemeAccount.get_random_hash()[:5]
        self.request.session['login_nonce'] = nonce
        try:
            password = DemeAccount.objects.get(username=username).password
            algo, salt, hsh = password.split('$')
            response_data = {'nonce':nonce, 'algo':algo, 'salt':salt}
        except ObjectDoesNotExist:
            # We need a fake salt so it looks like the account could exist
            salt = DemeAccount.get_hexdigest('sha1', username, settings.SECRET_KEY)[:5]
            response_data = {'nonce':nonce, 'algo':'sha1', 'salt':salt}
        json_data = simplejson.dumps(response_data, separators=(',',':'))
        return HttpResponse(json_data, mimetype='application/json')

    def type_loginmenuitem_html(self):
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('demeaccount/loginmenuitem.html')
        auth_methods = DemeAccount.objects.filter(agent=self.cur_agent)
        num_auth_methods = auth_methods.count()

        one_or_more = True
        two_or_more = True
        if num_auth_methods == 0:
            one_or_more = False
            two_or_more = False
        if num_auth_methods == 1:
            two_or_more = False

        self.context['auth_methods'] = auth_methods
        self.context['one_or_more'] = one_or_more
        self.context['two_or_more'] = two_or_more
        return HttpResponse(template.render(self.context))

