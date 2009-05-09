"""
This module manages all of the views for items and viewer requests (aliases),
and directs them to the proper viewer or renders an error for invalid URL.
"""

from django.http import HttpResponseNotFound
from cms.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import datastructures, simplejson
from cms.views import ItemViewer
from cms.base_viewer import get_viewer_class_for_viewer_name, get_current_site
from django.conf import settings

# Import viewers from modules so they get registered with ViewerMetaClass
for module_name in settings.MODULE_NAMES:
    __import__('modules.%s.views' % module_name)


def item_view(request, *args, **kwargs):
    """
    This is the view that takes care of all valid URLs starting with
    "/item/". It finds the appropriate viewer and dispatches the request
    to it.
    """
    viewer_name = kwargs['viewer']
    action = kwargs.get('action')
    noun = kwargs.get('noun')
    format = kwargs.get('format')
    viewer_class = get_viewer_class_for_viewer_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_for_http(request, action, noun, format)
        response = viewer.dispatch()
        if response is None:
            return viewer.render_error(HttpResponseNotFound, "Action Not Found", "We could not find any action matching your URL.")
        else:
            return response
    else:
        viewer = ItemViewer()
        viewer.init_for_http(request, action, noun, format)
        return viewer.render_error(HttpResponseNotFound, "Viewer Not Found", "We could not find any viewer matching your URL.")


def invalid_url_view(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs that don't match any expected
    pattern.
    """
    viewer = ItemViewer()
    viewer.init_for_http(request, 'error', None, 'html')
    return viewer.render_error(HttpResponseNotFound, "Invalid URL", "The URL you typed in is invalid.")


def alias_view(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs other than those beginning
    with "/static/", "/item/", and those URLs taken by modules.
    
    It checks all of the ViewerRequests to see if any match the current URL,
    and if so, simulates a request to the given viewer.
    """
    cur_site = get_current_site(request)
    path_parts = [x for x in request.path.split('/') if x] # Reduce consecutive slashes
    viewer_request = cur_site
    try:
        for path_part in path_parts:
            viewer_request = CustomUrl.objects.get(path=path_part, parent_url=viewer_request)
    except ObjectDoesNotExist:
        viewer = ItemViewer()
        viewer.init_for_http(request, 'error', None, 'html')
        return viewer.render_error(HttpResponseNotFound, "Alias Not Found",
                                   "We could not find any alias matching your URL http://%s%s." % (request.get_host(), request.path))
    item = viewer_request.aliased_item
    kwargs = {}
    kwargs['viewer'] = viewer_request.viewer
    kwargs['format'] = viewer_request.format
    kwargs['action'] = viewer_request.action
    kwargs['noun'] = str(item.pk) if item else None
    query_dict = QueryDict(viewer_request.query_string).copy()
    query_dict.update(request.GET)
    request.GET = query_dict
    # Set the REQUEST dict
    request._request = datastructures.MergeDict(request.POST, request.GET)
    return item_view(request, **kwargs)

