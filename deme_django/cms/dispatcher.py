from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
import cms.models
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import datastructures
import datetime

from cms.views import *
import permission_functions

# import module viewers
import os
modules_dir = os.path.join(os.path.dirname(__file__), '..', 'modules')
for module_name in os.listdir(modules_dir):
    if module_name.startswith('.'):
        continue
    if module_name.startswith('_'):
        continue
    __import__('modules.%s.views' % module_name)


### HELPER FUNCTIONS ###

def get_logged_in_agent(request):
    cur_agent_id = request.session.get('cur_agent_id', None)
    cur_agent = None
    if cur_agent_id != None:
        try:
            cur_agent = cms.models.Agent.objects.get(pk=cur_agent_id).downcast()
        except ObjectDoesNotExist:
            if 'cur_agent_id' in request.session:
                del request.session['cur_agent_id']
    if not cur_agent:
        try:
            cur_agent = cms.models.AnonymousAgent.objects.all()[0:1].get()
        except ObjectDoesNotExist:
            raise Exception("You must create an anonymous account")
    cms.models.Agent.objects.filter(pk=cur_agent.pk).update(last_online_at=datetime.datetime.now())
    return cur_agent


### VIEWS ###

def resource(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    viewer_name = kwargs['viewer']
    viewer_class = get_viewer_class_for_viewer_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_from_http(request, cur_agent, kwargs)
        response = viewer.dispatch()
        if response == None:
            template = loader.get_template('action_not_found.html')
            context = Context()
            context['layout'] = 'base.html'
            context['cur_agent'] = cur_agent
            return HttpResponseNotFound(template.render(context))
        else:
            return response
    else:
        template = loader.get_template('viewer_not_found.html')
        context = Context()
        context['layout'] = 'base.html'
        context['cur_agent'] = cur_agent
        return HttpResponseNotFound(template.render(context))


def invalidresource(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    template = loader.get_template('invalid_resource_url.html')
    context = Context()
    context['layout'] = 'base.html'
    context['cur_agent'] = cur_agent
    return HttpResponseNotFound(template.render(context))

def login(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(cur_agent)
    if request.method == 'GET':
        template = loader.get_template('login.html')
        context = Context()
        context['layout'] = 'base.html'
        context['redirect_url'] = request.GET['redirect']
        context['full_path'] = request.get_full_path()
        context['cur_agent'] = cur_agent
        if can_do_everything:
            context['login_as_agents'] = [x for x in cms.models.Agent.objects.all()]
        else:
            context['login_as_agents'] = [x for x in cms.models.Agent.objects.filter(permission_functions.filter_for_agent_and_ability(cur_agent, 'login_as', 'id'))]#.distinct()] TODO don't need this?
        return HttpResponse(template.render(context))
    else:
        redirect_url = request.GET['redirect']
        login_type = request.POST['login_type']
        if login_type == 'password':
            email = request.POST['email']
            password = request.POST['password']
            try:
                person = cms.models.Person.objects.get(email=email)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest('no person has that email')
            new_account = None
            for password_account in cms.models.PasswordAccount.objects.filter(agent=person).all():
                if password_account.check_password(password):
                    new_account = password_account
                    break
            if new_account:
                new_agent = new_account.agent
                request.session['cur_agent_id'] = new_agent.pk
                return HttpResponseRedirect(redirect_url)
            else:
                return HttpResponseBadRequest('no account for that person has that password')
        elif login_type == 'login_as':
            for key in request.POST.iterkeys():
                if key.startswith('login_as_'):
                    new_agent_id = key.split('login_as_')[1]
                    try:
                        new_agent = cms.models.Agent.objects.get(pk=new_agent_id)
                    except ObjectDoesNotExist:
                        return HttpResponseBadRequest('invalid agent id')
                    if can_do_everything or ('login_as', 'id') in permission_functions.get_abilities_for_agent_and_item(cur_agent, new_agent):
                        request.session['cur_agent_id'] = new_agent.pk
                        return HttpResponseRedirect(redirect_url)
                    else:
                        return HttpResponseBadRequest('you do not have permission to login as this agent')
            return HttpResponseBadRequest('invalid login request')

def logout(request, *args, **kwargs):
    redirect_url = request.GET['redirect']
    if 'cur_agent_id' in request.session:
        del request.session['cur_agent_id']
    return HttpResponseRedirect(redirect_url)

def codegraph(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    import os
    import subprocess
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
        {%% extends 'base.html' %%}
        {%% block title %%}Deme Code Graphs{%% endblock %%}
        {%% block content %%}
        <div><a href="/static/codegraph.png?%d">Code graph</a></div>
        <div><a href="/static/codegraph_basic.png?%d">Code graph (basic)</a></div>
        {%% endblock %%}
    """ % (models_mtime, models_mtime))
    context = Context()
    context['cur_agent'] = cur_agent
    return HttpResponse(template.render(context))

def alias(request, *args, **kwargs):
    cur_agent = get_logged_in_agent(request)
    hostname = request.META['HTTP_HOST'].split(':')[0]
    try:
        current_site = cms.models.Site.objects.filter(site_domains_as_site__hostname=hostname)[0:1].get()
    except ObjectDoesNotExist:
        try:
            current_site = cms.models.Site.objects.filter(is_default_site=True)[0:1].get()
        except ObjectDoesNotExist:
            raise Exception("You must create a default Site")
            current_site = None
    path_parts = [x for x in request.path.split('/') if x]
    custom_url = current_site
    try:
        for path_part in path_parts:
            custom_url = cms.models.CustomUrl.objects.filter(path=path_part, parent_url=custom_url)[0:1].get()
    except ObjectDoesNotExist:
        template = loader.get_template('alias_not_found.html')
        context = Context()
        context['layout'] = 'base.html'
        context['hostname'] = request.META['HTTP_HOST']
        context['path'] = request.path
        context['cur_agent'] = cur_agent
        return HttpResponseNotFound(template.render(context))
    if not custom_url:
        raise Exception("we should never get here 23942934")
    item = custom_url.aliased_item
    kwargs = {}
    kwargs['viewer'] = custom_url.viewer
    kwargs['format'] = 'html'
    if item:
        kwargs['noun'] = str(item.pk)
        kwargs['collection_action'] = None
        kwargs['entry_action'] = custom_url.action
    else:
        kwargs['noun'] = None
        kwargs['collection_action'] = custom_url.action
        kwargs['entry_action'] = None
    query_dict = QueryDict(custom_url.query_string).copy()
    #TODO this is quite hacky, let's fix this when we finalize sites and stuff
    query_dict.update(request.GET)
    request.GET = query_dict
    request._request = datastructures.MergeDict(request.POST, request.GET)
    return resource(request, **kwargs)

