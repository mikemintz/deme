#TODO completely clean up code

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.utils.http import urlquote
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.template import Context, loader
from django.db import models
from django.db.models import Q
from cms.models import *
from django import forms
from django.utils import simplejson
from django.core.exceptions import ObjectDoesNotExist
import django.contrib.syndication.feeds
import django.contrib.syndication.views
from permissions import PermissionCache
import re
import os
import subprocess
import datetime

###############################################################################
# Models, forms, and fields
###############################################################################

item_type_name_dict = {}
for item_type in all_item_types():
    item_type_name_dict[item_type.__name__.lower()] = item_type


class AjaxModelChoiceWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        model = self.choices.queryset.model
        #field = self.choices.field
        try:
            if issubclass(model, Item):
                value_item = Item.objects.get(pk=value)
            elif issubclass(model, Item.Version):
                value_item = Item.Version.objects.get(pk=value)
            else:
                value_item = None
        except:
            value_item = None
        initial_search = value_item.name if value_item else ''
        if value is None: value = ''
        if attrs is None: attrs = {}
        ajax_url = reverse('item_type_url', kwargs={'viewer': model.__name__.lower(), 'format': 'json'})
        result = """
        <input type="hidden" name="%(name)s" value="%(value)s" />
        <input class="ajax_choice_field" type="text" id="%(id)s" name="%(name)s_search" value="%(initial_search)s" autocomplete="off" />
        <div class="ajax_choice_results" style="display: none;"></div>
        <script type="text/javascript">
        fn = function(){
          var ajax_observer = null;
          var search_onchange = function(e, value) {
            var hidden_input = $(e).previousSiblings()[0];
            var results_div = $(e).nextSiblings()[0];
            if (value == '') {
              $A(results_div.childNodes).each(Element.remove);
              $(results_div).hide();
              hidden_input.value = '';
              return;
            }
            var url = '%(ajax_url)s?q=' + encodeURIComponent(value);
            new Ajax.Request(url, {
              method: 'get',
              onSuccess: function(transport) {
                var results = $A(transport.responseJSON);
                results.splice(0, 0, ['[NULL]', '']);
                $A(results_div.childNodes).each(Element.remove);
                results.each(function(result){
                  var option = document.createElement('div');
                  option.className = 'ajax_choice_option';
                  option.innerHTML = result[0];
                  $(option).observe('click', function(event){
                    e.ajax_observer.stop();
                    e.value = result[0];
                    e.ajax_observer = new Form.Element.Observer(e, 0.25, search_onchange);
                    hidden_input.value = result[1];
                    $A(results_div.childNodes).each(Element.remove);
                    $(results_div).hide();
                  });
                  results_div.appendChild(option);
                });
                $(results_div).show();
              }
            });
          };
          $$('.ajax_choice_field').each(function(input){
            if (!input.hasClassName('ajax_choice_field_activated')) {
              input.addClassName('ajax_choice_field_activated');
              input.ajax_observer = new Form.Element.Observer(input, 0.25, search_onchange);
            }
          });
        };
        fn();
        </script>
        """ % {'name': name, 'value': value, 'id': attrs.get('id', ''), 'ajax_url': ajax_url, 'initial_search': initial_search}
        return result

class AjaxModelChoiceField(forms.ModelChoiceField):
    widget = AjaxModelChoiceWidget

class HiddenModelChoiceField(forms.ModelChoiceField):
    widget = forms.HiddenInput

class TextModelChoiceField(forms.ModelChoiceField):
    widget = forms.TextInput

class AddSubPathForm(forms.ModelForm):
    aliased_item = super(models.ForeignKey, CustomUrl._meta.get_field_by_name('aliased_item')[0]).formfield(queryset=CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.to._default_manager.complex_filter(CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.field_name)
    parent_url = super(models.ForeignKey, CustomUrl._meta.get_field_by_name('parent_url')[0]).formfield(queryset=CustomUrl._meta.get_field_by_name('parent_url')[0].rel.to._default_manager.complex_filter(CustomUrl._meta.get_field_by_name('parent_url')[0].rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=CustomUrl._meta.get_field_by_name('parent_url')[0].rel.field_name)
    class Meta:
        model = CustomUrl
        fields = ['aliased_item', 'viewer', 'action', 'query_string', 'format', 'parent_url', 'path']

class NewMembershipForm(forms.ModelForm):
    item = AjaxModelChoiceField(Item.objects)
    class Meta:
        model = Membership
        fields = ['item']

class NewTextCommentForm(forms.ModelForm):
    item = HiddenModelChoiceField(Item.objects)
    item_version_number = forms.IntegerField(widget=forms.HiddenInput())
    item_index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = TextComment
        fields = ['name', 'description', 'body', 'item', 'item_version_number']

class NewPasswordAuthenticationMethodForm(forms.ModelForm):
    agent = AjaxModelChoiceField(Agent.objects)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    class Meta:
        model = PasswordAuthenticationMethod
        exclude = ['password']
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    def save(self, commit=True):
        item = super(NewPasswordAuthenticationMethodForm, self).save(commit=False)
        item.set_password(self.cleaned_data["password1"])
        if commit:
            item.save()
        return item

class EditPasswordAuthenticationMethodForm(forms.ModelForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    class Meta:
        model = PasswordAuthenticationMethod
        exclude = ['password', 'agent']
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    def save(self, commit=True):
        item = super(EditPasswordAuthenticationMethodForm, self).save(commit=False)
        item.set_password(self.cleaned_data["password1"])
        if commit:
            item.save()
        return item

def get_form_class_for_item_type(update_or_create, item_type, fields=None):
    if issubclass(item_type, PasswordAuthenticationMethod):
        if update_or_create == 'update':
            return EditPasswordAuthenticationMethodForm
        else:
            return NewPasswordAuthenticationMethodForm
    # For now, this is how we prevent manual creation of TextDocumentExcerpts
    if issubclass(item_type, TextDocumentExcerpt):
        return forms.models.modelform_factory(item_type, fields=['name'])

    exclude = []
    for field in item_type._meta.fields:
        if (field.rel and field.rel.parent_link) or (update_or_create == 'update' and field.name in item_type.all_immutable_fields()):
            exclude.append(field.name)
    def formfield_callback(f):
        if isinstance(f, models.ForeignKey):
            return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
        else:
            return f.formfield()
    return forms.models.modelform_factory(item_type, exclude=exclude, fields=fields, formfield_callback=formfield_callback)


###############################################################################
# Viewer helper functions
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
    Agent.objects.filter(pk=cur_agent.pk).update(last_online_at=datetime.datetime.now())
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


class ViewerMetaClass(type):
    viewer_name_dict = {}
    def __new__(cls, name, bases, attrs):
        result = super(ViewerMetaClass, cls).__new__(cls, name, bases, attrs)
        if name != 'Viewer':
            ViewerMetaClass.viewer_name_dict[attrs['viewer_name']] = result
        return result


class Viewer(object):
    __metaclass__ = ViewerMetaClass

    def __init__(self):
        pass

    def cur_agent_can_global(self, ability):
        return self.permission_cache.agent_can_global(self.cur_agent, ability)

    def cur_agent_can(self, ability, item):
        return self.permission_cache.agent_can(self.cur_agent, ability, item)

    def render_error(self, request_class, title, body):
        """
        Return an HttpResponse (of type request_class) that displays a simple
        error page with the specified title and body.
        """
        template = loader.get_template_from_string("""
        {%% extends layout %%}
        {%% load item_tags %%}
        {%% block favicon %%}{{ "error"|icon_url:16 }}{%% endblock %%}
        {%% block title %%}<img src="{{ "error"|icon_url:48 }}" /> %s{%% endblock %%}
        {%% block content %%}%s{%% endblock content %%}
        """ % (title, body))
        return request_class(template.render(self.context))

        return error_response(self.cur_agent, self.cur_site, self.context['full_path'], request_class, title, body)

    def init_from_http(self, request, action, noun, format):
        self.context = Context()
        self.permission_cache = PermissionCache()
        self.action = action
        self.noun = noun
        self.format = format or 'html'
        self.method = (request.GET.get('_method', None) or request.method).upper()
        self.request = request # FOR NOW
        if self.noun is None:
            if self.action is None:
                self.action = {'GET': 'list', 'POST': 'create', 'PUT': 'update', 'DELETE': 'deactivate'}.get(self.method, 'list')
            self.item = None
        else:
            if self.action is None:
                self.action = {'GET': 'show', 'POST': 'create', 'PUT': 'update', 'DELETE': 'deactivate'}.get(self.method, 'show')
            try:
                self.item = Item.objects.get(pk=self.noun)
                self.item = self.item.downcast()
                self.item = get_versioned_item(self.item, self.request.GET.get('version'))
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
        self.cur_agent = get_logged_in_agent(request)
        self.cur_site = get_current_site(request)
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        self._set_default_layout()

    def init_from_div(self, original_viewer, action, item):
        self.permission_cache = original_viewer.permission_cache
        self.request = original_viewer.request
        self.format = 'html'
        self.method = 'GET'
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
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = original_viewer.cur_agent
        self.cur_site = original_viewer.cur_site
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        self.context['layout'] = 'blank.html'

    def init_for_outgoing_email(self, agent):
        self.permission_cache = PermissionCache()
        self.request = None
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
        self.cur_agent = agent
        self.cur_site = get_default_site()
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        self.context['layout'] = 'blank.html'

    def dispatch(self):
        if self.noun is None:
            action_method = getattr(self, 'type_%s_%s' % (self.action, self.format), None)
        else:
            action_method = getattr(self, 'item_%s_%s' % (self.action, self.format), None)
        if action_method:
            if self.noun != None:
                if self.item is None:
                    return self.render_item_not_found()
                elif self.action == 'copy':
                    pass
                else:
                    if not isinstance(self.item, self.accepted_item_type):
                        return self.render_item_not_found()
            return action_method()
        else:
            return None

    def render_item_not_found(self):
        if self.item:
            title = "%s Not Found" % self.accepted_item_type.__name__
            body = 'You cannot view item %s in this viewer. Try viewing it in the <a href="%s">%s viewer</a>.' % (self.noun, reverse('item_url', kwargs={'viewer': self.item.item_type_string.lower(), 'noun': self.item.pk}), self.item.item_type_string)
        else:
            title = "Item Not Found"
            version = self.request.GET.get('version')
            if version is None:
                body = 'There is no item %s.' % self.noun
            else:
                body = 'There is no item %s version %s.' % (self.noun, version)
        return self.render_error(HttpResponseNotFound, title, body)

    def _set_default_layout(self):
        cur_node = self.cur_site.default_layout
        while cur_node is not None:
            next_node = cur_node.layout
            if next_node is None:
                if cur_node.override_default_layout:
                    extends_string = ''
                else:
                    extends_string = "{% extends 'default_layout.html' %}\n"
            else:
                extends_string = "{%% extends layout%s %%}\n" % next_node.pk
            if self.permission_cache.agent_can(self.cur_agent, 'view body', cur_node):
                template_string = extends_string + cur_node.body
            else:
                template_string = "{% extends 'default_layout.html' %}\n"
                self.context['layout_permissions_problem'] = True
                next_node = None
            t = loader.get_template_from_string(template_string)
            self.context['layout%d' % cur_node.pk] = t
            cur_node = next_node
        if self.cur_site.default_layout:
            self.context['layout'] = self.context['layout%s' % self.cur_site.default_layout.pk]
        else:
            self.context['layout'] = 'default_layout.html'



def get_viewer_class_for_viewer_name(viewer_name):
    return ViewerMetaClass.viewer_name_dict.get(viewer_name, None)


def get_versioned_item(item, version_number):
    if version_number is not None:
        item.copy_fields_from_version(version_number)
    return item


###############################################################################
# Viewers
###############################################################################

class CodeGraphViewer(Viewer):
    accepted_item_type = Item
    viewer_name = 'codegraph'

    def type_list_html(self):
        """
        Generate images for the graph of the Deme item type ontology, and
        display a page with links to them.
        """
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
        return HttpResponse(template.render(self.context))


class ItemViewer(Viewer):
    accepted_item_type = Item
    viewer_name = 'item'

    def _type_list_helper(self):
        if self.request.GET.get('collection'):
            collection = Item.objects.get(pk=self.request.GET.get('collection')).downcast()
        else:
            collection = None
        offset = int(self.request.GET.get('offset', 0))
        limit = int(self.request.GET.get('limit', 100))
        active = self.request.GET.get('active', '1') == '1'
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name_plural': x._meta.verbose_name_plural, 'item_type': x} for x in item_type_name_dict.itervalues() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['search_query'] = self.request.GET.get('q', '')
        items = self.accepted_item_type.objects
        if self.context['search_query']:
            q = self.context['search_query']
            search_filter = Q(name__icontains=q)
            # This is commented out because it's too simplistic, and does not respect permissions.
            # search_filter = search_filter | Q(description__icontains=q)
            # if self.accepted_item_type == Item:
            #     search_filter = search_filter | Q(document__textdocument__body__icontains=q)
            # elif self.accepted_item_type == Document:
            #     search_filter = search_filter | Q(textdocument__body__icontains=q)
            # elif issubclass(self.accepted_item_type, TextDocument):
            #     search_filter = search_filter | Q(body__icontains=q)
            items = items.filter(search_filter)
        if isinstance(collection, Collection):
            if self.cur_agent_can_global('do_anything'):
                recursive_filter = None
            else:
                visible_memberships = self.permission_cache.filter_items(self.cur_agent, 'view item', Membership.objects)
                recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
            items = items.filter(pk__in=collection.all_contained_collection_members(recursive_filter).values('pk').query)
        listable_items = self.permission_cache.filter_items(self.cur_agent, 'view name', items)
        n_opposite_active_items = listable_items.filter(active=(not active)).count()
        listable_items = listable_items.filter(active=active)
        listable_items = listable_items.order_by('id')
        n_items = items.count()
        n_listable_items = listable_items.count()
        items = [item for item in listable_items.all()[offset:offset+limit]]
        self.context['item_types'] = item_types
        self.context['items'] = items
        self.context['n_items'] = n_items
        self.context['n_listable_items'] = n_listable_items
        self.context['n_unlistable_items'] = n_items - n_listable_items - n_opposite_active_items
        self.context['n_opposite_active_items'] = n_opposite_active_items
        self.context['offset'] = offset
        self.context['limit'] = limit
        self.context['list_start_i'] = offset + 1
        self.context['list_end_i'] = min(offset + limit, n_listable_items)
        self.context['active'] = active
        self.context['collection'] = collection
        self.context['all_collections'] = self.permission_cache.filter_items(self.cur_agent, 'view name', Collection.objects.filter(active=True)).order_by('name')

    def type_list_html(self):
        self._type_list_helper()
        template = loader.get_template('item/list.html')
        return HttpResponse(template.render(self.context))
        if self.format == 'json':
            json_data = simplejson.dumps([[item.name, item.pk] for item in items], separators=(',',':'))
            return HttpResponse(json_data, mimetype='application/json')

    def type_list_json(self):
        self._type_list_helper()
        data = [[item.name, item.pk] for item in self.context['items']]
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def type_list_rss(self):
        self._type_list_helper()
        item_list = self.context['items'] #TODO probably not useful to get this ordering
        #TODO permissions to view name/description
        class ItemListFeed(django.contrib.syndication.feeds.Feed):
            title = "Items"
            description = "Items"
            link = reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'list', 'format': 'rss'})
            def items(self):
                return item_list
            def item_link(self, item):
                return item.get_absolute_url()
            def item_pubdate(self, item):
                return item.created_at
        return django.contrib.syndication.views.feed(self.request, 'item_list', {'item_list': ItemListFeed})

    def type_new_html(self):
        can_create = self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.accepted_item_type.__name__)
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        can_create = self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.accepted_item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    def item_show_html(self):
        template = loader.get_template('item/show.html')
        return HttpResponse(template.render(self.context))

    def item_show_rss(self):
        from cms.templatetags.item_tags import get_viewable_name
        viewer = self
        if not self.cur_agent_can('view_action_notices', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to view action notices for this item")
        action_notices = ActionNotice.objects.filter(Q(item=self.item) | Q(creator=self.item)).order_by('created_at') #TODO limit
        action_notice_pk_to_object_map = {}
        for action_notice_subclass in [RelationActionNotice, DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, CreateActionNotice, EditActionNotice]:
            specific_action_notices = action_notice_subclass.objects.filter(pk__in=action_notices.values('pk').query)
            if action_notice_subclass == RelationActionNotice:
                self.permission_cache.mass_learn(self.cur_agent, 'view name', Item.objects.filter(Q(pk__in=specific_action_notices.values('from_item').query)))
            for action_notice in specific_action_notices:
                action_notice_pk_to_object_map[action_notice.pk] = action_notice
        self.permission_cache.mass_learn(self.cur_agent, 'view name', Item.objects.filter(Q(pk__in=action_notices.values('item').query) | Q(pk__in=action_notices.values('creator').query)))
        class ItemShowFeed(django.contrib.syndication.feeds.Feed):
            title = get_viewable_name(viewer.context, viewer.item)
            description = viewer.item.description if viewer.cur_agent_can('view description', viewer.item) else ''
            link = reverse('item_url', kwargs={'viewer': viewer.viewer_name, 'action': 'show', 'noun': viewer.item.pk, 'format': 'rss'})
            def items(self):
                result = []
                for action_notice in action_notices:
                    action_notice = action_notice_pk_to_object_map[action_notice.pk]
                    if isinstance(action_notice, RelationActionNotice):
                        if not viewer.cur_agent_can('view %s' % action_notice.from_field_name, action_notice.from_item):
                            continue
                    item = {}
                    item['created_at'] = action_notice.created_at
                    item['creator_name'] = get_viewable_name(viewer.context, action_notice.creator)
                    item['creator_link'] = action_notice.creator.get_absolute_url()
                    item['item_name'] = get_viewable_name(viewer.context, action_notice.item)
                    item['description'] = action_notice.description
                    if isinstance(action_notice, RelationActionNotice):
                        item['from_item_name'] = get_viewable_name(viewer.context, action_notice.from_item)
                        item['from_field_name'] = action_notice.from_field_name
                        item['relation_added'] = action_notice.relation_added
                        item['link'] = action_notice.from_item.get_absolute_url()
                    else:
                        item['link'] = action_notice.item.get_absolute_url()
                    item['action_notice_type'] = type(action_notice).__name__
                    result.append(item)
                return result
            def item_link(self, item):
                return item['link']
            def item_pubdate(self, item):
                return item['created_at']
        return django.contrib.syndication.views.feed(self.request, 'item_show', {'item_show': ItemShowFeed})

    def item_history_html(self):
        import copy
        versions = []
        for version_number in xrange(1, self.item.version_number + 1):
            versioned_item = copy.deepcopy(self.item)
            versioned_item.copy_fields_from_version(version_number)
            versions.append(versioned_item)
        template = loader.get_template('item/history.html')
        self.context['versions'] = versions
        return HttpResponse(template.render(self.context))

    def item_relationships_html(self):
        relationship_sets = []
        for name in sorted(self.item._meta.get_all_field_names()):
            field, model, direct, m2m = self.item._meta.get_field_by_name(name)
            if type(field).__name__ != 'RelatedObject':
                continue
            if type(field.field).__name__ != 'ForeignKey':
                continue
            if issubclass(field.model, (ItemPermission, GlobalPermission)):
                continue
            if not issubclass(field.model, Item):
                continue
            manager = getattr(self.item, name)
            relationship_set = {}
            relationship_set['name'] = name
            viewable_items = manager.filter(active=True)
            if viewable_items.count() == 0:
                continue
            relationship_item_type = manager.model
            self.permission_cache.mass_learn(self.cur_agent, 'view name', viewable_items)
            viewable_items = self.permission_cache.filter_items(self.cur_agent, 'view %s' % field.field.name, viewable_items)
            relationship_set['items'] = viewable_items
            relationship_sets.append(relationship_set)
        template = loader.get_template('item/relationships.html')
        self.context['relationship_sets'] = relationship_sets
        self.context['abilities'] = sorted(self.permission_cache.item_abilities(self.cur_agent, self.item))
        return HttpResponse(template.render(self.context))

    def item_edit_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.accepted_item_type, fields_can_edit)
        form = form_class(instance=self.item)
        fields_can_view = set([x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'view'])
        initial_fields_set = set(form.initial.iterkeys())
        fields_must_blank = initial_fields_set - fields_can_view
        for field_name in fields_must_blank:
            del form.initial[field_name]
        template = loader.get_template('item/edit.html')
        self.context['form'] = form
        self.context['query_string'] = self.request.META['QUERY_STRING']
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    def item_copy_html(self):
        can_create = self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.accepted_item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        fields_to_copy = [field_name for field_name in form_class.base_fields if self.cur_agent_can('view %s' % field_name, self.item)]
        form_initial = {}
        for field_name in fields_to_copy:
            try:
                field_value = getattr(self.item, field_name)
            except AttributeError:
                continue
            if isinstance(field_value, models.Model):
                field_value = field_value.pk
            form_initial[field_name] = field_value
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['action_is_item_copy'] = True
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        if 'redirect' in self.request.GET:
            self.context['redirect'] = self.request.GET['redirect']
        return HttpResponse(template.render(self.context))

    def item_update_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        new_item = self.item
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.accepted_item_type, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            return HttpResponseRedirect(reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/edit.html')
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))

    def item_deactivate_html(self):
        if self.method == 'GET':
            return self.render_error(HttpResponseBadRequest, 'Invalid Method', "You cannot visit this URL using the GET method")
        if not self.item.can_be_deleted() or not self.cur_agent_can('delete', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to deactivate this item")
        self.item.deactivate(action_agent=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def item_reactivate_html(self):
        if self.method == 'GET':
            return self.render_error(HttpResponseBadRequest, 'Invalid Method', "You cannot visit this URL using the GET method")
        if not self.item.can_be_deleted() or not self.cur_agent_can('delete', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to reactivate this item")
        self.item.reactivate(action_agent=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def item_destroy_html(self):
        if self.method == 'GET':
            return self.render_error(HttpResponseBadRequest, 'Invalid Method', "You cannot visit this URL using the GET method")
        if not self.item.can_be_deleted() or not self.cur_agent_can('delete', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to destroy this item")
        self.item.destroy(action_agent=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def item_itempermissions_html(self):
        can_modify_permissions = self.cur_agent_can('do_anything', self.item)
        if not can_modify_permissions:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify permissions of this item")

        def formfield_callback(f):
            if f.name in ['agent', 'collection', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(AgentItemPermission, fields=['agent', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        collection_permission_form_class = forms.models.modelform_factory(CollectionItemPermission, fields=['collection', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        everyone_permission_form_class = forms.models.modelform_factory(EveryoneItemPermission, fields=['item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'collectionpermission':
                form_class = collection_permission_form_class
            elif form_type == 'everyonepermission':
                form_class = everyone_permission_form_class
            else:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Type', "You submitted a permission form with an invalid formtype parameter")

            if self.request.POST.get('permission_to_delete') is not None:
                permission = form_class._meta.model.objects.get(pk=self.request.POST.get('permission_to_delete'))
                permission.delete()
                redirect = self.request.GET['redirect']
                return HttpResponseRedirect(redirect)

            form = form_class(self.request.POST, self.request.FILES, prefix=self.request.GET['formprefix'])
            if form.is_valid():
                item = form.save(commit=False)
                item.save()
                redirect = self.request.GET['redirect']
                return HttpResponseRedirect(redirect)
            elif form.non_field_errors(): # there may have been a duplicate
                model = form._meta.model
                fields = form._meta.fields
                existing_permission = model.objects
                for field in fields:
                    data = form[field].data
                    if field == 'agent':
                        existing_permission = existing_permission.filter(agent__pk=data)
                    elif field == 'collection':
                        existing_permission = existing_permission.filter(collection__pk=data)
                    elif field == 'item':
                        existing_permission = existing_permission.filter(item__pk=data)
                    elif field == 'ability':
                        existing_permission = existing_permission.filter(ability=data)
                try:
                    existing_permission = existing_permission.get()
                except ObjectDoesNotExist:
                    existing_permission = None
                if existing_permission:
                    if 'is_allowed' in fields and existing_permission.is_allowed != form['is_allowed'].data:
                        existing_permission.is_allowed = form['is_allowed'].data
                        existing_permission.save()
                    redirect = self.request.GET['redirect']
                    return HttpResponseRedirect(redirect)
                else:
                    # we'll display it in the regular page below as an invalid form
                    pass

        agent_permissions = self.item.agent_item_permissions_as_item.order_by('ability')
        collection_permissions = self.item.collection_item_permissions_as_item.order_by('ability')
        everyone_permissions = self.item.everyone_item_permissions_as_item.order_by('ability')
        agents = Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        collections = Collection.objects.filter(Q(pk__in=collection_permissions.values('collection__pk').query) | Q(pk=self.request.GET.get('collection', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'item': self.item.pk, 'agent': agent.pk})
            agent_data.append(agent_datum)
        collection_data = []
        for collection in collections:
            collection_datum = {}
            collection_datum['collection'] = collection
            collection_datum['permissions'] = collection_permissions.filter(collection=collection)
            collection_datum['permission_form'] = collection_permission_form_class(prefix="collection%s" % collection.pk, initial={'item': self.item.pk, 'collection': collection.pk})
            collection_data.append(collection_datum)
        everyone_data = {}
        everyone_data['permissions'] = everyone_permissions
        everyone_data['permission_form'] = everyone_permission_form_class(prefix="everyone", initial={'item': self.item.pk})

        # now include the error form
        if self.method == 'POST':
            if form_type == 'agentpermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['permission_form'] = form
                agent_datum['permission_form_invalid'] = True
            elif form_type == 'collectionpermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['permission_form'] = form
                collection_datum['permission_form_invalid'] = True
            elif form_type == 'everyonepermission':
                everyone_data['permission_form'] = form
                everyone_data['permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(AgentItemPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_collection_form_class = forms.models.modelform_factory(CollectionItemPermission, fields=['collection'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/itempermissions.html')
        self.context['agent_data'] = agent_data
        self.context['collection_data'] = collection_data
        self.context['everyone_data'] = everyone_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_collection_form'] = new_collection_form_class()
        return HttpResponse(template.render(self.context))

    def type_globalpermissions_html(self):
        if not self.cur_agent_can_global('do_anything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify global permissions")

        def formfield_callback(f):
            if f.name in ['agent', 'collection', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(AgentGlobalPermission, fields=['agent', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        collection_permission_form_class = forms.models.modelform_factory(CollectionGlobalPermission, fields=['collection', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        everyone_permission_form_class = forms.models.modelform_factory(EveryoneGlobalPermission, fields=['ability', 'is_allowed'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'collectionpermission':
                form_class = collection_permission_form_class
            elif form_type == 'everyonepermission':
                form_class = everyone_permission_form_class
            else:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Type', "You submitted a permission form with an invalid formtype parameter")

            if self.request.POST.get('permission_to_delete') is not None:
                permission = form_class._meta.model.objects.get(pk=self.request.POST.get('permission_to_delete'))
                if isinstance(permission, AgentGlobalPermission) and permission.agent.pk == 1 and permission.ability == 'do_anything':
                    # Don't delete the admin permission, it may be difficult to get back.
                    pass
                else:
                    permission.delete()
                redirect = self.request.GET['redirect']
                return HttpResponseRedirect(redirect)

            form = form_class(self.request.POST, self.request.FILES, prefix=self.request.GET['formprefix'])
            if form.is_valid():
                item = form.save(commit=False)
                item.save()
                redirect = self.request.GET['redirect']
                return HttpResponseRedirect(redirect)
            else:
                model = form._meta.model
                fields = form._meta.fields
                existing_permission = model.objects
                for field in fields:
                    data = form[field].data
                    if field == 'agent':
                        existing_permission = existing_permission.filter(agent__pk=data)
                    elif field == 'collection':
                        existing_permission = existing_permission.filter(collection__pk=data)
                    elif field == 'ability':
                        existing_permission = existing_permission.filter(ability=data)
                try:
                    existing_permission = existing_permission.get()
                except ObjectDoesNotExist:
                    existing_permission = None
                if existing_permission:
                    if isinstance(existing_permission, AgentGlobalPermission) and existing_permission.agent.pk == 1 and existing_permission.ability == 'do_anything':
                        # Don't delete the admin permission, it may be difficult to get back.
                        pass
                    else:
                        if 'is_allowed' in fields and existing_permission.is_allowed != form['is_allowed'].data:
                            existing_permission.is_allowed = form['is_allowed'].data
                            existing_permission.save()
                    redirect = self.request.GET['redirect']
                    return HttpResponseRedirect(redirect)
                else:
                    # we'll display it in the regular page below as an invalid form
                    pass

        agent_permissions = AgentGlobalPermission.objects.order_by('ability')
        collection_permissions = CollectionGlobalPermission.objects.order_by('ability')
        everyone_permissions = EveryoneGlobalPermission.objects.order_by('ability')
        agents = Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        collections = Collection.objects.filter(Q(pk__in=collection_permissions.values('collection__pk').query) | Q(pk=self.request.GET.get('collection', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'agent': agent.pk})
            agent_data.append(agent_datum)
        collection_data = []
        for collection in collections:
            collection_datum = {}
            collection_datum['collection'] = collection
            collection_datum['permissions'] = collection_permissions.filter(collection=collection)
            collection_datum['permission_form'] = collection_permission_form_class(prefix="collection%s" % collection.pk, initial={'collection': collection.pk})
            collection_data.append(collection_datum)
        everyone_data = {}
        everyone_data['permissions'] = everyone_permissions
        everyone_data['permission_form'] = everyone_permission_form_class(prefix="everyone", initial={})

        # now include the error form
        if self.method == 'POST':
            if form_type == 'agentpermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['permission_form'] = form
                agent_datum['permission_form_invalid'] = True
            elif form_type == 'collectionpermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['permission_form'] = form
                collection_datum['permission_form_invalid'] = True
            elif form_type == 'everyonepermission':
                everyone_data['permission_form'] = form
                everyone_data['permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(AgentGlobalPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_collection_form_class = forms.models.modelform_factory(CollectionGlobalPermission, fields=['collection'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/globalpermissions.html')
        self.context['agent_data'] = agent_data
        self.context['collection_data'] = collection_data
        self.context['everyone_data'] = everyone_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_collection_form'] = new_collection_form_class()
        return HttpResponse(template.render(self.context))


class ContactMethodViewer(ItemViewer):
    accepted_item_type = ContactMethod
    viewer_name = 'contactmethod'

    def type_new_html(self):
        try:
            agent = Item.objects.get(pk=self.request.GET.get('agent'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the agent you are adding an contact method to")
        can_add_contact_method = self.cur_agent_can('add_contact_method', agent)
        if not can_add_contact_method:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add contact methods to this agent")
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            can_add_contact_method = self.cur_agent_can('add_contact_method', item.agent)
            if not can_add_contact_method:
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add contact methods to this agent")
            item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))


class AuthenticationMethodViewer(ItemViewer):
    accepted_item_type = AuthenticationMethod
    viewer_name = 'authenticationmethod'

    def type_new_html(self):
        try:
            agent = Item.objects.get(pk=self.request.GET.get('agent'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the agent you are adding an authentication method to")
        can_add_authentication_method = self.cur_agent_can('add_authentication_method', agent)
        if not can_add_authentication_method:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add authentication methods to this agent")
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            can_add_authentication_method = self.cur_agent_can('add_authentication_method', item.agent)
            if not can_add_authentication_method:
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add authentication methods to this agent")
            item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    def type_login_html(self):
        """
        This is the view that takes care of all URLs dealing with logging in
        and logging out.
        """
        if self.request.method == 'GET':
            # If getencryptionmethod is a key in the query string, return a JSON
            # response with the details about the PasswordAuthenticationMethod
            # necessary for JavaScript to encrypt the password.
            if 'getencryptionmethod' in self.request.GET:
                username = self.request.GET['getencryptionmethod']
                nonce = PasswordAuthenticationMethod.get_random_hash()[:5]
                self.request.session['login_nonce'] = nonce
                try:
                    password = PasswordAuthenticationMethod.objects.get(username=username).password
                    algo, salt, hsh = password.split('$')
                    response_data = {'nonce':nonce, 'algo':algo, 'salt':salt}
                except ObjectDoesNotExist:
                    response_data = {'nonce':nonce, 'algo':'sha1', 'salt':'x'}
                json_data = simplejson.dumps(response_data, separators=(',',':'))
                return HttpResponse(json_data, mimetype='application/json')
            # If openidcomplete is a key in the query string, the user has just
            # authenticated with OpenID
            elif 'openidcomplete' in self.request.GET:
                redirect = self.request.GET['redirect']
                try:
                    import openid.consumer.consumer
                except ImportError:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID is not supported in this installation")
                consumer = openid.consumer.consumer.Consumer(self.request.session, None)
                query_dict = dict((k,v) for k,v in self.request.GET.items())
                current_url = self.request.build_absolute_uri().split('?')[0]
                openid_response = consumer.complete(query_dict, current_url)
                
                if openid_response.status == openid.consumer.consumer.SUCCESS:
                    identity_url = openid_response.identity_url
                    display_identifier = openid_response.getDisplayIdentifier()
                    sreg = openid_response.extensionResponse('sreg', False)
                    try:
                        openid_authentication_method = OpenidAuthenticationMethod.objects.get(openid_url=identity_url)
                    except ObjectDoesNotExist:
                        # No OpenidAuthenticationMethod has this openid_url.
                        return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that OpenID")
                    if not openid_authentication_method.active or not openid_authentication_method.agent.active: 
                        # The Agent or OpenidAuthenticationMethod is inactive.
                        return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that OpenID")
                    self.request.session['cur_agent_id'] = openid_authentication_method.agent.pk
                    return HttpResponseRedirect(redirect)
                elif openid_response.status == openid.consumer.consumer.CANCEL:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID request was cancelled")
                elif openid_response.status == openid.consumer.consumer.FAILURE:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID error: %s" % escape(openid_response.message))
                elif openid_response.status == openid.consumer.consumer.SETUP_NEEDED:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID setup needed")
                else:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "Invalid OpenID status: %s" % escape(openid_response.status))
            # Otherwise, return the login.html page.
            else:
                login_as_agents = Agent.objects.filter(active=True).order_by('name')
                login_as_agents = self.permission_cache.filter_items(self.cur_agent, 'login_as', login_as_agents)
                self.permission_cache.mass_learn(self.cur_agent, 'view name', login_as_agents)
                template = loader.get_template('login.html')
                self.context['redirect'] = self.request.GET['redirect']
                self.context['login_as_agents'] = login_as_agents
                return HttpResponse(template.render(self.context))
        else:
            # The user just submitted a login form, so we try to authenticate.
            redirect = self.request.GET['redirect']
            login_type = self.request.POST['login_type']
            if login_type == 'logout':
                if 'cur_agent_id' in self.request.session:
                    del self.request.session['cur_agent_id']
                return HttpResponseRedirect(redirect)
            elif login_type == 'password':
                nonce = self.request.session['login_nonce']
                del self.request.session['login_nonce']
                username = self.request.POST['username']
                hashed_password = self.request.POST['hashed_password']
                try:
                    password_authentication_method = PasswordAuthenticationMethod.objects.get(username=username)
                except ObjectDoesNotExist:
                    # No PasswordAuthenticationMethod has this username.
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
                if not password_authentication_method.active or not password_authentication_method.agent.active:
                    # The Agent or PasswordAuthenticationMethod is inactive.
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
                if password_authentication_method.check_nonced_password(hashed_password, nonce):
                    self.request.session['cur_agent_id'] = password_authentication_method.agent.pk
                    return HttpResponseRedirect(redirect)
                else:
                    # The password given does not correspond to the PasswordAuthenticationMethod.
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
            elif login_type == 'login_as':
                for key in self.request.POST.iterkeys():
                    if key.startswith('login_as_'):
                        new_agent_id = key.split('login_as_')[1]
                        try:
                            new_agent = Agent.objects.get(pk=new_agent_id)
                        except ObjectDoesNotExist:
                            # There is no Agent with the specified id.
                            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
                        if not new_agent.active:
                            # The specified agent is inactive.
                            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
                        if self.permission_cache.agent_can(self.cur_agent, 'login_as', new_agent):
                            self.request.session['cur_agent_id'] = new_agent.pk
                            return HttpResponseRedirect(redirect)
                        else:
                            # The current agent does not have permission to login_as the specified agent.
                            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")
            elif login_type == 'openid':
                try:
                    import openid.consumer.consumer
                except ImportError:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "OpenID is not supported in this installation")
                trust_root = self.request.build_absolute_uri('/')
                full_redirect = self.request.build_absolute_uri('%s?openidcomplete=1&redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'login'}), urlquote(redirect)))
                user_url = self.request.POST['openid_url']
                consumer = openid.consumer.consumer.Consumer(self.request.session, None)
                try:
                    auth_request = consumer.begin(user_url)
                except openid.consumer.consumer.DiscoveryFailure:
                    return self.render_error(HttpResponseBadRequest, "Authentication Failed", "Invalid OpenID URL")
                auth_request.addExtensionArg('sreg', 'optional', 'nickname,email,fullname')
                return HttpResponseRedirect(auth_request.redirectURL(trust_root, full_redirect))
            # Invalid login_type parameter.
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There was a problem with your login form")


class WebauthAuthenticationMethodViewer(ItemViewer):
    accepted_item_type = WebauthAuthenticationMethod
    viewer_name = 'webauth'

    def type_login_html(self):
        if not self.request.is_secure():
            return HttpResponseRedirect('https://%s%s' % (self.request.get_host(), self.request.get_full_path()))
        if self.request.META.get('AUTH_TYPE') != 'WebAuth' or not self.request.META.get('REMOTE_USER'):
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "WebAuth is not supported in this installation")
        username = self.request.META['REMOTE_USER']
        try:
            webauth_authentication_method = WebauthAuthenticationMethod.objects.get(username=username)
        except ObjectDoesNotExist:
            # No WebauthAuthenticationMethod has this username.
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that webauth username")
        if not webauth_authentication_method.active or not webauth_authentication_method.agent.active: 
            # The Agent or WebauthAuthenticationMethod is inactive.
            return self.render_error(HttpResponseBadRequest, "Authentication Failed", "There is no active agent with that webauth username")
        self.request.session['cur_agent_id'] = webauth_authentication_method.agent.pk
        redirect = self.request.GET['redirect']
        return HttpResponseRedirect(redirect)


class GroupViewer(ItemViewer):
    accepted_item_type = Group
    viewer_name = 'group'

    def type_create_html(self):
        can_create = self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.accepted_item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            return HttpResponseRedirect(reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))

    def item_show_html(self):
        template = loader.get_template('group/show.html')
        return HttpResponse(template.render(self.context))


class ViewerRequestViewer(ItemViewer):
    accepted_item_type = ViewerRequest
    viewer_name = 'viewerrequest'

    def item_show_html(self):
        site, custom_urls = self.item.calculate_full_path()
        self.context['site'] = site
        self.context['custom_urls'] = custom_urls
        self.context['child_urls'] = self.item.child_urls.filter(active=True)
        self.context['addsubpath_form'] = AddSubPathForm(initial={'parent_url':self.item.pk})
        template = loader.get_template('viewerrequest/show.html')
        return HttpResponse(template.render(self.context))


    def item_addsubpath_html(self):
        form = AddSubPathForm(self.request.POST, self.request.FILES)
        if form.data['parent_url'] != str(self.item.pk):
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the parent url you are extending")
        if not self.cur_agent_can('add_sub_path', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add a sub path to this url")
        try:
            custom_url = CustomUrl.objects.get(parent_url=self.item, path=form.data['path'])
        except ObjectDoesNotExist:
            custom_url = None
        form = AddSubPathForm(self.request.POST, self.request.FILES, instance=custom_url)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            if not new_item.active:
                new_item.reactivate(action_agent=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            site, custom_urls = self.item.calculate_full_path()
            self.context['site'] = site
            self.context['custom_urls'] = custom_urls
            self.context['child_urls'] = self.item.child_urls.filter(active=True)
            self.context['addsubpath_form'] = form
            template = loader.get_template('viewerrequest/show.html')
            return HttpResponse(template.render(self.context))


class CollectionViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'collection'

    def item_show_html(self):
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items(self.cur_agent, 'view item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.mass_learn(self.cur_agent, 'view name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can(self.cur_agent, 'view name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        self.context['addmember_form'] = NewMembershipForm()
        template = loader.get_template('collection/show.html')
        return HttpResponse(template.render(self.context))


    def item_addmember_html(self):
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('add_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add this member to this Collection")
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if not membership.active:
                membership.reactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            membership = Membership(collection=self.item, item=member)
            membership.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


    def item_removemember_html(self):
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('remove_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to remove this member from this Collection")
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if membership.active:
                membership.deactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            pass
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


class ImageDocumentViewer(ItemViewer):
    accepted_item_type = ImageDocument
    viewer_name = 'imagedocument'

    def item_show_html(self):
        template = loader.get_template('imagedocument/show.html')
        return HttpResponse(template.render(self.context))


class TextDocumentViewer(ItemViewer):
    accepted_item_type = TextDocument
    viewer_name = 'textdocument'

    def item_show_html(self):
        template = loader.get_template('textdocument/show.html')
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))


    def item_edit_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.accepted_item_type, fields_can_edit)


        transclusions = Transclusion.objects.filter(from_item=self.item, from_item_version_number=self.item.version_number).order_by('-from_item_index')
        body_as_list = list(self.item.body)
        for transclusion in transclusions:
            if issubclass(self.accepted_item_type, HtmlDocument):
                transclusion_text = '<img id="transclusion_%s" src="/static/spacer.gif" title="Comment %s" style="margin: 0 2px 0 2px; background: #ddd; border: 1px dotted #777; height: 10px; width: 10px;"/>' % (transclusion.to_item_id, transclusion.to_item_id)
            else:
                transclusion_text = '<deme_transclusion id="%s"/>' % transclusion.to_item_id
            i = transclusion.from_item_index
            body_as_list[i:i] = transclusion_text
        self.item.body = ''.join(body_as_list)

        form = form_class(instance=self.item)
        fields_can_view = set([x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'view'])
        initial_fields_set = set(form.initial.iterkeys())
        fields_must_blank = initial_fields_set - fields_can_view
        for field_name in fields_must_blank:
            del form.initial[field_name]
        template = loader.get_template('item/edit.html')
        self.context['form'] = form
        self.context['query_string'] = self.request.META['QUERY_STRING']
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    def item_update_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        new_item = self.item
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.accepted_item_type, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)

            new_transclusions = []
            while True:
                def repl(m):
                    index = m.start()
                    to_item_id = m.group(1)
                    new_transclusions.append((index, to_item_id))
                    return ''
                if issubclass(self.accepted_item_type, HtmlDocument):
                    transclusion_re = r'(?i)<img[^>]+transclusion_(\d+)[^>]*>'
                else:
                    transclusion_re = r'<deme_transclusion id="(\d+)"/>'
                new_item.body, n_subs = re.subn(transclusion_re, repl, new_item.body, 1)
                if n_subs == 0:
                    break
            
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))

            for index, to_item_id in new_transclusions:
                try:
                    to_item = Item.objects.get(pk=to_item_id)
                except:
                    to_item = None
                if to_item:
                    transclusion = Transclusion()
                    transclusion.from_item = new_item
                    transclusion.from_item_index = index
                    transclusion.from_item_version_number = new_item.version_number
                    transclusion.to_item = to_item
                    transclusion.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))

            return HttpResponseRedirect(reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/edit.html')
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    accepted_item_type = DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def item_render_html(self):
        cur_node = self.item
        while cur_node is not None:
            next_node = cur_node.layout
            if cur_node.override_default_layout:
                template_string = cur_node.body
            else:
                if self.cur_agent_can('view body', cur_node):
                    template_string = '{%% extends layout%s %%}\n%s' % (next_node.pk if next_node else '', cur_node.body)
                else:
                    template_string = "{%% extends 'default_layout.html' %%}\n%s" % (cur_node.body,)
                    self.context['layout_permissions_problem'] = True
                    next_node = None
            t = loader.get_template_from_string(template_string)
            if cur_node is self.item:
                template = t
            else:
                self.context['layout%d' % cur_node.pk] = t
            cur_node = next_node
        return HttpResponse(template.render(self.context))


class TextCommentViewer(TextDocumentViewer):
    accepted_item_type = TextComment
    viewer_name = 'textcomment'

    def type_new_html(self):
        try:
            item = Item.objects.get(pk=self.request.GET.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are commenting on")
        can_comment_on = self.cur_agent_can('comment_on', item)
        if not can_comment_on:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to comment on this item")
        form_initial = dict(self.request.GET.items())
        form_class = NewTextCommentForm
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        try:
            item = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are commenting on")
        can_comment_on = self.cur_agent_can('comment_on', item)
        if not can_comment_on:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to comment on this item")
        form_class = NewTextCommentForm
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the Transclusion save at the same time as the Comment
            item_index = form.cleaned_data['item_index']
            comment = form.save(commit=False)
            comment.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            item = comment.item.downcast()
            if isinstance(item, TextDocument) and item_index is not None and self.permission_cache.agent_can(self.cur_agent, 'add_transclusion', item):
                transclusion = Transclusion(from_item=item, from_item_version_number=comment.item_version_number, from_item_index=item_index, to_item=comment)
                transclusion.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': comment.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update comments


class TransclusionViewer(ItemViewer):
    accepted_item_type = Transclusion
    viewer_name = 'transclusion'

    def type_new_html(self):
        try:
            from_item = Item.objects.get(pk=self.request.GET.get('from_item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are adding a transclusion to")
        can_add_transclusion = self.cur_agent_can('add_transclusion', from_item)
        if not can_add_transclusion:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add transclusions to this item")
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the Transclusion save at the same time as the Comment
            item = form.save(commit=False)
            can_add_transclusion = self.cur_agent_can('add_transclusion', item.from_item)
            if not can_add_transclusion:
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add transclusions to this item")
            item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update transclusions


class TextDocumentExcerptViewer(TextDocumentViewer):
    accepted_item_type = TextDocumentExcerpt
    viewer_name = 'textdocumentexcerpt'

    def type_createmultiexcerpt_html(self):
        if not self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.accepted_item_type.__name__)
        if not self.cur_agent_can_global('create Collection'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create Collections")
        excerpts = []
        for excerpt_form_datum in self.request.POST.getlist('excerpt'):
            try:
                text_document_id, text_document_version_number, start_index, length = excerpt_form_datum.split(' ')
                start_index = int(start_index)
                length = int(length)
            except ValueError:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Data', "Could not parse the excerpt data in the form")
            try:
                text_document = get_versioned_item(TextDocument.objects.get(pk=text_document_id), text_document_version_number)
            except:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Data', "Could not find the specified TextDocument")
            if not self.cur_agent_can('view body', text_document):
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to view the body of this item")
            body = text_document.body[start_index:start_index+length]
            excerpt = TextDocumentExcerpt(body=body, text_document=text_document, text_document_version_number=text_document_version_number, start_index=start_index, length=length)
            excerpts.append(excerpt)
        if not excerpts:
            return self.render_error(HttpResponseBadRequest, 'Invalid Form Data', "You must submit at least one excerpt")
        collection = Collection()
        collection.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        for excerpt in excerpts:
            excerpt.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            Membership(item=excerpt, collection=collection).save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': 'collection', 'noun': collection.pk}))
        return HttpResponseRedirect(redirect)


class DemeSettingViewer(ItemViewer):
    accepted_item_type = DemeSetting
    viewer_name = 'demesetting'

    def type_modify_html(self):
        if not self.cur_agent_can_global('do_anything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify DemeSettings")
        self.context['deme_settings'] = DemeSetting.objects.filter(active=True).order_by('key')
        template = loader.get_template('demesetting/modify.html')
        return HttpResponse(template.render(self.context))

    def type_addsetting_html(self):
        if not self.cur_agent_can_global('do_anything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify DemeSettings")
        key = self.request.POST.get('key')
        value = self.request.POST.get('value')
        DemeSetting.set(key, value, self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'modify'}))
        return HttpResponseRedirect(redirect)


class SubscriptionViewer(ItemViewer):
    accepted_item_type = Subscription
    viewer_name = 'subscription'

    def type_new_html(self):
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def type_create_html(self):
        form_class = get_form_class_for_item_type('create', self.accepted_item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            can_add_subscription = self.cur_agent_can('add_subscription', item.contact_method)
            if not can_add_subscription:
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add subscriptions to this contact method")
            item.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))


# Dynamically create default viewers for the ones we don't have.
for item_type in all_item_types():
    viewer_name = item_type.__name__.lower()
    if viewer_name not in ViewerMetaClass.viewer_name_dict:
        parent_item_type_with_viewer = item_type
        while issubclass(parent_item_type_with_viewer, Item):
            parent_viewer_class = ViewerMetaClass.viewer_name_dict.get(parent_item_type_with_viewer.__name__.lower(), None)
            if parent_viewer_class:
                break
            parent_item_type_with_viewer = parent_item_type_with_viewer.__base__
        if parent_viewer_class:
            viewer_class_name = '%sViewer' % item_type.__name__
            ViewerMetaClass.__new__(ViewerMetaClass, viewer_class_name, (parent_viewer_class,), {'accepted_item_type': item_type, 'viewer_name': viewer_name})
        else:
            pass

