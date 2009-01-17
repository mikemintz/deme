from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
from cms.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import datastructures, simplejson
import datetime
from cms.views import set_default_layout, error_response, get_viewer_class_for_viewer_name
import permissions
import os
import subprocess
from django.conf import settings

# Import viewers from modules
for module_name in settings.MODULE_NAMES:
    __import__('modules.%s.views' % module_name)


###############################################################################
# Helper functions
###############################################################################

def get_logged_in_agent(request):
    """
    Return the currently logged in Agent (based on the cur_agent_id parameter
    in request.session), or return the AnonymousAgent if the cur_agent_id is
    missing or invalid.
    
    Also update last_online_at for the resulting Agent to the current time.
    """
    cur_agent_id = request.session.get('cur_agent_id', None)
    cur_agent = None
    if cur_agent_id is not None:
        try:
            cur_agent = Agent.objects.get(pk=cur_agent_id).downcast()
        except ObjectDoesNotExist:
            if 'cur_agent_id' in request.session:
                del request.session['cur_agent_id']
    if not cur_agent:
        try:
            cur_agent = AnonymousAgent.objects.all()[0:1].get()
        except ObjectDoesNotExist:
            raise Exception("You must create an anonymous agent")
    Agent.objects.filter(pk=cur_agent.pk).update(last_online_at=datetime.datetime.now())
    return cur_agent


def get_current_site(request):
    """
    Return the Site that corresponds to the URL in the request, or return the
    default site (based on the DemeSetting cms.default_site) if no Site
    matches.
    """
    hostname = request.get_host().split(':')[0]
    try:
        return Site.objects.filter(site_domains__hostname=hostname)[0:1].get()
    except ObjectDoesNotExist:
        try:
            return Site.objects.get(pk=DemeSetting.get('cms.default_site'))
        except ObjectDoesNotExist:
            raise Exception("You must create a default Site")


###############################################################################
# Views
###############################################################################

def resource(request, *args, **kwargs):
    """
    This is the view that takes care of all valid URLs starting with
    "/resource/". It finds the appropriate viewer and dispatches the request
    to it.
    """
    cur_agent = get_logged_in_agent(request)
    cur_site = get_current_site(request)
    viewer_name = kwargs['viewer']
    action = kwargs.get('action')
    noun = kwargs.get('noun')
    format = kwargs.get('format')
    viewer_class = get_viewer_class_for_viewer_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_from_http(request, cur_agent, cur_site, action, noun, format)
        response = viewer.dispatch()
        if response is None:
            return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseNotFound,
                                  "Action Not Found", "We could not find any action matching your URL.")
        else:
            return response
    else:
        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseNotFound,
                              "Viewer Not Found", "We could not find any viewer matching your URL.")


def invalidurl(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs that don't match any expected
    pattern.
    """
    cur_agent = get_logged_in_agent(request)
    cur_site = get_current_site(request)
    return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseNotFound,
                          "Invalid URL", "The URL you typed in is invalid.")

def authenticate(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs starting with
    "/meta/authenticate".
    """
    cur_agent = get_logged_in_agent(request)
    cur_site = get_current_site(request)
    permission_cache = permissions.PermissionCache()
    if request.method == 'GET':
        # If getencryptionmethod is a key in the query string, return a JSON
        # response with the details about the PasswordAuthenticationMethod
        # necessary for JavaScript to encrypt the password.
        if 'getencryptionmethod' in request.GET:
            username = request.GET['getencryptionmethod']
            nonce = PasswordAuthenticationMethod.get_random_hash()[:5]
            request.session['login_nonce'] = nonce
            try:
                password = PasswordAuthenticationMethod.objects.get(username=username).password
                algo, salt, hsh = password.split('$')
                response_data = {'nonce':nonce, 'algo':algo, 'salt':salt}
            except ObjectDoesNotExist:
                response_data = {'nonce':nonce, 'algo':'sha1', 'salt':'x'}
            json_data = simplejson.dumps(response_data, separators=(',',':'))
            return HttpResponse(json_data, mimetype='application/json')
        # Otherwise, return the login.html page.
        else:
            login_as_agents = Agent.objects.filter(trashed=False).order_by('name')
            login_as_agents = login_as_agents.filter(permission_cache.filter_items(cur_agent, 'login_as'))
            permission_cache.mass_learn(cur_agent, 'view name', login_as_agents)
            template = loader.get_template('login.html')
            context = Context()
            context['redirect'] = request.GET['redirect']
            context['full_path'] = request.get_full_path()
            context['cur_agent'] = cur_agent
            context['cur_site'] = cur_site
            context['_permission_cache'] = permission_cache
            context['login_as_agents'] = login_as_agents
            set_default_layout(context)
            return HttpResponse(template.render(context))
    else:
        # The user just submitted a login form, so we try to authenticate.
        redirect = request.GET['redirect']
        login_type = request.POST['login_type']
        if login_type == 'logout':
            if 'cur_agent_id' in request.session:
                del request.session['cur_agent_id']
            return HttpResponseRedirect(redirect)
        elif login_type == 'password':
            nonce = request.session['login_nonce']
            del request.session['login_nonce']
            username = request.POST['username']
            hashed_password = request.POST['hashed_password']
            try:
                password_authentication_method = PasswordAuthenticationMethod.objects.get(username=username)
            except ObjectDoesNotExist:
                # No PasswordAuthenticationMethod has this username.
                return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                      "Authentication Failed", "There was a problem with your login form")
            if password_authentication_method.agent.trashed: 
                # The Agent corresponding to this PasswordAuthenticationMethod is trashed.
                return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                      "Authentication Failed", "There was a problem with your login form")
            if password_authentication_method.check_nonced_password(hashed_password, nonce):
                request.session['cur_agent_id'] = password_authentication_method.agent.pk
                return HttpResponseRedirect(redirect)
            else:
                # The password given does not correspond to the PasswordAuthenticationMethod.
                return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                      "Authentication Failed", "There was a problem with your login form")
        elif login_type == 'login_as':
            for key in request.POST.iterkeys():
                if key.startswith('login_as_'):
                    new_agent_id = key.split('login_as_')[1]
                    try:
                        new_agent = Agent.objects.get(pk=new_agent_id)
                    except ObjectDoesNotExist:
                        # There is no Agent with the specified id.
                        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                              "Authentication Failed", "There was a problem with your login form")
                    if new_agent.trashed:
                        # The specified agent is trashed.
                        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                              "Authentication Failed", "There was a problem with your login form")
                    if permission_cache.agent_can(cur_agent, 'login_as', new_agent):
                        request.session['cur_agent_id'] = new_agent.pk
                        return HttpResponseRedirect(redirect)
                    else:
                        # The current agent does not have permission to login_as the specified agent.
                        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                                              "Authentication Failed", "There was a problem with your login form")
        # Invalid login_type parameter.
        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseBadRequest,
                              "Authentication Failed", "There was a problem with your login form")

def codegraph(request, *args, **kwargs):
    """
    This is the view that takes care of "/meta/codegraph", displaying a graph
    of the Deme item type ontology.
    """
    cur_agent = get_logged_in_agent(request)
    cur_site = get_current_site(request)
    # If cms/models.py was modified after static/codegraph.png was,
    # re-render the graph before displaying this page.
    models_filename = os.path.join(os.path.dirname(__file__), 'models.py')
    codegraph_filename = os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph.png')
    models_mtime = os.stat(models_filename)[8]
    try:
        codegraph_mtime = os.stat(codegraph_filename)[8]
    except OSError, e:
        codegraph_mtime = 0
    if models_mtime > codegraph_mtime:
        subprocess.call(os.path.join(os.path.dirname(__file__), '..', 'script', 'gen_graph.py'), shell=True)
    template = loader.get_template_from_string("""
    {%% extends layout %%}
    {%% block title %%}Deme Code Graph{%% endblock %%}
    {%% block content %%}
    <div><a href="/static/codegraph.png?%d">Code graph</a></div>
    <div><a href="/static/codegraph_basic.png?%d">Code graph (basic)</a></div>
    {%% endblock %%}
    """ % (models_mtime, models_mtime))
    context = Context()
    context['cur_agent'] = cur_agent
    context['cur_site'] = cur_site
    context['full_path'] = request.get_full_path()
    context['_permission_cache'] = permissions.PermissionCache()
    set_default_layout(context)
    return HttpResponse(template.render(context))

def alias(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs other than those beginning
    with "/static/", "/meta/", "/resource/", and those URLs taken by modules.
    
    It checks all of the ViewerRequests to see if any match the current URL,
    and if so, simulates a request to the given viewer.
    """
    cur_agent = get_logged_in_agent(request)
    cur_site = get_current_site(request)
    path_parts = [x for x in request.path.split('/') if x] # Reduce consecutive slashes
    viewer_request = cur_site
    try:
        for path_part in path_parts:
            viewer_request = CustomUrl.objects.get(path=path_part, parent_url=viewer_request)
    except ObjectDoesNotExist:
        return error_response(cur_agent, cur_site, request.get_full_path(), HttpResponseNotFound,
                              "Alias Not Found", "We could not find any alias matching your URL http://%s%s." % (request.get_host(), request.path))
    item = viewer_request.aliased_item
    kwargs = {}
    kwargs['viewer'] = viewer_request.viewer
    kwargs['format'] = viewer_request.format
    if item:
        kwargs['noun'] = str(item.pk)
        kwargs['action'] = viewer_request.action
    else:
        kwargs['noun'] = None
        kwargs['action'] = viewer_request.action
    query_dict = QueryDict(viewer_request.query_string).copy()
    query_dict.update(request.GET)
    request.GET = query_dict
    # Set the REQUEST dict
    request._request = datastructures.MergeDict(request.POST, request.GET)
    return resource(request, **kwargs)

