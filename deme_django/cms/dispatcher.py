from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
from cms.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import datastructures, simplejson
import datetime
from cms.views import set_default_layout, get_viewer_class_for_viewer_name
import permissions
import os
import subprocess
from django.conf import settings

# import module viewers
for module_name in settings.MODULE_NAMES:
    __import__('modules.%s.views' % module_name)


### HELPER FUNCTIONS ###

def render_error(cur_agent, current_site, full_path, request_class, title, body):
    template = loader.get_template_from_string("""
    {%% extends layout %%}
    {%% load resource_extras %%}
    {%% block favicon %%}{{ "error"|icon_url:16 }}{%% endblock %%}
    {%% block title %%}<img src="{{ "error"|icon_url:48 }}" /> %s{%% endblock %%}
    {%% block content %%}%s{%% endblock content %%}
    """ % (title, body))
    context = Context()
    context['cur_agent'] = cur_agent
    context['full_path'] = full_path
    context['_permission_cache'] = permissions.PermissionCache()
    set_default_layout(context, current_site, cur_agent)
    return request_class(template.render(context))

def get_logged_in_agent(request):
    cur_agent_id = request.session.get('cur_agent_id', None)
    cur_agent = None
    if cur_agent_id != None:
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
    hostname = request.META['HTTP_HOST'].split(':')[0]
    try:
        return Site.objects.filter(site_domains_as_site__hostname=hostname)[0:1].get()
    except ObjectDoesNotExist:
        try:
            return Site.objects.get(pk=DemeSetting.get('cms.default_site'))
        except ObjectDoesNotExist:
            raise Exception("You must create a default Site")


### VIEWS ###

def resource(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    current_site = get_current_site(request)
    viewer_name = kwargs['viewer']
    viewer_class = get_viewer_class_for_viewer_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_from_http(request, cur_agent, current_site, kwargs)
        response = viewer.dispatch()
        if response == None:
            return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseNotFound, "Action Not Found", "We could not find any action matching your URL.")
        else:
            return response
    else:
        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseNotFound, "Viewer Not Found", "We could not find any viewer matching your URL.")


def invalidurl(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    current_site = get_current_site(request)
    return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseNotFound, "Invalid URL", "The URL you typed in is invalid.")

def authenticate(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    current_site = get_current_site(request)
    permission_cache = permissions.PermissionCache()
    if request.method == 'GET':
        if 'getencryptionmethod' in request.GET:
            nonce = get_random_hash()[:5]
            try:
                password_authentication_method = PasswordAuthenticationMethod.objects.get(username=request.GET['getencryptionmethod'])
                algo, salt, hsh = password_authentication_method.password.split('$')
                json_data = simplejson.dumps({'nonce':nonce, 'algo':algo, 'salt':salt}, separators=(',',':'))
            except:
                json_data = simplejson.dumps({'nonce':nonce, 'algo':'sha1', 'salt':'x'}, separators=(',',':'))
            request.session['login_nonce'] = nonce
            return HttpResponse(json_data, mimetype='application/json')
        else:
            template = loader.get_template('login.html')
            context = Context()
            context['redirect_url'] = request.GET['redirect']
            context['full_path'] = request.get_full_path()
            context['cur_agent'] = cur_agent
            context['_permission_cache'] = permission_cache
            if permission_cache.agent_can_global(cur_agent, 'do_everything'):
                context['login_as_agents'] = Agent.objects.filter(trashed=False).order_by('name')
            else:
                context['login_as_agents'] = Agent.objects.filter(trashed=False).filter(permissions.filter_items_by_permission(cur_agent, 'login_as')).order_by('name')
                context['_permission_cache'].mass_learn(cur_agent, 'view name', context['login_as_agents'])
            set_default_layout(context, current_site, cur_agent)
            return HttpResponse(template.render(context))
    else:
        redirect_url = request.GET['redirect']
        login_type = request.POST['login_type']
        if login_type == 'logout':
            if 'cur_agent_id' in request.session:
                del request.session['cur_agent_id']
            return HttpResponseRedirect(redirect_url)
        elif login_type == 'password':
            nonce = request.session['login_nonce']
            del request.session['login_nonce']
            username = request.POST['username']
            hashed_password = request.POST['hashed_password']
            try:
                password_authentication_method = PasswordAuthenticationMethod.objects.get(username=username)
            except ObjectDoesNotExist:
                return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Invalid Username", "No person has this username")
            if password_authentication_method.agent.trashed: 
                return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Trashed Agent", "The agent you are trying to log in as is trashed")
            if password_authentication_method.check_nonced_password(hashed_password, nonce):
                new_agent = password_authentication_method.agent
                request.session['cur_agent_id'] = new_agent.pk
                return HttpResponseRedirect(redirect_url)
            else:
                return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Invalid Password", "The password you typed was not correct for this username")
        elif login_type == 'login_as':
            for key in request.POST.iterkeys():
                if key.startswith('login_as_'):
                    new_agent_id = key.split('login_as_')[1]
                    try:
                        new_agent = Agent.objects.get(pk=new_agent_id)
                    except ObjectDoesNotExist:
                        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Invalid Agent ID", "There is no agent with the id you specified")
                    if new_agent.trashed:
                        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Trashed Agent", "The agent you are trying to log in as is trashed")
                    if permission_cache.agent_can(cur_agent, 'login_as', new_agent):
                        request.session['cur_agent_id'] = new_agent.pk
                        return HttpResponseRedirect(redirect_url)
                    else:
                        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Permission Denied", "You do not have permission to login as this agent")
        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseBadRequest, "Invalid Login Request", "The login_type field on your form was invalid")

def codegraph(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    current_site = get_current_site(request)
    models_filename = os.path.join(os.path.dirname(__file__), 'models.py')
    codegraph_filename = os.path.join(os.path.dirname(__file__), '..', 'static', 'codegraph.png')
    models_mtime = os.stat(models_filename)[8]
    try:
        codegraph_mtime = os.stat(codegraph_filename)[8]
    except OSError, e:
        codegraph_mtime = 0
    if models_mtime > codegraph_mtime:
        subprocess.call(os.path.join(os.path.dirname(__file__), '..', 'gen_graph.py'), shell=True)
    template = loader.get_template_from_string("""
    {%% extends layout %%}
    {%% block title %%}Deme Code Graphs{%% endblock %%}
    {%% block content %%}
    <div><a href="/static/codegraph.png?%d">Code graph</a></div>
    <div><a href="/static/codegraph_basic.png?%d">Code graph (basic)</a></div>
    {%% endblock %%}
    """ % (models_mtime, models_mtime))
    context = Context()
    context['cur_agent'] = cur_agent
    context['full_path'] = request.get_full_path()
    context['_permission_cache'] = permissions.PermissionCache()
    set_default_layout(context, current_site, cur_agent)
    return HttpResponse(template.render(context))

def alias(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    current_site = get_current_site(request)
    path_parts = [x for x in request.path.split('/') if x]
    custom_url = current_site
    try:
        for path_part in path_parts:
            custom_url = CustomUrl.objects.filter(path=path_part, parent_url=custom_url)[0:1].get()
    except ObjectDoesNotExist:
        return render_error(cur_agent, current_site, request.get_full_path(), HttpResponseNotFound, "Alias Not Found", "We could not find any alias matching your URL http://%s%s." % (request.META['HTTP_HOST'], request.path))
    item = custom_url.aliased_item
    kwargs = {}
    kwargs['viewer'] = custom_url.viewer
    kwargs['format'] = custom_url.format
    if item:
        kwargs['noun'] = str(item.pk)
        kwargs['action'] = custom_url.action
    else:
        kwargs['noun'] = None
        kwargs['action'] = custom_url.action
    query_dict = QueryDict(custom_url.query_string).copy()
    query_dict.update(request.GET)
    request.GET = query_dict
    request._request = datastructures.MergeDict(request.POST, request.GET)
    return resource(request, **kwargs)

