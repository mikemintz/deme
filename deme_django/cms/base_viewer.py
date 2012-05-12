"""
This module defines the abstract Viewer superclass of all item viewers.
"""

from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpRequest, QueryDict
from django.utils.datastructures import MergeDict
from django.template import Context, loader
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django import forms
from datetime import datetime
from cms.permissions import MultiAgentPermissionCache
from cms.forms import AjaxModelChoiceField
from django.utils.text import get_text_list, capfirst
from django.utils.safestring import mark_safe
from django.utils.html import escape
from urllib import urlencode
from cms.models import Item, Agent, Site, AnonymousAgent, DemeSetting, friendly_name_for_ability


###############################################################################
# Helper functions that don't require a Viewer
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
            cur_agent = Agent.objects.get(active=True, pk=cur_agent_id).downcast()
        except ObjectDoesNotExist:
            if 'cur_agent_id' in request.session:
                del request.session['cur_agent_id']
    if not cur_agent:
        try:
            cur_agent = AnonymousAgent.objects.filter(active=True)[0:1].get()
        except ObjectDoesNotExist:
            raise Exception("You must create an anonymous agent")
    Agent.objects.filter(pk=cur_agent.pk).update(last_online_at=datetime.now())
    return cur_agent


def get_default_site():
    """
    Return the default site, or raise an Exception if there is none.
    """
    try:
        return Site.objects.get(pk=DemeSetting.get('cms.default_site'))
    except ObjectDoesNotExist:
        raise Exception("You must create a default Site")


def get_current_site(request):
    """
    Return the Site that corresponds to the URL in the request, or return the
    default site (based on the DemeSetting cms.default_site) if no Site
    matches.
    """
    hostname = request.get_host().split(':')[0]
    try:
        return Site.objects.filter(hostname=hostname).get()
    except ObjectDoesNotExist:
        return get_default_site()


###############################################################################
# Classes that are used by Viewers
###############################################################################

class DemePermissionDenied(Exception):
    def __init__(self, ability, item):
        self.ability = ability
        self.item = item
        super(DemePermissionDenied, self).__init__("The agent does not have permission to perform the action")


class VirtualRequest(HttpRequest):
    """
    A VirtualRequest is used to simulate the rendering of a page when it was
    not itself initiated from an HTTP connection. This is particularly useful in
    embedding viewers within other viewers. VirtualRequest requires an
    `original_request` HttpRequest that is used to keep track of where it is
    being embedded.
    
    VirtualRequest only supports the GET method.
    """

    def __init__(self, original_request, path, query_string):
        self.original_request = original_request
        self.path = path
        self.query_string = query_string
        self.encoding = self.original_request.encoding
        self.GET = QueryDict(self.query_string, encoding=self._encoding)
        self.POST = QueryDict('', encoding=self._encoding)
        self.FILES = QueryDict('', encoding=self._encoding)
        self.REQUEST = MergeDict(self.POST, self.GET)
        self.COOKIES = self.original_request.COOKIES
        self.META = {}
        self.raw_post_data = ''
        #TODO: will we ever need META, path_info, or script_name?
        self.method = 'GET'

    def get_full_path(self):
        return '%s%s' % (self.path, self.query_string and ('?' + self.query_string) or '')

    def is_secure(self):
        return self.original_request.is_secure()

    def has_virtual_request_cycle(self):
        """
        Return whether the chain of virtual requests is cyclical, and will thus
        cause an infinite loop if we try to render.
        """
        visited_nodes = set()
        cur_node = self
        request_hash_fn = lambda r: (r.path, r.method, r.query_string, r.raw_post_data)
        while True:
            cur_node_hash = request_hash_fn(cur_node)
            if cur_node_hash in visited_nodes:
                return True
            visited_nodes.add(cur_node_hash)
            if not hasattr(cur_node.original_request, 'has_virtual_request_cycle'):
                break
            cur_node = cur_node.original_request
        return False


###############################################################################
# Viewer metaclass stuff
###############################################################################

class ViewerMetaClass(type):
    """
    Metaclass for viewers. Defines ViewerMetaClass.viewer_name_dict, a mapping
    from viewer names to viewer classes.
    """
    viewer_name_dict = {}
    def __new__(cls, name, bases, attrs):
        result = super(ViewerMetaClass, cls).__new__(cls, name, bases, attrs)
        if name != 'Viewer':
            if 'viewer_name' not in attrs:
                raise Exception("Viewer `%s` does not define `viewer_name`" % name)
            if 'accepted_item_type' not in attrs:
                raise Exception("Viewer `%s` does not define `accepted_item_type`" % name)
            viewer_name = attrs['viewer_name']
            if viewer_name in ViewerMetaClass.viewer_name_dict:
                raise Exception("Viewer with name `%s` is defined multiple times" % viewer_name)
            ViewerMetaClass.viewer_name_dict[viewer_name] = result
        return result


###############################################################################
# The Viewer class
###############################################################################

class Viewer(object):
    """
    Superclass of all viewers. Implements all of the common functionality
    like dispatching and convenience methods, but does not define any views.
    
    Although most viewers will want to inherit from ItemViewer, since it
    defines the basic views (like list, show, edit), some viewers may want to
    inherit from this abstract Viewer so they can ensure no views will be
    inherited.
    
    Subclasses must define the following fields:
    * `accepted_item_type`: The item type that this viewer is defined over. For
      example, if accepted_item_type == Agent, this viewer can be used to view
      Agents and all subclasses of Agents (e.g., Person), but an error will be
      rendered if a user tries to view something else (e.g., a Document) with
      this viewer.
    * `viewer_name`: The name of the viewer, which shows up in the URL. This
      should only consist of lowercase letters, in accordance with the Deme URL
      scheme.
    
    There are two types of views subclasses can define: item-specific views,
    and type-wide views. Item-specific views expect an item in the URL (the noun),
    while type-wide views do not expect a particular item.
    1. To define an item-speicfic view, define a method with the name
      `item_method_format`, where `method` is the name of the view (which shows
      up in the URL as the action), and format is the output format (which shows
      up in the URL as the format). For example, the method item_edit_html(self)
      in an agent viewer represents the item-specific view with action="edit" and
      format="html", and would respond to the URL `/viewing/agent/123/edit.html`.
    2. To define a type-wide view, define a method with the name
      `type_method_format`. For example, the method type_new_html(self) in an
      agent viewer represents the type-wide view with action="new" and
      format="html", and would respond to the URL `/viewing/agent/new.html`.
    
    View methods take no parameters (except self), since all of the details of
    the request are defined as instance variables in the viewer before
    dispatch. They must return an HttpResponse. They should take advantage of
    self.context, which is defined before the view is called.
        
    The following instance variables are defined on the viewer:
    * self.item (the requested Item, or None if there is no noun)
    * self.context (the Context object used to render templates)
    * self.action (the action part of the URL)
    * self.noun (the noun part of the URL)
    * self.format (the format part of the URL)
    * self.request (the HttpRequest that initiated this viewer)
    * self.method (the HTTP method of the request, so that require_POST works)
    * self.cur_agent (the currently authenticated Agent or AnonymousAgent)
    * self.cur_site (the Site that is being used for this request)
    * self.multi_agent_permission_cache (a MultiAgentPermissionCache for
      permission queries)
    * self.permission_cache (a PermissionCache for permission queries on cur_agent)
    * self.item (the downcasted requested item if there's a noun in the request)
      - If there is a `version` parameter in the query string, the item's fields
        will be populated with data from the requested version
    
    The following context variables are defined:
    * self.context['action'] (the action part of the URL)
    * self.context['item'] (the requested Item, or None if there is no noun)
    * self.context['specific_version'] (True if the user requested a specific
      version of the item in the query string, otherwise False)
    * self.context['viewer_name'] (value of viewer.viewer_name)
    * self.context['accepted_item_type'] (value of viewer.accepted_item_type)
    * self.context['accepted_item_type_name'] (verbose name of accepted_item_type)
    * self.context['accepted_item_type_name_plural'] (verbose name plural of
      accepted_item_type)
    * self.context['full_path'] (the path to the current page)
    * self.context['query_string'] (the query string for the current page)
    * self.context['cur_agent'] (the currently authenticated Agent)
    * self.context['cur_site'] (the Site that is being used for this request)
    * self.context['_viewer'] (the viewer itself, only for custom tags/filters)
    * self.context['layout'] (the layout that the template should inherit from)

        
    """
    __metaclass__ = ViewerMetaClass

    ###########################################################################
    # Important functions (initializing and dispatching)
    ###########################################################################

    def __init__(self):
        # Nothing happens in the constructor. All of the initialization happens
        # in the init_for_* methods, based on how the viewer was loaded.
        pass

    def init_for_http(self, request, action, noun, format):
        """
        This method sets up the Viewer from an incoming HttpRequest. The
        `action`, `noun`, and `format` parameters are extracted from the URL
        (or the ViewerRequest). This method should only be called from
        cms/dispatcher.py.
        """
        self.context = Context()
        self.action = action or ('show' if noun else 'list')
        self.noun = noun
        self.format = format or 'html'
        self.request = request
        self.method = self.request.method
        self.cur_agent = get_logged_in_agent(request)
        self.cur_site = get_current_site(request)
        self.multi_agent_permission_cache = MultiAgentPermissionCache()
        self.permission_cache = self.multi_agent_permission_cache.get(self.cur_agent)
        if self.noun is None:
            self.item = None
        else:
            try:
                self.item = Item.objects.get(pk=self.noun)
                self.item = self.item.downcast()
                version_number = self.request.GET.get('version')
                if version_number is not None:
                    self.item.copy_fields_from_version(version_number)
                self.context['specific_version'] = ('version' in self.request.GET)
            except ObjectDoesNotExist:
                self.item = None
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['viewer_name'] = self.viewer_name
        self.context['accepted_item_type'] = self.accepted_item_type
        self.context['accepted_item_type_name'] = self.accepted_item_type._meta.verbose_name
        self.context['accepted_item_type_name_plural'] = self.accepted_item_type._meta.verbose_name_plural
        self.context['full_path'] = self.request.get_full_path()
        self.context['query_string'] = self.request.META['QUERY_STRING']
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_viewer'] = self
        self.context['default_metadata_menu_option'] = self.default_metadata_menu_option()
        self._set_default_layout()

    def init_for_div(self, original_viewer, action, item, query_string):
        """
        This method sets up the Viewer to be embedded (probably in a <div>) in
        the specified original_viewer. The action, item, and query_string
        specify the details of what will be embedded in this viewer.
        """
        if item is None:
            path = reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': action})
        else:
            path = reverse('item_url', kwargs={'viewer': self.viewer_name, 'action': action, 'noun': item.pk})
        self.request = VirtualRequest(original_viewer.request, path, query_string)
        self.method = self.request.method
        self.cur_agent = original_viewer.cur_agent
        self.cur_site = original_viewer.cur_site
        self.multi_agent_permission_cache = original_viewer.multi_agent_permission_cache
        self.permission_cache = original_viewer.permission_cache
        self.format = 'html'
        if item is None:
            self.noun = None
        else:
            self.noun = str(item.pk)
        self.item = item
        self.action = action
        self.context = Context()
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['specific_version'] = False
        self.context['viewer_name'] = self.viewer_name
        self.context['accepted_item_type'] = self.accepted_item_type
        self.context['accepted_item_type_name'] = self.accepted_item_type._meta.verbose_name
        self.context['accepted_item_type_name_plural'] = self.accepted_item_type._meta.verbose_name_plural
        self.context['full_path'] = original_viewer.context['full_path'] 
        self.context['query_string'] = ''
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_viewer'] = self
        self.context['layout'] = 'blank.html'

    def init_for_outgoing_email(self, agent):
        """
        This method sets up the Viewer to render the body of an outgoing email
        to the specified `agent`. There is no request associated with this
        viewer. Viewers initialized with this function should not be used to
        render ordinary actions (like item_show_html). Instead, they can be
        used to render emails that want to take advantage of the item_tags
        and existing infrastructure that requires a viewer.
        """
        self.request = None
        self.method = None
        self.cur_agent = agent
        self.cur_site = get_default_site()
        self.multi_agent_permission_cache = MultiAgentPermissionCache()
        self.permission_cache = self.multi_agent_permission_cache.get(self.cur_agent)
        self.format = 'html'
        self.noun = None
        self.item = None
        self.action = 'list'
        self.context = Context()
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['specific_version'] = False
        self.context['viewer_name'] = self.viewer_name
        self.context['accepted_item_type'] = self.accepted_item_type
        self.context['accepted_item_type_name'] = self.accepted_item_type._meta.verbose_name
        self.context['accepted_item_type_name_plural'] = self.accepted_item_type._meta.verbose_name_plural
        self.context['full_path'] = '/'
        self.context['query_string'] = ''
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_viewer'] = self
        self.context['layout'] = 'blank.html'

    def dispatch(self):
        """
        Perform the requested action and return an HttpResponse. In general,
        this should just be called from cms/dispatcher.py. Return None if there
        is no Python method that corresponds with the requested action.
        """
        # Make sure there isn't a cycle in the virtual request graph.
        if hasattr(self.request, 'has_virtual_request_cycle'):
            if self.request.has_virtual_request_cycle():
                return self.render_error(
                    'Cycle detected in embedded viewers',
                    'The embedded viewers cannot be rendered without an infinite loop.',
                    HttpResponseNotFound)

        # Get the Python method that corresponds to the requested action
        if self.noun is None:
            action_method_name = 'type_%s_%s' % (self.action, self.format)
        else:
            action_method_name = 'item_%s_%s' % (self.action, self.format)
        action_method = getattr(self, action_method_name, None)
        if not action_method:
            return None

        # Return an error if there was a noun in the request but we weren't
        # able to find the corresponding item, or if the corresponding item
        # is not an instance of accepted_item_type (with the exception of
        # the 'copy' action, which will allow any viewer to copy any item).
        if self.noun != None:
            if self.item is None:
                return self.render_item_not_found()
            if not isinstance(self.item, self.accepted_item_type) and self.action != 'copy':
                return self.render_item_not_found()

        # Perform the action
        try:
            response = action_method()
            return response
        except DemePermissionDenied, e:
            # If a DemePermissionDenied exception was raised while trying to
            # perform the action, render a friendly error page.
            from cms.templatetags.item_tags import get_item_link_tag
            ability_friendly_name = friendly_name_for_ability(e.ability) or e.ability
            # Explain what the user is trying to do
            if self.context.get('action_title'):
                msg = u'You do not have permission to perform the "%s" action' % self.context['action_title']
            else:
                msg = u'You do not have permission to perform the action'
            if self.item:
                msg += u' on %s' % get_item_link_tag(self.context, self.item)
            # Explain why the user cannot do it
            if e.item is None:
                msg += u' (you need the "%s" global ability)' % ability_friendly_name
            else:
                permission_item_text = 'it' if e.item == self.item else get_item_link_tag(self.context, e.item)
                if e.item.destroyed:
                    msg += u' (%s is destroyed)' % permission_item_text
                else:
                    msg += u' (you need the "%s" ability on %s)' % (ability_friendly_name, permission_item_text)
            return self.render_error('Permission Denied', msg)

    ###########################################################################
    # Overridable functions
    ###########################################################################

    def default_metadata_menu_option(self):
        """
        Return the default metadata menu option to display in the layout when
        pages are displayed in this viewer. Possible choices are None,
        'item_details', 'comments', 'action_notices', 'versions', 'related_items',
        and 'permissions'.
        """
        return None

    ###########################################################################
    # Helper functions
    ###########################################################################

    def cur_agent_can_global(self, ability, wildcard_suffix=False):
        """
        Return whether the currently logged in agent has the given global
        ability. If wildcard_suffix=True, then return True if the agent has
        **any** global ability whose prefix is the specified ability.
        """
        if wildcard_suffix:
            global_abilities = self.permission_cache.global_abilities()
            return any(x.startswith(ability) for x in global_abilities)
        else:
            return self.permission_cache.agent_can_global(ability)

    def cur_agent_can(self, ability, item, wildcard_suffix=False):
        """
        Return whether the currently logged in agent has the given item ability
        with respect to the given item. If wildcard_suffix=True, then return
        True if the agent has **any** ability whose prefix is the specified
        ability.
        """
        if wildcard_suffix:
            abilities_for_item = self.permission_cache.item_abilities(item)
            return any(x.startswith(ability) for x in abilities_for_item)
        else:
            return self.permission_cache.agent_can(ability, item)

    def require_global_ability(self, ability, wildcard_suffix=False):
        """
        Raise a DemePermissionDenied exception if the current agent does not
        have the specified global ability. The wildcard_suffix parameter is
        defined same as in cur_agent_can_global.
        """
        if not self.cur_agent_can_global(ability, wildcard_suffix):
            if wildcard_suffix:
                raise DemePermissionDenied(_(ability.strip()), None)
            else:
                raise DemePermissionDenied(ability, None)

    def require_ability(self, ability, item, wildcard_suffix=False):
        """
        Raise a DemePermissionDenied exception if the current agent does not
        have the specified ability with respect to the specified item. The
        wildcard_suffix parameter is defined same as in cur_agent_can.
        """
        if not self.cur_agent_can(ability, item, wildcard_suffix):
            if wildcard_suffix:
                raise DemePermissionDenied(_(ability.strip()), item)
            else:
                raise DemePermissionDenied(ability, item)

    def render_error(self, title, body, request_class=HttpResponseBadRequest):
        """
        Return an HttpResponse (of type request_class) that displays a simple
        error page with the specified title and body.
        """
        #TODO obey self.format when rendering an error if possible
        if 'action_title' not in self.context:
            self.context['action_title'] = 'Error'
        template = loader.get_template_from_string("""
        {%% extends layout %%}
        {%% load item_tags %%}
        {%% block favicon %%}{{ "error"|icon_url:16 }}{%% endblock %%}
        {%% block title %%}<img src="{{ "error"|icon_url:24 }}" /> %s{%% endblock %%}
        {%% block content %%}%s{%% endblock content %%}
        """ % (title, body))
        return request_class(template.render(self.context))

    def render_item_not_found(self):
        """
        Render an error response since the requested item could not be displayed.
        """
        if self.item:
            title = "%s Not Found" % self.accepted_item_type.__name__
            body = """
            You cannot view item %s in this viewer.
            Try viewing it in the <a href="%s">%s viewer</a>.
            """ % (self.noun, self.item.get_absolute_url(), self.item.get_default_viewer())
        else:
            title = "Item Not Found"
            version = self.request.GET.get('version')
            if version is None:
                body = 'There is no item %s.' % self.noun
            else:
                body = 'There is no item %s version %s.' % (self.noun, version)
        return self.render_error(title, body, HttpResponseNotFound)

    def get_form_class_for_item_type(self, item_type, is_new, fields=None):
        """
        Return a Django form class to render a create/edit form for the given
        item type. This form class will be dynamically created. If is_new=True,
        it will be customized for creating new items, and if is_new=False, it
        will be customized for editing existing items. If fields is a list,
        the form fields will be limited to only the fields in that list (but if
        it's None, the default form fields will be used).
        
        This function wraps around Django's modelforms.
        """
        viewer = self

        # Exclude parent_link fields, as well as immutable fields (when editing)
        exclude = []
        for field in item_type._meta.fields:
            if (field.rel and field.rel.parent_link) or ((not is_new) and field.name in item_type.all_immutable_fields()):
                exclude.append(field.name)


        # Sort the fields by their original ordering in the model
        if fields is not None:
            def field_sort_fn(field_name):
                try:
                    field = item_type._meta.get_field_by_name(field_name)[0]
                    return (0, field)
                except FieldDoesNotExist:
                    return (1, None)
            fields.sort(key=field_sort_fn)

        # Set up the modelform class like modelform_factory does
        #TODO check modelform_factory to see if there are updates to this, since it mentioned it was hacky
        attrs = {}
        class Meta:
            pass
        setattr(Meta, 'model', item_type)
        setattr(Meta, 'fields', fields)
        setattr(Meta, 'exclude', exclude)
        attrs['Meta'] = Meta

        # Define a custom formfield callback that will automatically use the
        # AjaxModelChoiceField for all ForeignKey fields.
        def formfield_callback(f):
            if isinstance(f, models.ForeignKey):
                options = {}
                options['queryset'] = f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to)
                options['form_class'] = AjaxModelChoiceField
                options['to_field_name'] = f.rel.field_name
                options['required_abilities'] = getattr(f, 'required_abilities', [])
                options['permission_cache'] = self.permission_cache
                return super(models.ForeignKey, f).formfield(**options)
            else:
                return f.formfield()
        attrs['formfield_callback'] = formfield_callback

        # Create an action_summary field
        if 'action_summary' not in exclude:
            attrs['action_summary'] = forms.CharField(label=_("Action summary"), help_text=_("%sReason for %s this item" % ('(Advanced) ' if is_new else '', 'creating' if is_new else 'editing')), widget=forms.TextInput, required=False)

        # Method that converts a form to a table that replaces as_table() in django.forms.forms
        # This method automatically hides all fields that have help_texts that begin with "(Advanced)"
        def convert_form_to_table(form):
            from django.forms.forms import BoundField
            from django.utils.html import conditional_escape
            from django.utils.encoding import force_unicode

            "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
            result = []
    
            for name, field in form.fields.items():
                if not field: continue
                bf = BoundField(form, field, name)
                bf_errors = form.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
                if bf.label:
                    label = conditional_escape(force_unicode(bf.label))
                help_text = force_unicode(field.help_text)
                if help_text.startswith('(Advanced)'):
                    result.append(""" <tr style="display: none;" class="advancedfield"><th>%(name)s:</th> <td>%(errors)s%(field)s<br>%(help_text)s</td></tr> """ %
                        {
                            'field':form[name],
                            'name':label,
                            'help_text': help_text,
                            'errors': force_unicode(bf_errors),
                        })
                else:
                    result.append(""" <tr><th>%(name)s:</th> <td>%(errors)s%(field)s<br>%(help_text)s</td></tr> """ %
                        {
                            'field':form[name],
                            'name':label,
                            'help_text': help_text,
                            'errors': force_unicode(bf_errors),
                        })

            result.append("""<tr id="showadv"><td colspan="2"><a href="#" style="float: right; font-size: 130%;" onclick="$('.advancedfield').show(); $('#hideadv').show(); $('#showadv').hide(); return false;">Display Advanced Options</a></td></tr> """)
            result.append("""<tr id="hideadv" style="display: none;"><td colspan="2"><a href="#" style="float: right; font-size: 130%;" onclick="$('.advancedfield').hide(); $('#hideadv').hide(); $('#showadv').show(); return false;">Hide Advanced Options</a></td></tr> """)
            return mark_safe(u'\n'.join(result))


        # Allow the item type to do its own specialized form configuration
        item_type.do_specialized_form_configuration(item_type, is_new, attrs)
        if not self.cur_agent.is_anonymous():
            del attrs['captcha'] 

        # Construct the form class
        class_name = item_type.__name__ + 'Form'
        form_class = forms.models.ModelFormMetaclass(class_name, (forms.models.ModelForm,), attrs)

        #Override the default as_table() method
        form_class.as_table = convert_form_to_table

        return form_class

    def get_populated_field_dict(self, item_type):
        """
        Return a dict of populated fields from the query string. For example,
        say the query string is ?populate_name=Mike&populate_description=hi --
        then this method should return {'name': 'Mike', 'description': 'hi'}.
        This method will ignore any parameters in the query string that do not
        start with `populate_`, and it a non-destructive method.
        """
        key_prefix = 'populate_'
        result = {}
        for key, value in self.request.GET.iteritems():
            if key.startswith(key_prefix):
                field_name = key.split(key_prefix, 1)[1]
                result[field_name] = value
        item_type.auto_populate_fields(item_type, result, self)
        return result

    def _set_default_layout(self):
        """
        Set the context['layout'] variable to the default layout template (from
        a DjangoTemplateDocument) for the current Site, or default_layout.html
        if there is no default layout item.
        """
        self.context['layout'] = 'default_layout.html'
        if self.cur_agent_can('view Site.default_layout', self.cur_site):
            if self.cur_site.default_layout:
                self.context['layout'] = self.construct_template(self.cur_site.default_layout)
        else:
            self.context['layout_permissions_problem'] = True

    def construct_template(self, django_template_document):
        """
        Construct a template object (like the result of loader.get_template)
        from the specified DjangoTemplateDocument, as it should be rendered to
        the current agent. This function takes care of rendering the
        DjangoTemplateDocument within its layout (recursively all the way up),
        and it checks for permissions to view each DjangoTemplateDocument in
        the layout path.
        """
        visited_nodes = set()
        cur_node = django_template_document
        while cur_node is not None:
            # Check for cycles
            if cur_node in visited_nodes:
                raise Exception("There is a layout cycle")
            visited_nodes.add(cur_node)

            # Get the context variable name, and don't set it if it was set
            # earlier (perhaps by an embedded document with the same layout).
            context_key = 'layout%d' % cur_node.pk
            if context_key in self.context:
                break

            # Set next_node
            if self.cur_agent_can('view DjangoTemplateDocument.layout', cur_node):
                next_node = cur_node.layout
            else:
                next_node = None
                self.context['layout_permissions_problem'] = True

            # Set extends_string
            if cur_node.override_default_layout:
                extends_string = ''
            elif not next_node:
                if 'layout' in self.context:
                    extends_string = "{% extends layout %}\n"
                else:
                    raise Exception("The default layout for this site cycles with itself")
            else:
                extends_string = '{%% extends layout%s %%}\n' % next_node.pk

            # Set body_string
            if self.cur_agent_can('view TextDocument.body', cur_node):
                body_string = cur_node.body
            else:
                body_string = ''
                if cur_node.override_default_layout:
                    extends_string = "{% extends 'default_layout.html' %}"
                self.context['layout_permissions_problem'] = True

            # Create the template
            t = loader.get_template_from_string(extends_string + body_string)
            self.context[context_key] = t

            cur_node = next_node
        return self.context['layout%s' % django_template_document.pk]


###############################################################################
# Viewer importing stuff (must come last)
###############################################################################

_all_views_imported = False
def import_all_views():
    """
    Import viewers from modules so they get registered with ViewerMetaClass
    """
    global _all_views_imported
    if not _all_views_imported:
        _all_views_imported = True
        import cms.views
        for module_name in settings.MODULE_NAMES:
            __import__('modules.%s.views' % module_name)

def get_viewer_class_by_name(viewer_name):
    """
    Return the viewer class with the given name. If no such class exists,
    return None.
    """
    import_all_views()
    result = ViewerMetaClass.viewer_name_dict.get(viewer_name, None)
    return result


def all_viewer_classes():
    "Return a list of all viewer classes defined."
    import_all_views()
    return ViewerMetaClass.viewer_name_dict.values()

