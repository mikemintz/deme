#TODO completely clean up code

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
from cms.forms import JavaScriptSpamDetectionField, AjaxModelChoiceField
from django.utils.text import get_text_list, capfirst
from django.utils.safestring import mark_safe
from django.utils.html import escape
from urllib import urlencode
from cms.models import Item, Agent, Site, AnonymousAgent, DemeSetting

#TODO obey self.format when rendering an error if possible

class DemePermissionDenied(Exception):
    def __init__(self, ability, item):
        self.ability = ability
        self.item = item
        super(DemePermissionDenied, self).__init__("The agent does not have permission to perform the action")


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
            print len(visited_nodes)
        return False


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
    """
    __metaclass__ = ViewerMetaClass

    def __init__(self):
        # Nothing happens in the constructor. All of the initialization happens
        # in the init_from_* methods, based on how the viewer was loaded.
        pass

    def cur_agent_can_global(self, ability, wildcard_suffix=False):
        """
        Return whether the currently logged in agent has the given global
        ability. If wildcard_suffix=True, then return True if the agent has
        **any** global ability whose first word is the specified ability.
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
        True if the agent has **any** ability whose first word is the specified
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
        have the specified global ability.
        """
        if not self.cur_agent_can_global(ability, wildcard_suffix):
            if wildcard_suffix:
                raise DemePermissionDenied(_(ability.strip()), None)
            else:
                raise DemePermissionDenied(ability, None)

    def require_ability(self, ability, item, wildcard_suffix=False):
        """
        Raise a DemePermissionDenied exception if the current agent does not
        have the specified ability with respect to the specified item.
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

    def init_for_http(self, request, action, noun, format):
        self.context = Context()
        self.action = action or ('show' if noun else 'list')
        self.noun = noun
        self.format = format or 'html'
        self.method = (request.GET.get('_method', None) or request.method).upper()
        self.request = request
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
        self._set_default_layout()

    def init_for_div(self, original_viewer, action, item, query_string):
        if item is None:
            path = reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': action})
        else:
            path = reverse('item_url', kwargs={'viewer': self.viewer_name, 'action': action, 'noun': item.pk})
        self.request = VirtualRequest(original_viewer.request, path, query_string)
        self.cur_agent = original_viewer.cur_agent
        self.cur_site = original_viewer.cur_site
        self.multi_agent_permission_cache = original_viewer.multi_agent_permission_cache
        self.permission_cache = original_viewer.permission_cache
        self.format = 'html'
        self.method = 'GET'
        if item is None:
            self.noun = None
        else:
            self.noun = item.pk
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
        self.request = None
        self.cur_agent = agent
        self.cur_site = get_default_site()
        self.multi_agent_permission_cache = MultiAgentPermissionCache()
        self.permission_cache = self.multi_agent_permission_cache.get(self.cur_agent)
        self.format = 'html'
        self.method = 'GET'
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
        if hasattr(self.request, 'has_virtual_request_cycle'):
            if self.request.has_virtual_request_cycle():
                return self.render_error("Cycle detected in embedded viewers", 'There is a cycle in the embedded viewers, and it cannot be rendered without an infinite loop.', HttpResponseNotFound)
        if self.noun is None:
            action_method_name = 'type_%s_%s' % (self.action, self.format)
        else:
            action_method_name = 'item_%s_%s' % (self.action, self.format)
        action_method = getattr(self, action_method_name, None)
        if action_method:
            if self.noun != None:
                if self.item is None:
                    return self.render_item_not_found()
                elif self.action == 'copy':
                    pass
                else:
                    if not isinstance(self.item, self.accepted_item_type):
                        return self.render_item_not_found()
            try:
                response = action_method()
                return response
            except DemePermissionDenied, e:
                from cms.templatetags.item_tags import get_item_link_tag
                ability_friendly_name = friendly_name_for_ability(e.ability) or e.ability
                if self.context.get('action_title'):
                    msg = u'You do not have permission to perform the "%s" action' % self.context['action_title']
                else:
                    msg = u'You do not have permission to perform the action'
                if self.item:
                    msg += u' on %s' % get_item_link_tag(self.context, self.item)
                if e.item is None:
                    msg += u' (you need the "%s" global ability)' % ability_friendly_name
                elif e.item.destroyed:
                    msg += u' (%s is destroyed)' % ('it' if e.item == self.item else get_item_link_tag(self.context, e.item))
                else:
                    msg += u' (you need the "%s" ability on %s)' % (ability_friendly_name, 'it' if e.item == self.item else get_item_link_tag(self.context, e.item))
                return self.render_error('Permission Denied', msg)
        else:
            return None

    def render_item_not_found(self):
        if self.item:
            title = "%s Not Found" % self.accepted_item_type.__name__
            body = 'You cannot view item %s in this viewer. Try viewing it in the <a href="%s">%s viewer</a>.' % (self.noun, self.item.get_absolute_url(), self.item.get_default_viewer())
        else:
            title = "Item Not Found"
            version = self.request.GET.get('version')
            if version is None:
                body = 'There is no item %s.' % self.noun
            else:
                body = 'There is no item %s version %s.' % (self.noun, version)
        return self.render_error(title, body, HttpResponseNotFound)

    def get_form_class_for_item_type(self, item_type, is_new, fields=None):
        viewer = self

        exclude = []
        for field in item_type._meta.fields:
            if (field.rel and field.rel.parent_link) or ((not is_new) and field.name in item_type.all_immutable_fields()):
                exclude.append(field.name)
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

        if fields is not None:
            # Sort the fields by their natural ordering
            def field_sort_fn(field_name):
                try:
                    field = item_type._meta.get_field_by_name(field_name)[0]
                    return (0, field)
                except FieldDoesNotExist:
                    return (1, None)
            fields.sort(key=field_sort_fn)

        #TODO check modelform_factory to see if there are updates to this
        attrs = {}
        class Meta:
            pass
        setattr(Meta, 'model', item_type)
        setattr(Meta, 'fields', fields)
        setattr(Meta, 'exclude', exclude)
        class_name = item_type.__name__ + 'Form'
        attrs['Meta'] = Meta
        attrs['formfield_callback'] = formfield_callback
        if 'action_summary' not in exclude:
            attrs['action_summary'] = forms.CharField(label=_("Action summary"), help_text=_("Reason for %s this item" % ('creating' if is_new else 'editing')), widget=forms.TextInput, required=False)
        if settings.USE_ANONYMOUS_JAVASCRIPT_SPAM_DETECTOR and self.cur_agent.is_anonymous():
            self.request.session.modified = True # We want to guarantee a cookie is given
            attrs['nospam'] = JavaScriptSpamDetectionField(self.request.session.session_key)

        def unique_error_message(self, unique_check):
            unique_field_dict = {}
            for field_name in unique_check:
                unique_field_dict[field_name] = self.cleaned_data[field_name]
            try:
                existing_item = type(self.instance).objects.get(**unique_field_dict)
            except ObjectDoesNotExist:
                existing_item = None
            if existing_item:
                show_item_url = existing_item.get_absolute_url()
                from cms.templatetags.item_tags import get_viewable_name
                item_name = get_viewable_name(viewer.context, existing_item)
                overwrite_url = reverse('item_url', kwargs={'viewer': existing_item.get_default_viewer(), 'noun': existing_item.pk, 'action': 'edit'})
                overwrite_query_params = []
                for k, v in self.cleaned_data.iteritems():
                    k = 'populate_' + k
                    if isinstance(v, Item):
                        v = str(v.pk)
                    overwrite_query_params.append(urlencode({k: v}))
                for k, list_ in viewer.request.GET.lists():
                    overwrite_query_params.extend([urlencode({k: v}) for v in list_])
                overwrite_query_string = '&'.join(overwrite_query_params)
                existing_item_str = u' as <a href="%s">%s</a> (<a href="%s?%s">overwrite it</a>)' % (show_item_url, item_name, overwrite_url, escape(overwrite_query_string))
            model_name = capfirst(self.instance._meta.verbose_name)
            field_labels = [self.fields[field_name].label for field_name in unique_check]
            field_labels = get_text_list(field_labels, _('and'))
            result = _(u"%(model_name)s with this %(field_label)s already exists%(existing_item_str)s.") %  {
                'model_name': unicode(model_name),
                'field_label': unicode(field_labels),
                'existing_item_str': existing_item_str,
            }
            return mark_safe(result)
        attrs['unique_error_message'] = unique_error_message
        
        item_type.do_specialized_form_configuration(item_type, is_new, attrs)
        form_class = forms.models.ModelFormMetaclass(class_name, (forms.models.ModelForm,), attrs)
        return form_class

    def get_populated_field_dict(self):
        result = {}
        for key, value in self.request.GET.iteritems():
            if key.startswith('populate_'):
                field_name = key.split('populate_', 1)[1]
                result[field_name] = value
        return result

    def _set_default_layout(self):
        self.context['layout'] = 'default_layout.html'
        if self.cur_agent_can('view Site.default_layout', self.cur_site):
            if self.cur_site.default_layout:
                self.context['layout'] = self.construct_template(self.cur_site.default_layout)
        else:
            self.context['layout_permissions_problem'] = True

    def construct_template(self, django_template_document):
        cur_node = django_template_document
        while cur_node is not None:
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


def get_viewer_class_by_name(viewer_name):
    """
    Return the viewer class with the given name. If no such class exists,
    return None.
    """
    # Check the defined viewers in ViewerMetaClass.viewer_name_dict
    result = ViewerMetaClass.viewer_name_dict.get(viewer_name, None)
    return result


def all_viewer_classes():
    "Return a list of all viewer classes defined."
    return ViewerMetaClass.viewer_name_dict.values()
