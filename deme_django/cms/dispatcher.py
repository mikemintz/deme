from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
import cms.models
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import datastructures

from cms.views import *

# import module viewers
import os
modules_dir = os.path.join(os.path.dirname(__file__), '..', 'modules')
for module_name in os.listdir(modules_dir):
    if module_name.startswith('.'):
        continue
    if module_name.startswith('_'):
        continue
    __import__('modules.%s.views' % module_name)

### VIEWS ###

def resource(request, *args, **kwargs):
    viewer_name = kwargs['viewer']
    viewer_class = get_viewer_class_for_viewer_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_from_http(request, kwargs)
        response = viewer.dispatch()
        if response == None:
            template = loader.get_template('action_not_found.html')
            context = Context()
            context['layout'] = 'base.html'
            return HttpResponseNotFound(template.render(context))
        else:
            return response
    else:
        template = loader.get_template('viewer_not_found.html')
        context = Context()
        context['layout'] = 'base.html'
        return HttpResponseNotFound(template.render(context))


def invalidresource(request, *args, **kwargs):
    template = loader.get_template('invalid_resource_url.html')
    context = Context()
    context['layout'] = 'base.html'
    return HttpResponseNotFound(template.render(context))

def login(request, *args, **kwargs):
    redirect_url = request.GET['redirect']
    account_unique_id = request.GET['account']
    account = cms.models.Account.objects.get(pk=account_unique_id)
    request.session['account_unique_id'] = account.pk
    return HttpResponseRedirect(redirect_url)

def logout(request, *args, **kwargs):
    redirect_url = request.GET['redirect']
    if 'account_unique_id' in request.session:
        del request.session['account_unique_id']
    return HttpResponseRedirect(redirect_url)

def codegraph(request, *args, **kwargs):
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
    return HttpResponse(template.render(context))

def alias(request, *args, **kwargs):
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

