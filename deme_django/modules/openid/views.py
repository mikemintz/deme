from django.template import Context, loader
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from cms.views import AuthenticationMethodViewer
from cms.models import *
from modules.openid.models import *
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist

class OpenidAccountViewer(AuthenticationMethodViewer):
    accepted_item_type = OpenidAccount
    viewer_name = 'openidaccount'

    def type_login_html(self):
        redirect = self.request.GET['redirect']
        try:
            import openid.consumer.consumer
        except ImportError:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID is not supported in this installation")
        trust_root = self.request.build_absolute_uri('/')
        full_redirect_path = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'logincomplete'}), urlquote(redirect))
        full_redirect_url = self.request.build_absolute_uri(full_redirect_path)
        user_url = self.request.POST['openid_url']
        consumer = openid.consumer.consumer.Consumer(self.request.session, None)
        try:
            auth_request = consumer.begin(user_url)
        except openid.consumer.consumer.DiscoveryFailure:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "Invalid OpenID URL")
        auth_request.addExtensionArg('sreg', 'optional', 'nickname,email,fullname')
        return HttpResponseRedirect(auth_request.redirectURL(trust_root, full_redirect_url))

    def type_logincomplete_html(self):
        redirect = self.request.GET['redirect']
        try:
            import openid.consumer.consumer
        except ImportError:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID is not supported in this installation")
        consumer = openid.consumer.consumer.Consumer(self.request.session, None)
        query_dict = dict((k,v) for k,v in self.request.GET.items())
        current_url = self.request.build_absolute_uri().split('?')[0]
        openid_response = consumer.complete(query_dict, current_url)
        
        if openid_response.status == openid.consumer.consumer.SUCCESS:
            identity_url = openid_response.identity_url
            identity_url_without_fragment = identity_url.split('#')[0]
            # If we want to use display_identifier, we need to have python-openid >=2.1, which isn't in Ubuntu Hardy
            #display_identifier = openid_response.getDisplayIdentifier()
            sreg = openid_response.extensionResponse('sreg', False)
            try:
                openid_authentication_method = OpenidAccount.objects.get(Q(openid_url=identity_url_without_fragment) | Q(openid_url__startswith=identity_url_without_fragment + '#'))
            except ObjectDoesNotExist:
                # No OpenidAccount has this openid_url.
                return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that OpenID (1)")
            if not openid_authentication_method.active or not openid_authentication_method.agent.active: 
                # The Agent or OpenidAccount is inactive.
                return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that OpenID (2)")
            self.request.session['cur_agent_id'] = openid_authentication_method.agent.pk
            full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
            return HttpResponseRedirect(full_redirect)
        elif openid_response.status == openid.consumer.consumer.CANCEL:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID request was cancelled")
        elif openid_response.status == openid.consumer.consumer.FAILURE:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID error: %s" % escape(openid_response.message))
        elif openid_response.status == openid.consumer.consumer.SETUP_NEEDED:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID setup needed")
        else:
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "Invalid OpenID status: %s" % escape(openid_response.status))

