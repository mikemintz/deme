"""
This module manages all of the views for items, viewer requests, and meta
URLs, and directs them to the proper viewer.
"""

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

