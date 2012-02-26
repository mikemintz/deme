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
from cms.base_viewer import get_viewer_class_by_name, get_current_site, all_viewer_classes
from django.conf import settings

# Check that all default viewers have been defined properly
for item_type in all_item_types():
    viewer_name = item_type.__name__.lower()
    viewer_class = get_viewer_class_by_name(viewer_name)
    if viewer_class is None:
        raise Exception("No default viewer defined for %s" % item_type)
    if viewer_class.accepted_item_type != item_type:
        raise Exception("Viewer with name `%s` has accepted_item_type=%s, should be %s"
                        % (viewer_name, viewer_class.accepted_item_type, item_type))

# Check that all viewers inherit from the correct superclasses
for viewer_class in all_viewer_classes():
    item_type = viewer_class.accepted_item_type
    if item_type != Item:
        desired_bases = item_type.__bases__
        actual_bases = tuple(base.accepted_item_type for base in viewer_class.__bases__)
        if desired_bases != actual_bases:
            raise Exception("Viewer with name `%s` has bases=%s, should be %s"
                            % (viewer_class.viewer_name, actual_bases, desired_bases))


def item_view(request, *args, **kwargs):
    """
    This is the view that takes care of all valid URLs starting with
    "/viewing/". It finds the appropriate viewer and dispatches the request
    to it.
    """
    viewer_name = kwargs['viewer']
    action = kwargs.get('action')
    noun = kwargs.get('noun')
    format = kwargs.get('format')
    viewer_class = get_viewer_class_by_name(viewer_name)
    if viewer_class:
        viewer = viewer_class()
        viewer.init_for_http(request, action, noun, format)
        response = viewer.dispatch()
        if response is None:
            response = viewer.render_error("Action Not Found", "We could not find any action matching your URL.", HttpResponseNotFound)
    else:
        viewer = ItemViewer()
        viewer.init_for_http(request, action, noun, format)
        response = viewer.render_error("Viewer Not Found", "We could not find any viewer matching your URL.", HttpResponseNotFound)
    return response


def alias_view(request, *args, **kwargs):
    """
    This is the view that takes care of all URLs other than those beginning
    with "/static/", "/viewing/", and those URLs taken by modules.
    
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
        url = 'http://%s%s' % (request.get_host(), request.path)
        return viewer.render_error("Page Not Found", "We could not find any page matching your URL %s" % url, HttpResponseNotFound)
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

