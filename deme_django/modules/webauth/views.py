from django.http import HttpResponse, HttpResponseRedirect
from cms.views import AuthenticationMethodViewer
from cms.models import *
from modules.webauth.models import *
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist

class WebauthAccountViewer(AuthenticationMethodViewer):
    accepted_item_type = WebauthAccount
    viewer_name = 'webauthaccount'

    def type_login_html(self):
        # We must be using SSL for WebAuth to work
        if not self.request.is_secure():
            return HttpResponseRedirect('https://%s%s' % (self.request.get_host(), self.request.get_full_path()))

        # Assert that the proper environment variables are set
        if self.request.META.get('AUTH_TYPE') != 'WebAuth' or not self.request.META.get('REMOTE_USER'):
            return self.render_error("WebAuth Error", "WebAuth is not supported in this installation")

        # Find the WebauthAccount
        username = self.request.META['REMOTE_USER']
        try:
            webauth_account = WebauthAccount.objects.get(username=username, active=True, agent__active=True)
        except ObjectDoesNotExist:
            return self.render_error("WebAuth Error", "There is no active agent with that webauth username")

        # Record the user's login in the session
        self.request.session['cur_agent_id'] = webauth_account.agent.pk

        # Redirect the browser to the loggedinorout page
        redirect = self.request.GET['redirect']
        full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
        return HttpResponseRedirect(full_redirect)

    def type_loginmenuitem_html(self):
        if self.cur_agent.is_anonymous():
            login_url = reverse('item_type_url', kwargs={'viewer': 'webauthaccount', 'action': 'login'})
            if 'redirect' in self.request.GET:
                login_url += '?redirect=%s' % urlquote(self.request.GET['redirect'])
            result = '<li class="loginmenuitem"><a href="%s">Webauth</a></li>' % login_url
        else:
            result = ''
        return HttpResponse(result)

