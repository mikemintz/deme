#TODO completely clean up code

from django.http import HttpResponseRedirect, HttpResponseBadRequest
from cms.views import AuthenticationMethodViewer
from cms.models import *
from modules.webauth.models import *
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist

class WebauthAccountViewer(AuthenticationMethodViewer):
    accepted_item_type = WebauthAccount
    viewer_name = 'webauth'

    def type_login_html(self):
        if not self.request.is_secure():
            return HttpResponseRedirect('https://%s%s' % (self.request.get_host(), self.request.get_full_path()))
        if self.request.META.get('AUTH_TYPE') != 'WebAuth' or not self.request.META.get('REMOTE_USER'):
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "WebAuth is not supported in this installation")
        username = self.request.META['REMOTE_USER']
        try:
            webauth_authentication_method = WebauthAccount.objects.get(username=username)
        except ObjectDoesNotExist:
            # No WebauthAccount has this username.
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that webauth username")
        if not webauth_authentication_method.active or not webauth_authentication_method.agent.active: 
            # The Agent or WebauthAccount is inactive.
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that webauth username")
        self.request.session['cur_agent_id'] = webauth_authentication_method.agent.pk
        redirect = self.request.GET['redirect']
        full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
        return HttpResponseRedirect(full_redirect)

