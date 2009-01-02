# Create your views here.
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
from django.db import models
from django.db.models import Q
import cms.models
from django import forms
from django.utils import simplejson
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging
import permission_functions
import re

### MODELS ###

resource_name_dict = {}
for model in cms.models.all_models():
    resource_name_dict[model.__name__.lower()] = model


class AjaxModelChoiceWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        model = self.choices.queryset.model
        #field = self.choices.field
        try:
            if issubclass(model, cms.models.Item):
                value_item = cms.models.Item.objects.get(pk=value)
            elif issubclass(model, cms.models.ItemVersion):
                value_item = cms.models.ItemVersion.objects.get(pk=value)
            else:
                value_item = None
        except:
            value_item = None
        initial_search = value_item.name if value_item else ''
        if value is None: value = ''
        if attrs is None: attrs = {}
        ajax_url = reverse('resource_collection', kwargs={'viewer': model.__name__.lower(), 'format': 'json'})
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

class NewMembershipForm(forms.ModelForm):
    item = AjaxModelChoiceField(cms.models.Item.objects)
    class Meta:
        model = cms.models.Membership
        fields = ['item']

class NewTextCommentForm(forms.ModelForm):
    commented_item = HiddenModelChoiceField(cms.models.Item.objects)
    commented_item_version_number = forms.IntegerField(widget=forms.HiddenInput())
    commented_item_index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = cms.models.TextComment
        fields = ['name', 'description', 'body', 'commented_item']

class NewTextDocumentExcerptForm(forms.ModelForm):
    text_document = HiddenModelChoiceField(cms.models.TextDocument.objects)
    text_document_version_number = forms.IntegerField(widget=forms.HiddenInput())
    start_index = forms.IntegerField(widget=forms.HiddenInput())
    length = forms.IntegerField(widget=forms.HiddenInput())
    class Meta:
        model = cms.models.TextDocumentExcerpt
        fields = ['name', 'description', 'text_document', 'text_document_version_number', 'start_index', 'length']

def get_form_class_for_item_type(update_or_create, item_type, fields=None):
    exclude = []
    for field in item_type._meta.fields:
        if (field.rel and field.rel.parent_link) or (update_or_create == 'update' and field.name in item_type.immutable_fields):
            exclude.append(field.name)
    def formfield_callback(f):
        if isinstance(f, models.ForeignKey):
            return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
        else:
            return f.formfield()
    return forms.models.modelform_factory(item_type, exclude=exclude, fields=fields, formfield_callback=formfield_callback)

### VIEWERS ###

class ViewerMetaClass(type):
    viewer_name_dict = {}
    def __new__(cls, name, bases, attrs):
        result = super(ViewerMetaClass, cls).__new__(cls, name, bases, attrs)
        ViewerMetaClass.viewer_name_dict[attrs['viewer_name']] = result
        return result

def set_default_layout(context, site, cur_agent):
    permission_cache = context['_permission_cache']
    cur_node = site.default_layout
    while cur_node is not None:
        next_node = cur_node.layout
        if next_node is None:
            if cur_node.override_default_layout:
                extends_string = ''
            else:
                extends_string = "{% extends 'default_layout.html' %}\n"
        else:
            extends_string = "{%% extends layout%s %%}\n" % next_node.pk
        if 'view layout' in permission_cache.get_abilities_for_agent_and_item(context['cur_agent'], cur_node) and 'view body' in permission_cache.get_abilities_for_agent_and_item(context['cur_agent'], cur_node):
            template_string = extends_string + cur_node.body
        else:
            template_string = "{% extends 'default_layout.html' %}\n"
            context['layout_permissions_problem'] = True
            next_node = None
        t = loader.get_template_from_string(template_string)
        context['layout%d' % cur_node.pk] = t
        cur_node = next_node
    if 'view default_layout' in permission_cache.get_abilities_for_agent_and_item(context['cur_agent'], site):
        if site.default_layout:
            context['layout'] = context['layout%s' % site.default_layout.pk]
        else:
            context['layout'] = 'default_layout.html'
    else:
        context['layout'] = 'default_layout.html'
        context['layout_permissions_problem'] = True

def get_viewer_class_for_viewer_name(viewer_name):
    return ViewerMetaClass.viewer_name_dict.get(viewer_name, None)

def get_versioned_item(item, version_number):
    if version_number is None:
        itemversion = type(item).VERSION.objects.filter(current_item=item).latest()
    else:
        itemversion = type(item).VERSION.objects.get(current_item=item, version_number=version_number)
        #TODO use copy_fields_from_itemversion here
        for name in itemversion._meta.get_all_field_names():
            if name in ['item_type', 'trashed', 'current_item', 'version_number']: # special fields
                continue
            field, model, direct, m2m = itemversion._meta.get_field_by_name(name)
            if hasattr(field, 'primary_key') and field.primary_key:
                continue
            elif type(field).__name__ == 'OneToOneField':
                continue
            elif type(field).__name__ == 'ManyToManyField':
                continue
            elif type(field).__name__ == 'RelatedObject':
                continue
            elif type(field).__name__ == 'ForeignKey':
                try:
                    obj = getattr(itemversion, name)
                except ObjectDoesNotExist:
                    obj = None
            else:
                obj = getattr(itemversion, name)
            setattr(item, name, obj)
    item.version_number = itemversion.version_number
    return item


class PermissionCache(object):

    def __init__(self):
        self._global_ability_cache = {}
        self._item_ability_cache = {}

    def get_global_abilities_for_agent(self, agent):
        result = self._global_ability_cache.get(agent.pk)
        if result is None:
            result = permission_functions.get_global_abilities_for_agent(agent)
            if 'do_everything' in result:
                result = [x[0] for x in cms.models.POSSIBLE_GLOBAL_ABILITIES]
            self._global_ability_cache[agent.pk] = result
        return result

    def get_abilities_for_agent_and_item(self, agent, item):
        result = self._item_ability_cache.get((agent.pk, item.pk))
        if result is None:
            if 'do_everything' in self.get_global_abilities_for_agent(agent):
                result = list(type(item).relevant_abilities)
            else:
                result = permission_functions.get_abilities_for_agent_and_item(agent, item)
            self._item_ability_cache[(agent.pk, item.pk)] = result
        return result


class ItemViewer(object):
    __metaclass__ = ViewerMetaClass

    item_type = cms.models.Item
    viewer_name = 'item'

    def __init__(self):
        pass

    def cur_agent_can_global(self, ability):
        return ability in self.permission_cache.get_global_abilities_for_agent(self.cur_agent)

    def cur_agent_can(self, ability, item):
        return ability in self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, item)

    def render_error(self, request_class, title, body):
        template = loader.get_template_from_string("""
        {%% extends layout %%}
        {%% load resource_extras %%}
        {%% block favicon %%}{{ "error"|icon_url:16 }}{%% endblock %%}
        {%% block title %%}<img src="{{ "error"|icon_url:48 }}" /> %s{%% endblock %%}
        {%% block content %%}%s{%% endblock content %%}
        """ % (title, body))
        return request_class(template.render(self.context))

    def init_from_http(self, request, cur_agent, current_site, url_info):
        self.permission_cache = PermissionCache()
        self.viewer_name = url_info.get('viewer')
        self.format = url_info.get('format', 'html')
        self.method = (request.REQUEST.get('_method', None) or request.method).upper()
        self.request = request # FOR NOW
        self.noun = url_info.get('noun')
        if self.noun == None:
            self.action = url_info.get('collection_action')
            if self.action == None:
                self.action = {'GET': 'list', 'POST': 'create', 'PUT': 'update', 'DELETE': 'delete'}.get(self.method, 'list')
            self.item = None
        else:
            self.action = url_info.get('entry_action')
            if self.action == None:
                self.action = {'GET': 'show', 'POST': 'create', 'PUT': 'update', 'DELETE': 'delete'}.get(self.method, 'show')
            try:
                self.item = cms.models.Item.objects.get(pk=self.noun)
                if self.item:
                    self.item = self.item.downcast()
                if 'version' in self.request.REQUEST:
                    version_number = self.request.REQUEST['version']
                    self.item = get_versioned_item(self.item, version_number)
                else:
                    self.item = get_versioned_item(self.item, None)
            except ObjectDoesNotExist:
                self.item = None
        self.context = Context()
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['item_type'] = self.item_type.__name__
        self.context['item_type_inheritance'] = [x.__name__ for x in reversed(self.item_type.mro()) if issubclass(x, cms.models.Item)]
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = cur_agent
        self.context['cur_agent'] = self.cur_agent
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        set_default_layout(self.context, current_site, cur_agent)

    def init_from_div(self, original_viewer, action, viewer_name, item, cur_agent):
        self.permission_cache = original_viewer.permission_cache
        self.request = original_viewer.request
        self.viewer_name = viewer_name
        self.format = 'html'
        self.method = 'GET'
        self.noun = item.pk
        self.item = item
        self.action = action
        self.context = Context()
        self.context['layout'] = 'blank.html'
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['item_type'] = self.item_type.__name__
        self.context['item_type_inheritance'] = [x.__name__ for x in reversed(self.item_type.mro()) if issubclass(x, cms.models.Item)]
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = cur_agent
        self.context['cur_agent'] = self.cur_agent
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self

    def dispatch(self):
        if not self.cur_agent_can_global('do_something'):
            template = loader.get_template_from_string("""
{% extends layout %}
{% load resource_extras %}
{% block title %}Not Allowed{% endblock %}
{% block content %}

The agent currently logged in is not allowed to use this application. Please log in as another agent.

{% endblock content %}
""")
            return HttpResponse(template.render(self.context))
        if self.noun == None:
            action_method = getattr(self, 'collection_%s' % self.action, None)
        else:
            action_method = getattr(self, 'entry_%s' % self.action, None)
        if action_method:
            if self.noun != None:
                if self.item is None:
                    return self.render_item_not_found()
                elif self.action == 'copy':
                    pass
                elif (self.action == 'edit' or self.action == 'update'):
                    if self.item_type != type(self.item):
                        return self.render_item_not_found()
                else:
                    if not isinstance(self.item, self.item_type):
                        return self.render_item_not_found()
            return action_method()
        else:
            return None

    def render_item_not_found(self):
        if self.item:
            title = "%s Not Found" % self.item_type.__name__
            body = 'You cannot view item %s in this viewer. Try viewing it in the <a href="{%% show_resource_url item %%}">{{ item.item_type }} viewer</a>.' % self.noun
        else:
            title = "Item Not Found"
            version = self.request.GET.get('version')
            if version is None:
                body = 'There is no item %s.' % self.noun
            else:
                body = 'There is no item %s version %s.' % (self.noun, version)
        return self.render_error(HttpResponseNotFound, title, body)

    def collection_list(self):
        if self.request.GET.get('itemset'):
            itemset = cms.models.Item.objects.get(pk=self.request.GET.get('itemset')).downcast()
        else:
            itemset = None
        offset = int(self.request.GET.get('offset', 0))
        limit = int(self.request.GET.get('limit', 100))
        trashed = self.request.GET.get('trashed', None) == '1'
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        self.context['search_query'] = self.request.GET.get('q', '')
        items = self.item_type.objects
        if self.context['search_query']:
            q = self.context['search_query']
            search_filter = Q(name__icontains=q)
            # This is commented out because it's too simplistic, and does not respect permissions.
            # search_filter = search_filter | Q(description__icontains=q)
            # if self.item_type == cms.models.Item:
            #     search_filter = search_filter | Q(document__textdocument__body__icontains=q)
            # elif self.item_type == cms.models.Document:
            #     search_filter = search_filter | Q(textdocument__body__icontains=q)
            # elif issubclass(self.item_type, cms.models.TextDocument):
            #     search_filter = search_filter | Q(body__icontains=q)
            items = items.filter(search_filter)
        if isinstance(itemset, cms.models.ItemSet):
            if self.cur_agent_can_global('do_everything'):
                recursive_filter = None
            else:
                visible_memberships = cms.models.Membership.objects.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view itemset'), permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view item'))
                recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
            items = items.filter(pk__in=itemset.all_contained_itemset_members(recursive_filter).values('pk').query)
        if self.cur_agent_can_global('do_everything'):
            listable_items = items
        else:
            listable_items = items.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view name'))
        n_opposite_trashed_items = listable_items.filter(trashed=(not trashed)).count()
        listable_items = listable_items.filter(trashed=trashed)
        listable_items = listable_items.order_by('id')
        n_items = items.count()
        n_listable_items = listable_items.count()
        items = [item for item in listable_items.all()[offset:offset+limit]]
        if self.format == 'json':
            json_data = simplejson.dumps([[item.name, item.pk] for item in items], separators=(',',':'))
            return HttpResponse(json_data, mimetype='application/json')
        template = loader.get_template('item/list.html')
        self.context['model_names'] = model_names
        self.context['items'] = items
        self.context['n_items'] = n_items
        self.context['n_listable_items'] = n_listable_items
        self.context['n_unlistable_items'] = n_items - n_listable_items - n_opposite_trashed_items
        self.context['n_opposite_trashed_items'] = n_opposite_trashed_items
        self.context['offset'] = offset
        self.context['limit'] = limit
        self.context['list_start_i'] = offset + 1
        self.context['list_end_i'] = min(offset + limit, n_listable_items)
        self.context['trashed'] = trashed
        self.context['itemset'] = itemset
        self.context['all_itemsets'] = cms.models.ItemSet.objects.filter(trashed=False).filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view name')).order_by('name')
        return HttpResponse(template.render(self.context))

    def collection_new(self):
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type) and self.cur_agent_can_global('create %s' % model.__name__)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save_versioned(updater=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type) and self.cur_agent_can_global('create %s' % model.__name__)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        def get_fields_for_item(item):
            fields = []
            for name in item._meta.get_all_field_names():
                if name in ['item_type', 'trashed', 'current_item', 'version_number']: # special fields
                    continue
                field, model, direct, m2m = item._meta.get_field_by_name(name)
                model_class = type(item) if model == None else model
                model_class = model_class.NOTVERSION if issubclass(model_class, cms.models.Item.VERSION) else model_class
                model_name = model_class.__name__
                if model_name == 'Item':
                    continue # things in Item are boring, since they're already part of the layout (itemheader)
                info = {'model_name': model_name, 'name': name, 'format': type(field).__name__}
                if type(field).__name__ == 'ForeignKey':
                    try:
                        obj = getattr(item, name)
                    except ObjectDoesNotExist:
                        obj = None
                    info['field_type'] = 'entry'
                elif type(field).__name__ == 'OneToOneField':
                    continue
                elif type(field).__name__ == 'ManyToManyField':
                    continue
                elif type(field).__name__ == 'RelatedObject':
                    continue
                else:
                    obj = getattr(item, name)
                    info['field_type'] = 'regular'
                info['obj'] = obj
                info['can_view'] = self.cur_agent_can('view %s' % name, self.item)
                if info['field_type'] == 'entry' and obj is not None:
                    info['can_view_name'] = self.cur_agent_can('view name', obj)
                fields.append(info)
            return fields
        template = loader.get_template('item/show.html')
        item_fields = get_fields_for_item(self.item)
        self.context['fields'] = item_fields
        return HttpResponse(template.render(self.context))

    def entry_relationships(self):
        relationship_sets = []
        for name in sorted(self.item._meta.get_all_field_names()):
            field, model, direct, m2m = self.item._meta.get_field_by_name(name)
            if type(field).__name__ != 'RelatedObject':
                continue
            if type(field.field).__name__ != 'ForeignKey':
                continue
            if issubclass(field.model, cms.models.Permission):
                continue
            if not issubclass(field.model, cms.models.Item):
                continue
            manager = getattr(self.item, name)
            relationship_set = {}
            relationship_set['name'] = name
            viewable_items = manager.filter(trashed=False)
            if viewable_items.count() == 0:
                continue
            if self.cur_agent_can_global('do_everything'):
                relationship_set['items'] = [{'item': item, 'can_view_name': True} for item in viewable_items]
            else:
                viewable_items = viewable_items.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view %s' % field.field.name))
                ids_can_view_name = set(viewable_items.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view name')).values_list('pk', flat=True))
                relationship_set['items'] = [{'item': item, 'can_view_name': item.pk in ids_can_view_name} for item in viewable_items]
            relationship_sets.append(relationship_set)
        template = loader.get_template('item/relationships.html')
        self.context['relationship_sets'] = relationship_sets
        self.context['abilities'] = sorted(self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item))
        return HttpResponse(template.render(self.context))

    def entry_edit(self):
        abilities_for_item = self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if isinstance(self.item, cms.models.Permission) and hasattr(self.item, 'item') and 'modify_permissions' in self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item.item):
            can_edit = True
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)
        form = form_class(instance=self.item)
        fields_can_view = set([x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'view'])
        initial_fields_set = set(form.initial.iterkeys())
        fields_must_blank = initial_fields_set - fields_can_view
        for field_name in fields_must_blank:
            del form.initial[field_name]
        template = loader.get_template('item/edit.html')
        self.context['form'] = form
        self.context['query_string'] = self.request.META['QUERY_STRING']
        return HttpResponse(template.render(self.context))

    def entry_copy(self):
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.item_type)
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
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type) and self.cur_agent_can_global('create %s' % model.__name__)]
        model_names.sort()
        self.context['model_names'] = model_names
        self.context['action_is_entry_copy'] = True
        if 'redirect' in self.request.GET:
            self.context['redirect'] = self.request.GET['redirect']
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        abilities_for_item = self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if isinstance(self.item, cms.models.Permission) and hasattr(self.item, 'item') and 'modify_permissions' in self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item.item):
            can_edit = True
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        new_item = self.item
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(updater=self.cur_agent)
            return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/edit.html')
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            return HttpResponse(template.render(self.context))

    def entry_trash(self):
        can_trash = self.cur_agent_can('trash', self.item)
        if isinstance(self.item, cms.models.Permission) and hasattr(self.item, 'item') and self.cur_agent_can('modify_permissions', self.item.item):
            can_trash = True
        if not can_trash:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to trash this item")
        self.item.trash(self.cur_agent)
        return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))

    def entry_untrash(self):
        can_trash = self.cur_agent_can('trash', self.item)
        if isinstance(self.item, cms.models.Permission) and hasattr(self.item, 'item') and self.cur_agent_can('modify_permissions', self.item.item):
            can_trash = True
        if not can_trash:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to untrash this item")
        self.item.untrash(self.cur_agent)
        return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))

    def entry_permissions(self):
        can_modify_permissions = self.cur_agent_can('modify_permissions', self.item)
        if not can_modify_permissions:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify permissions of this item")

        def formfield_callback(f):
            if f.name in ['agent', 'itemset', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(cms.models.AgentPermission, fields=['agent', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        agent_role_permission_form_class = forms.models.modelform_factory(cms.models.AgentRolePermission, fields=['agent', 'item', 'role'], formfield_callback=formfield_callback)
        itemset_permission_form_class = forms.models.modelform_factory(cms.models.ItemSetPermission, fields=['itemset', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        itemset_role_permission_form_class = forms.models.modelform_factory(cms.models.ItemSetRolePermission, fields=['itemset', 'item', 'role'], formfield_callback=formfield_callback)
        default_permission_form_class = forms.models.modelform_factory(cms.models.DefaultPermission, fields=['item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        default_role_permission_form_class = forms.models.modelform_factory(cms.models.DefaultRolePermission, fields=['item', 'role'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'agentrolepermission':
                form_class = agent_role_permission_form_class
            elif form_type == 'itemsetpermission':
                form_class = itemset_permission_form_class
            elif form_type == 'itemsetrolepermission':
                form_class = itemset_role_permission_form_class
            elif form_type == 'defaultpermission':
                form_class = default_permission_form_class
            elif form_type == 'defaultrolepermission':
                form_class = default_role_permission_form_class
            else:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Type', "You submitted a permission form with an invalid formtype parameter")

            form = form_class(self.request.POST, self.request.FILES, prefix=self.request.GET['formprefix'])
            if form.is_valid():
                item = form.save(commit=False)
                item.name = "Untitled Permission"
                item.save_versioned(updater=self.cur_agent)
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
                    elif field == 'itemset':
                        existing_permission = existing_permission.filter(itemset__pk=data)
                    elif field == 'item':
                        existing_permission = existing_permission.filter(item__pk=data)
                    elif field == 'role':
                        existing_permission = existing_permission.filter(role__pk=data)
                    elif field == 'ability':
                        existing_permission = existing_permission.filter(ability=data)
                try:
                    existing_permission = existing_permission.get()
                except ObjectDoesNotExist:
                    existing_permission = None
                if existing_permission:
                    something_changed = False
                    if existing_permission.trashed:
                        existing_permission.untrash(self.cur_agent)
                        something_changed = True
                    if 'is_allowed' in fields and existing_permission.is_allowed != form['is_allowed'].data:
                        existing_permission.is_allowed = form['is_allowed'].data
                        existing_permission.save_versioned(updater=self.cur_agent)
                        something_changed = True
                    # Regardless of whether something_changed, it was a success
                    redirect = self.request.GET['redirect']
                    return HttpResponseRedirect(redirect)
                else:
                    # we'll display it in the regular page below as an invalid form
                    pass

        agent_permissions = self.item.agent_permissions_as_item.filter(trashed=False)
        itemset_permissions = self.item.itemset_permissions_as_item.filter(trashed=False)
        default_permissions = self.item.default_permissions_as_item.filter(trashed=False)
        agent_role_permissions = self.item.agent_role_permissions_as_item.filter(trashed=False)
        itemset_role_permissions = self.item.itemset_role_permissions_as_item.filter(trashed=False)
        default_role_permissions = self.item.default_role_permissions_as_item.filter(trashed=False)
        agents = cms.models.Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk__in=agent_role_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        itemsets = cms.models.ItemSet.objects.filter(Q(pk__in=itemset_permissions.values('itemset__pk').query) | Q(pk__in=itemset_role_permissions.values('itemset__pk').query) | Q(pk=self.request.GET.get('itemset', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['role_permissions'] = agent_role_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'item': self.item.pk, 'agent': agent.pk})
            agent_datum['role_permission_form'] = agent_role_permission_form_class(prefix="roleagent%s" % agent.pk, initial={'item': self.item.pk, 'agent': agent.pk})
            agent_data.append(agent_datum)
        itemset_data = []
        for itemset in itemsets:
            itemset_datum = {}
            itemset_datum['itemset'] = itemset
            itemset_datum['permissions'] = itemset_permissions.filter(itemset=itemset)
            itemset_datum['role_permissions'] = itemset_role_permissions.filter(itemset=itemset)
            itemset_datum['permission_form'] = itemset_permission_form_class(prefix="itemset%s" % itemset.pk, initial={'item': self.item.pk, 'itemset': itemset.pk})
            itemset_datum['role_permission_form'] = itemset_role_permission_form_class(prefix="roleitemset%s" % itemset.pk, initial={'item': self.item.pk, 'itemset': itemset.pk})
            itemset_data.append(itemset_datum)
        default_data = {}
        default_data['permissions'] = default_permissions
        default_data['role_permissions'] = default_role_permissions
        default_data['permission_form'] = default_permission_form_class(prefix="default", initial={'item': self.item.pk})
        default_data['role_permission_form'] = default_role_permission_form_class(prefix="roledefault", initial={'item': self.item.pk})

        # now include the error form
        if self.method == 'POST':
            if form_type == 'agentpermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['permission_form'] = form
                agent_datum['permission_form_invalid'] = True
            elif form_type == 'agentrolepermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['role_permission_form'] = form
                agent_datum['role_permission_form_invalid'] = True
            elif form_type == 'itemsetpermission':
                itemset_datum = [datum for datum in itemset_data if str(datum['itemset'].pk) == form['itemset'].data][0]
                itemset_datum['permission_form'] = form
                itemset_datum['permission_form_invalid'] = True
            elif form_type == 'itemsetrolepermission':
                itemset_datum = [datum for datum in itemset_data if str(datum['itemset'].pk) == form['itemset'].data][0]
                itemset_datum['role_permission_form'] = form
                itemset_datum['role_permission_form_invalid'] = True
            elif form_type == 'defaultpermission':
                default_data['permission_form'] = form
                default_data['permission_form_invalid'] = True
            elif form_type == 'defaultrolepermission':
                default_data['role_permission_form'] = form
                default_data['role_permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(cms.models.AgentPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_itemset_form_class = forms.models.modelform_factory(cms.models.ItemSetPermission, fields=['itemset'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/permissions.html')
        self.context['agent_data'] = agent_data
        self.context['itemset_data'] = itemset_data
        self.context['default_data'] = default_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_itemset_form'] = new_itemset_form_class()
        return HttpResponse(template.render(self.context))

    def collection_globalpermissions(self):
        if not self.cur_agent_can_global('do_everything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify global permissions")

        def formfield_callback(f):
            if f.name in ['agent', 'itemset', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(cms.models.AgentGlobalPermission, fields=['agent', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        agent_role_permission_form_class = forms.models.modelform_factory(cms.models.AgentGlobalRolePermission, fields=['agent', 'global_role'], formfield_callback=formfield_callback)
        itemset_permission_form_class = forms.models.modelform_factory(cms.models.ItemSetGlobalPermission, fields=['itemset', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        itemset_role_permission_form_class = forms.models.modelform_factory(cms.models.ItemSetGlobalRolePermission, fields=['itemset', 'global_role'], formfield_callback=formfield_callback)
        default_permission_form_class = forms.models.modelform_factory(cms.models.DefaultGlobalPermission, fields=['ability', 'is_allowed'], formfield_callback=formfield_callback)
        default_role_permission_form_class = forms.models.modelform_factory(cms.models.DefaultGlobalRolePermission, fields=['global_role'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'agentrolepermission':
                form_class = agent_role_permission_form_class
            elif form_type == 'itemsetpermission':
                form_class = itemset_permission_form_class
            elif form_type == 'itemsetrolepermission':
                form_class = itemset_role_permission_form_class
            elif form_type == 'defaultpermission':
                form_class = default_permission_form_class
            elif form_type == 'defaultrolepermission':
                form_class = default_role_permission_form_class
            else:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Type', "You submitted a permission form with an invalid formtype parameter")

            form = form_class(self.request.POST, self.request.FILES, prefix=self.request.GET['formprefix'])
            if form.is_valid():
                item = form.save(commit=False)
                item.name = "Untitled Permission"
                item.save_versioned(updater=self.cur_agent)
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
                    elif field == 'itemset':
                        existing_permission = existing_permission.filter(itemset__pk=data)
                    elif field == 'global_role':
                        existing_permission = existing_permission.filter(global_role__pk=data)
                    elif field == 'ability':
                        existing_permission = existing_permission.filter(ability=data)
                try:
                    existing_permission = existing_permission.get()
                except ObjectDoesNotExist:
                    existing_permission = None
                if existing_permission:
                    something_changed = False
                    if existing_permission.trashed:
                        existing_permission.untrash(self.cur_agent)
                        something_changed = True
                    if 'is_allowed' in fields and existing_permission.is_allowed != form['is_allowed'].data:
                        existing_permission.is_allowed = form['is_allowed'].data
                        existing_permission.save_versioned(updater=self.cur_agent)
                        something_changed = True
                    # Regardless of whether something_changed, it was a success
                    redirect = self.request.GET['redirect']
                    return HttpResponseRedirect(redirect)
                else:
                    # we'll display it in the regular page below as an invalid form
                    pass

        agent_permissions = cms.models.AgentGlobalPermission.objects.filter(trashed=False)
        itemset_permissions = cms.models.ItemSetGlobalPermission.objects.filter(trashed=False)
        default_permissions = cms.models.DefaultGlobalPermission.objects.filter(trashed=False)
        agent_role_permissions = cms.models.AgentGlobalRolePermission.objects.filter(trashed=False)
        itemset_role_permissions = cms.models.ItemSetGlobalRolePermission.objects.filter(trashed=False)
        default_role_permissions = cms.models.DefaultGlobalRolePermission.objects.filter(trashed=False)
        agents = cms.models.Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk__in=agent_role_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        itemsets = cms.models.ItemSet.objects.filter(Q(pk__in=itemset_permissions.values('itemset__pk').query) | Q(pk__in=itemset_role_permissions.values('itemset__pk').query) | Q(pk=self.request.GET.get('itemset', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['role_permissions'] = agent_role_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'agent': agent.pk})
            agent_datum['role_permission_form'] = agent_role_permission_form_class(prefix="roleagent%s" % agent.pk, initial={'agent': agent.pk})
            agent_data.append(agent_datum)
        itemset_data = []
        for itemset in itemsets:
            itemset_datum = {}
            itemset_datum['itemset'] = itemset
            itemset_datum['permissions'] = itemset_permissions.filter(itemset=itemset)
            itemset_datum['role_permissions'] = itemset_role_permissions.filter(itemset=itemset)
            itemset_datum['permission_form'] = itemset_permission_form_class(prefix="itemset%s" % itemset.pk, initial={'itemset': itemset.pk})
            itemset_datum['role_permission_form'] = itemset_role_permission_form_class(prefix="roleitemset%s" % itemset.pk, initial={'itemset': itemset.pk})
            itemset_data.append(itemset_datum)
        default_data = {}
        default_data['permissions'] = default_permissions
        default_data['role_permissions'] = default_role_permissions
        default_data['permission_form'] = default_permission_form_class(prefix="default", initial={})
        default_data['role_permission_form'] = default_role_permission_form_class(prefix="roledefault", initial={})

        # now include the error form
        if self.method == 'POST':
            if form_type == 'agentpermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['permission_form'] = form
                agent_datum['permission_form_invalid'] = True
            elif form_type == 'agentrolepermission':
                agent_datum = [datum for datum in agent_data if str(datum['agent'].pk) == form['agent'].data][0]
                agent_datum['role_permission_form'] = form
                agent_datum['role_permission_form_invalid'] = True
            elif form_type == 'itemsetpermission':
                itemset_datum = [datum for datum in itemset_data if str(datum['itemset'].pk) == form['itemset'].data][0]
                itemset_datum['permission_form'] = form
                itemset_datum['permission_form_invalid'] = True
            elif form_type == 'itemsetrolepermission':
                itemset_datum = [datum for datum in itemset_data if str(datum['itemset'].pk) == form['itemset'].data][0]
                itemset_datum['role_permission_form'] = form
                itemset_datum['role_permission_form_invalid'] = True
            elif form_type == 'defaultpermission':
                default_data['permission_form'] = form
                default_data['permission_form_invalid'] = True
            elif form_type == 'defaultrolepermission':
                default_data['role_permission_form'] = form
                default_data['role_permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(cms.models.AgentGlobalPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_itemset_form_class = forms.models.modelform_factory(cms.models.ItemSetGlobalPermission, fields=['itemset'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/globalpermissions.html')
        self.context['agent_data'] = agent_data
        self.context['itemset_data'] = itemset_data
        self.context['default_data'] = default_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_itemset_form'] = new_itemset_form_class()
        return HttpResponse(template.render(self.context))


class GroupViewer(ItemViewer):
    item_type = cms.models.Group
    viewer_name = 'group'

    def collection_create(self):
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        form_class = get_form_class_for_item_type('create', self.item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(updater=self.cur_agent)
            return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        #TODO permission to know folio is associated with group?
        folio = get_versioned_item(self.item.folios_as_group.get(), None)
        folio_viewer_class = get_viewer_class_for_viewer_name('itemset')
        folio_viewer = folio_viewer_class()
        folio_viewer.init_from_div(self, 'show', 'itemset', folio, self.cur_agent)
        folio_html = folio_viewer.dispatch().content
        self.context['folio_html'] = folio_html
        template = loader.get_template('group/show.html')
        return HttpResponse(template.render(self.context))


class ItemSetViewer(ItemViewer):
    item_type = cms.models.ItemSet
    viewer_name = 'itemset'

    def entry_show(self):
        memberships = self.item.memberships_as_itemset
        memberships = memberships.filter(trashed=False)
        memberships = memberships.filter(item__trashed=False)
        memberships = memberships.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view item'))
        memberships = memberships.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view itemset'))
        memberships = memberships.select_related('item')
        memberships_can_view_name_pks = set(memberships.filter(item__pk__in=cms.models.Item.objects.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view name')).values('pk').query).values_list('pk', flat=True))
        self.context['memberships'] = [{'membership': x, 'can_view_name': x.pk in memberships_can_view_name_pks} for x in memberships]
        self.context['cur_agent_in_itemset'] = bool(self.item.memberships_as_itemset.filter(trashed=False, item=self.cur_agent))
        self.context['addmember_form'] = NewMembershipForm()
        template = loader.get_template('itemset/show.html')
        return HttpResponse(template.render(self.context))


    def entry_addmember(self):
        try:
            member = cms.models.Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('add_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add this member to this ItemSet")
        try:
            membership = cms.models.Membership.objects.get(itemset=self.item, item=member)
            if membership.trashed:
                membership.untrash(self.cur_agent)
        except:
            membership = cms.models.Membership(itemset=self.item, item=member)
            membership.save_versioned(updater=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


    def entry_removemember(self):
        try:
            member = cms.models.Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('remove_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to remove this member from this ItemSet")
        try:
            membership = cms.models.Membership.objects.get(itemset=self.item, item=member)
            if not membership.trashed:
                membership.trash(self.cur_agent)
        except:
            pass
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


class ImageDocument(ItemViewer):
    item_type = cms.models.ImageDocument
    viewer_name = 'imagedocument'

    def entry_show(self):
        template = loader.get_template('imagedocument/show.html')
        return HttpResponse(template.render(self.context))


class TextDocumentViewer(ItemViewer):
    item_type = cms.models.TextDocument
    viewer_name = 'textdocument'

    def entry_show(self):
        template = loader.get_template('textdocument/show.html')
        self.context['is_html'] = issubclass(self.item_type, cms.models.HtmlDocument)
        return HttpResponse(template.render(self.context))


    def entry_edit(self):
        abilities_for_item = self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)


        comment_locations = cms.models.CommentLocation.objects.filter(comment__commented_item=self.item.pk, commented_item_version_number=self.item.version_number, commented_item_index__isnull=False).order_by('-commented_item_index')
        body_as_list = list(self.item.body)
        for comment_location in comment_locations:
            if issubclass(self.item_type, cms.models.HtmlDocument):
                virtual_comment = '<img id="comment_location_%s" src="/static/spacer.gif" title="Comment %s" style="margin: 0 2px 0 2px; background: #ddd; border: 1px dotted #777; height: 10px; width: 10px;"/>' % (comment_location.comment.pk, comment_location.comment.pk)
            else:
                virtual_comment = '<deme_comment_location id="%s"/>' % comment_location.comment.pk
            i = comment_location.commented_item_index
            body_as_list[i:i] = virtual_comment
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
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        abilities_for_item = self.permission_cache.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        new_item = self.item
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)

            new_comment_locations = []
            while True:
                def repl(m):
                    index = m.start()
                    comment_id = m.group(1)
                    new_comment_locations.append((index, comment_id))
                    return ''
                if issubclass(self.item_type, cms.models.HtmlDocument):
                    virtual_comment_re = r'(?i)<img[^>]+comment_location_(\d+)[^>]*>'
                else:
                    virtual_comment_re = r'<deme_comment_location id="(\d+)"/>'
                new_item.body, n_subs = re.subn(virtual_comment_re, repl, new_item.body, 1)
                if n_subs == 0:
                    break
            
            new_item.save_versioned(updater=self.cur_agent)

            new_item_version_number = new_item.versions.latest().version_number
            for index, comment_id in new_comment_locations:
                comment_location = cms.models.CommentLocation()
                comment_location.comment = cms.models.Comment.objects.get(pk=comment_id)
                comment_location.commented_item_index = index
                comment_location.commented_item_version_number = new_item_version_number
                comment_location.save_versioned(updater=self.cur_agent)

            return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/edit.html')
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, type(self.item))]
            model_names.sort()
            self.context['model_names'] = model_names
            return HttpResponse(template.render(self.context))


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    item_type = cms.models.DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def entry_render(self):
        cur_node = self.item
        while cur_node is not None:
            next_node = cur_node.layout
            if cur_node.override_default_layout:
                template_string = cur_node.body
            else:
                if self.cur_agent_can('view layout', cur_node) and self.cur_agent_can('view body', cur_node):
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
    __metaclass__ = ViewerMetaClass

    item_type = cms.models.TextComment
    viewer_name = 'textcomment'

    def collection_new(self):
        try:
            commented_item = cms.models.Item.objects.get(pk=self.request.GET.get('commented_item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are commenting on")
        can_comment_on = self.cur_agent_can('comment_on', commented_item)
        if not can_comment_on:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to comment on this item")
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        form_class = NewTextCommentForm
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        try:
            commented_item = cms.models.Item.objects.get(pk=self.request.POST.get('commented_item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are commenting on")
        can_comment_on = self.cur_agent_can('comment_on', commented_item)
        if not can_comment_on:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to comment on this item")
        form_class = NewTextCommentForm
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the CommentLocation save at the same time as the Comment
            commented_item_version_number = form.cleaned_data['commented_item_version_number']
            commented_item_index = form.cleaned_data['commented_item_index']
            item = form.save(commit=False)
            item.save_versioned(updater=self.cur_agent)
            comment_location = cms.models.CommentLocation(comment=item, commented_item_version_number=commented_item_version_number, commented_item_index=commented_item_index)
            comment_location.save_versioned(updater=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update comments


class TextDocumentExcerptViewer(TextDocumentViewer):
    __metaclass__ = ViewerMetaClass

    item_type = cms.models.TextDocumentExcerpt
    viewer_name = 'textdocumentexcerpt'

    def collection_new(self):
        try:
            text_document = cms.models.TextDocument.objects.get(pk=self.request.GET.get('text_document'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are excerpting from")
        if not self.cur_agent_can('view body', text_document):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to view the body of this item")
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        form_class = NewTextDocumentExcerptForm
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        try:
            text_document = cms.models.TextDocument.objects.get(pk=self.request.GET.get('text_document'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are excerpting from")
        if not self.cur_agent_can('view body', text_document):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to view the body of this item")
        can_create = self.cur_agent_can_global('create %s' % self.item_type.__name__)
        if not can_create:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
        form_class = NewTextDocumentExcerptForm
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            start_index = form.cleaned_data['start_index']
            length = form.cleaned_data['length']
            text_document = get_versioned_item(form.cleaned_data['text_document'], form.cleaned_data['text_document_version_number'])
            body = text_document.body[start_index:start_index+length]
            item = form.save(commit=False)
            item.body = body
            item.save_versioned(updater=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update excerpts


# let's dynamically create default viewers for the ones we don't have
for item_type in cms.models.all_models():
    viewer_name = item_type.__name__.lower()
    if viewer_name not in ViewerMetaClass.viewer_name_dict:
        parent_item_type_with_viewer = item_type
        while issubclass(parent_item_type_with_viewer, cms.models.Item):
            parent_viewer_class = ViewerMetaClass.viewer_name_dict.get(parent_item_type_with_viewer.__name__.lower(), None)
            if parent_viewer_class:
                break
            parent_item_type_with_viewer = parent_item_type_with_viewer.__base__
        if parent_viewer_class:
            viewer_class_name = '%sViewer' % item_type.__name__
            import new
            viewer_class_def = new.classobj(viewer_class_name, (parent_viewer_class,), {'item_type': item_type, 'viewer_name': viewer_name})
            exec('global %s;%s = viewer_class_def'%(viewer_class_name, viewer_class_name))
        else:
            pass

