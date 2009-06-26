#TODO completely clean up code

from django.http import HttpResponse, HttpResponseRedirect
from cms.views import AuthenticationMethodViewer
from modules.demeaccount.models import DemeAccount
from django.template import loader
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import simplejson
from django.views.decorators.http import require_POST

class DemeAccountViewer(AuthenticationMethodViewer):
    accepted_item_type = DemeAccount
    viewer_name = 'demeaccount'

    @require_POST
    def type_login_html(self):
        redirect = self.request.GET['redirect']
        nonce = self.request.session['login_nonce']
        del self.request.session['login_nonce']
        username = self.request.POST['username']
        hashed_password = self.request.POST['hashed_password']
        try:
            password_authentication_method = DemeAccount.objects.get(username=username, active=True, agent__active=True)
        except ObjectDoesNotExist:
            # No active DemeAccount has this username.
            return self.render_error("Authentication Failed", "Invalid username/password")
        if password_authentication_method.check_nonced_password(hashed_password, nonce):
            self.request.session['cur_agent_id'] = password_authentication_method.agent.pk
            full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
            return HttpResponseRedirect(full_redirect)
        else:
            # The password given does not correspond to the DemeAccount.
            return self.render_error("Authentication Failed", "Invalid username/password")

    def type_getencryptionmethod_html(self):
        # Return a JSON response with the details about the DemeAccount
        # necessary for JavaScript to encrypt the password.
        username = self.request.GET['username']
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
        template = loader.get_template('demeaccount/loginmenuitem.html')
        return HttpResponse(template.render(self.context))

