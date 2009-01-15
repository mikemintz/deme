from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
from django.db import models
from django.db.models import Q
from cms.models import *
from django import forms
from django.utils import simplejson
from django.core.exceptions import ObjectDoesNotExist
import permissions
import re

###############################################################################
# Models, forms, and fields
###############################################################################

resource_name_dict = {}
for model in all_models():
    resource_name_dict[model.__name__.lower()] = model


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
    commented_item = HiddenModelChoiceField(Item.objects)
    commented_item_version_number = forms.IntegerField(widget=forms.HiddenInput())
    commented_item_index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = TextComment
        fields = ['name', 'description', 'body', 'commented_item', 'commented_item_version_number']

def get_form_class_for_item_type(update_or_create, item_type, fields=None):
    # For now, this is how we prevent manual creation of TextDocumentExcerpts
    if issubclass(item_type, TextDocumentExcerpt):
        return forms.models.modelform_factory(item_type, fields=['name'])

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


###############################################################################
# Viewer helper functions
###############################################################################

class ViewerMetaClass(type):
    viewer_name_dict = {}
    def __new__(cls, name, bases, attrs):
        result = super(ViewerMetaClass, cls).__new__(cls, name, bases, attrs)
        ViewerMetaClass.viewer_name_dict[attrs['viewer_name']] = result
        return result

def set_default_layout(context):
    cur_agent = context['cur_agent']
    cur_site = context['cur_site']
    permission_cache = context['_permission_cache']
    cur_node = cur_site.default_layout
    while cur_node is not None:
        next_node = cur_node.layout
        if next_node is None:
            if cur_node.override_default_layout:
                extends_string = ''
            else:
                extends_string = "{% extends 'default_layout.html' %}\n"
        else:
            extends_string = "{%% extends layout%s %%}\n" % next_node.pk
        if permission_cache.agent_can(context['cur_agent'], 'view body', cur_node):
            template_string = extends_string + cur_node.body
        else:
            template_string = "{% extends 'default_layout.html' %}\n"
            context['layout_permissions_problem'] = True
            next_node = None
        t = loader.get_template_from_string(template_string)
        context['layout%d' % cur_node.pk] = t
        cur_node = next_node
    if cur_site.default_layout:
        context['layout'] = context['layout%s' % cur_site.default_layout.pk]
    else:
        context['layout'] = 'default_layout.html'

def error_response(cur_agent, cur_site, full_path, request_class, title, body):
    """
    Return an HttpResponse (of type request_class) that displays a simple
    error page with the specified title and body.
    
    You must supply cur_agent, cur_site, and full_path so that the error page
    can be rendered within the expected layout.
    """
    template = loader.get_template_from_string("""
    {%% extends layout %%}
    {%% load resource_extras %%}
    {%% block favicon %%}{{ "error"|icon_url:16 }}{%% endblock %%}
    {%% block title %%}<img src="{{ "error"|icon_url:48 }}" /> %s{%% endblock %%}
    {%% block content %%}%s{%% endblock content %%}
    """ % (title, body))
    context = Context()
    context['cur_agent'] = cur_agent
    context['cur_site'] = cur_site
    context['full_path'] = full_path
    context['_permission_cache'] = permissions.PermissionCache()
    set_default_layout(context)
    return request_class(template.render(context))

def get_viewer_class_for_viewer_name(viewer_name):
    return ViewerMetaClass.viewer_name_dict.get(viewer_name, None)

def get_versioned_item(item, version_number):
    if version_number is not None:
        item.copy_fields_from_version(version_number)
    return item


###############################################################################
# Viewers
###############################################################################

class ItemViewer(object):
    __metaclass__ = ViewerMetaClass

    item_type = Item
    viewer_name = 'item'

    def __init__(self):
        pass

    def cur_agent_can_global(self, ability):
        return self.permission_cache.agent_can_global(self.cur_agent, ability)

    def cur_agent_can(self, ability, item):
        return self.permission_cache.agent_can(self.cur_agent, ability, item)

    def render_error(self, request_class, title, body):
        return error_response(self.cur_agent, self.cur_site, self.context['full_path'], request_class, title, body)

    def init_from_http(self, request, cur_agent, cur_site, action, noun, format):
        self.permission_cache = permissions.PermissionCache()
        self.action = action
        self.noun = noun
        self.format = format or 'html'
        self.method = (request.REQUEST.get('_method', None) or request.method).upper()
        self.request = request # FOR NOW
        if self.noun == None:
            if self.action == None:
                self.action = {'GET': 'list', 'POST': 'create', 'PUT': 'update', 'DELETE': 'trash'}.get(self.method, 'list')
            self.item = None
        else:
            if self.action == None:
                self.action = {'GET': 'show', 'POST': 'create', 'PUT': 'update', 'DELETE': 'trash'}.get(self.method, 'show')
            try:
                self.item = Item.objects.get(pk=self.noun)
                if self.item:
                    self.item = self.item.downcast()
                self.item = get_versioned_item(self.item, self.request.GET.get('version'))
            except ObjectDoesNotExist:
                self.item = None
        self.context = Context()
        self.context['action'] = self.action
        self.context['item'] = self.item
        self.context['item_type'] = self.item_type.__name__
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = cur_agent
        self.cur_site = cur_site
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        set_default_layout(self.context)

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
        self.context['item_type'] = self.item_type.__name__
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = original_viewer.cur_agent
        self.cur_site = original_viewer.cur_site
        self.context['cur_agent'] = self.cur_agent
        self.context['cur_site'] = self.cur_site
        self.context['_permission_cache'] = self.permission_cache
        self.context['_viewer'] = self
        self.context['layout'] = 'blank.html'

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
                else:
                    if not isinstance(self.item, self.item_type):
                        return self.render_item_not_found()
            return action_method()
        else:
            return None

    def render_item_not_found(self):
        if self.item:
            title = "%s Not Found" % self.item_type.__name__
            body = 'You cannot view item %s in this viewer. Try viewing it in the <a href="%s">%s viewer</a>.' % (self.noun, reverse('resource_entry', kwargs={'viewer': self.item.item_type.lower(), 'noun': self.item.pk}), self.item.item_type)
        else:
            title = "Item Not Found"
            version = self.request.GET.get('version')
            if version is None:
                body = 'There is no item %s.' % self.noun
            else:
                body = 'There is no item %s version %s.' % (self.noun, version)
        return self.render_error(HttpResponseNotFound, title, body)

    def collection_list(self):
        if self.request.GET.get('collection'):
            collection = Item.objects.get(pk=self.request.GET.get('collection')).downcast()
        else:
            collection = None
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
            # if self.item_type == Item:
            #     search_filter = search_filter | Q(document__textdocument__body__icontains=q)
            # elif self.item_type == Document:
            #     search_filter = search_filter | Q(textdocument__body__icontains=q)
            # elif issubclass(self.item_type, TextDocument):
            #     search_filter = search_filter | Q(body__icontains=q)
            items = items.filter(search_filter)
        if isinstance(collection, Collection):
            if self.cur_agent_can_global('do_everything'):
                recursive_filter = None
            else:
                visible_memberships = Membership.objects.filter(permissions.filter_items_by_permission(self.cur_agent, 'view item'))
                recursive_filter = Q(child_memberships__pk__in=visible_memberships.values('pk').query)
            items = items.filter(pk__in=collection.all_contained_collection_members(recursive_filter).values('pk').query)
        if self.cur_agent_can_global('do_everything'):
            listable_items = items
        else:
            listable_items = items.filter(permissions.filter_items_by_permission(self.cur_agent, 'view name'))
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
        self.context['collection'] = collection
        self.context['all_collections'] = Collection.objects.filter(trashed=False).filter(permissions.filter_items_by_permission(self.cur_agent, 'view name')).order_by('name')
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
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
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
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
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
                model_class = model_class.NotVersion if issubclass(model_class, Item.Version) else model_class
                model_name = model_class.__name__
                if model_name == 'Item':
                    continue # things in Item are boring, since they're already part of the layout (entryheader)
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
            if issubclass(field.model, Permission):
                continue
            if not issubclass(field.model, Item):
                continue
            manager = getattr(self.item, name)
            relationship_set = {}
            relationship_set['name'] = name
            viewable_items = manager.filter(trashed=False)
            if viewable_items.count() == 0:
                continue
            self.permission_cache.mass_learn(self.cur_agent, 'view name', viewable_items)
            if not self.cur_agent_can_global('do_everything'):
                viewable_items = viewable_items.filter(permissions.filter_items_by_permission(self.cur_agent, 'view %s' % field.field.name))
            relationship_set['items'] = viewable_items
            relationship_sets.append(relationship_set)
        template = loader.get_template('item/relationships.html')
        self.context['relationship_sets'] = relationship_sets
        self.context['abilities'] = sorted(self.permission_cache.item_abilities(self.cur_agent, self.item))
        return HttpResponse(template.render(self.context))

    def entry_edit(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
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
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
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
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
        if 'redirect' in self.request.GET:
            self.context['redirect'] = self.request.GET['redirect']
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
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
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))

    def entry_trash(self):
        if self.method == 'GET':
            return self.render_error(HttpResponseBadRequest, 'Invalid Method', "You cannot visit this URL using the GET method")
        can_trash = self.cur_agent_can('trash', self.item)
        if isinstance(self.item, Permission) and self.cur_agent_can('modify_permissions', self.item.item):
            can_trash = True
        if isinstance(self.item, GlobalPermission) and self.cur_agent_can_global('do_everything'):
            can_trash = True
        if not can_trash:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to trash this item")
        self.item.trash(self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def entry_untrash(self):
        if self.method == 'GET':
            return self.render_error(HttpResponseBadRequest, 'Invalid Method', "You cannot visit this URL using the GET method")
        can_trash = self.cur_agent_can('trash', self.item)
        if isinstance(self.item, Permission) and self.cur_agent_can('modify_permissions', self.item.item):
            can_trash = True
        if isinstance(self.item, GlobalPermission) and self.cur_agent_can_global('do_everything'):
            can_trash = True
        if not can_trash:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to untrash this item")
        self.item.untrash(self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def entry_permissions(self):
        can_modify_permissions = self.cur_agent_can('modify_permissions', self.item)
        if not can_modify_permissions:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify permissions of this item")

        def formfield_callback(f):
            if f.name in ['agent', 'collection', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(AgentPermission, fields=['agent', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        agent_role_permission_form_class = forms.models.modelform_factory(AgentRolePermission, fields=['agent', 'item', 'role'], formfield_callback=formfield_callback)
        collection_permission_form_class = forms.models.modelform_factory(CollectionPermission, fields=['collection', 'item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        collection_role_permission_form_class = forms.models.modelform_factory(CollectionRolePermission, fields=['collection', 'item', 'role'], formfield_callback=formfield_callback)
        default_permission_form_class = forms.models.modelform_factory(DefaultPermission, fields=['item', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        default_role_permission_form_class = forms.models.modelform_factory(DefaultRolePermission, fields=['item', 'role'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'agentrolepermission':
                form_class = agent_role_permission_form_class
            elif form_type == 'collectionpermission':
                form_class = collection_permission_form_class
            elif form_type == 'collectionrolepermission':
                form_class = collection_role_permission_form_class
            elif form_type == 'defaultpermission':
                form_class = default_permission_form_class
            elif form_type == 'defaultrolepermission':
                form_class = default_role_permission_form_class
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
                    elif field == 'role':
                        existing_permission = existing_permission.filter(role__pk=data)
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

        agent_permissions = self.item.agent_permissions_as_item.order_by('ability')
        collection_permissions = self.item.collection_permissions_as_item.order_by('ability')
        default_permissions = self.item.default_permissions_as_item.order_by('ability')
        agent_role_permissions = self.item.agent_role_permissions_as_item.order_by('role__name')
        collection_role_permissions = self.item.collection_role_permissions_as_item.order_by('role__name')
        default_role_permissions = self.item.default_role_permissions_as_item.order_by('role__name')
        agents = Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk__in=agent_role_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        collections = Collection.objects.filter(Q(pk__in=collection_permissions.values('collection__pk').query) | Q(pk__in=collection_role_permissions.values('collection__pk').query) | Q(pk=self.request.GET.get('collection', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['role_permissions'] = agent_role_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'item': self.item.pk, 'agent': agent.pk})
            agent_datum['role_permission_form'] = agent_role_permission_form_class(prefix="roleagent%s" % agent.pk, initial={'item': self.item.pk, 'agent': agent.pk})
            agent_data.append(agent_datum)
        collection_data = []
        for collection in collections:
            collection_datum = {}
            collection_datum['collection'] = collection
            collection_datum['permissions'] = collection_permissions.filter(collection=collection)
            collection_datum['role_permissions'] = collection_role_permissions.filter(collection=collection)
            collection_datum['permission_form'] = collection_permission_form_class(prefix="collection%s" % collection.pk, initial={'item': self.item.pk, 'collection': collection.pk})
            collection_datum['role_permission_form'] = collection_role_permission_form_class(prefix="rolecollection%s" % collection.pk, initial={'item': self.item.pk, 'collection': collection.pk})
            collection_data.append(collection_datum)
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
            elif form_type == 'collectionpermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['permission_form'] = form
                collection_datum['permission_form_invalid'] = True
            elif form_type == 'collectionrolepermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['role_permission_form'] = form
                collection_datum['role_permission_form_invalid'] = True
            elif form_type == 'defaultpermission':
                default_data['permission_form'] = form
                default_data['permission_form_invalid'] = True
            elif form_type == 'defaultrolepermission':
                default_data['role_permission_form'] = form
                default_data['role_permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(AgentPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_collection_form_class = forms.models.modelform_factory(CollectionPermission, fields=['collection'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/permissions.html')
        self.context['agent_data'] = agent_data
        self.context['collection_data'] = collection_data
        self.context['default_data'] = default_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_collection_form'] = new_collection_form_class()
        return HttpResponse(template.render(self.context))

    def collection_globalpermissions(self):
        if not self.cur_agent_can_global('do_everything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify global permissions")

        def formfield_callback(f):
            if f.name in ['agent', 'collection', 'item']:
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=f.rel.field_name)
            if isinstance(f, models.ForeignKey):
                return super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name)
            else:
                return f.formfield()

        agent_permission_form_class = forms.models.modelform_factory(AgentGlobalPermission, fields=['agent', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        agent_role_permission_form_class = forms.models.modelform_factory(AgentGlobalRolePermission, fields=['agent', 'global_role'], formfield_callback=formfield_callback)
        collection_permission_form_class = forms.models.modelform_factory(CollectionGlobalPermission, fields=['collection', 'ability', 'is_allowed'], formfield_callback=formfield_callback)
        collection_role_permission_form_class = forms.models.modelform_factory(CollectionGlobalRolePermission, fields=['collection', 'global_role'], formfield_callback=formfield_callback)
        default_permission_form_class = forms.models.modelform_factory(DefaultGlobalPermission, fields=['ability', 'is_allowed'], formfield_callback=formfield_callback)
        default_role_permission_form_class = forms.models.modelform_factory(DefaultGlobalRolePermission, fields=['global_role'], formfield_callback=formfield_callback)

        if self.method == 'POST':
            form_type = self.request.GET.get('formtype')
            if form_type == 'agentpermission':
                form_class = agent_permission_form_class
            elif form_type == 'agentrolepermission':
                form_class = agent_role_permission_form_class
            elif form_type == 'collectionpermission':
                form_class = collection_permission_form_class
            elif form_type == 'collectionrolepermission':
                form_class = collection_role_permission_form_class
            elif form_type == 'defaultpermission':
                form_class = default_permission_form_class
            elif form_type == 'defaultrolepermission':
                form_class = default_role_permission_form_class
            else:
                return self.render_error(HttpResponseBadRequest, 'Invalid Form Type', "You submitted a permission form with an invalid formtype parameter")

            if self.request.POST.get('permission_to_delete') is not None:
                permission = form_class._meta.model.objects.get(pk=self.request.POST.get('permission_to_delete'))
                if isinstance(permission, AgentGlobalPermission) and permission.agent.pk == 1 and permission.ability == 'do_everything':
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
                    elif field == 'global_role':
                        existing_permission = existing_permission.filter(global_role__pk=data)
                    elif field == 'ability':
                        existing_permission = existing_permission.filter(ability=data)
                try:
                    existing_permission = existing_permission.get()
                except ObjectDoesNotExist:
                    existing_permission = None
                if existing_permission:
                    if isinstance(existing_permission, AgentGlobalPermission) and existing_permission.agent.pk == 1 and existing_permission.ability == 'do_everything':
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
        default_permissions = DefaultGlobalPermission.objects.order_by('ability')
        agent_role_permissions = AgentGlobalRolePermission.objects.order_by('global_role__name')
        collection_role_permissions = CollectionGlobalRolePermission.objects.order_by('global_role__name')
        default_role_permissions = DefaultGlobalRolePermission.objects.order_by('global_role__name')
        agents = Agent.objects.filter(Q(pk__in=agent_permissions.values('agent__pk').query) | Q(pk__in=agent_role_permissions.values('agent__pk').query) | Q(pk=self.request.GET.get('agent', 0))).order_by('name')
        collections = Collection.objects.filter(Q(pk__in=collection_permissions.values('collection__pk').query) | Q(pk__in=collection_role_permissions.values('collection__pk').query) | Q(pk=self.request.GET.get('collection', 0))).order_by('name')

        agent_data = []
        for agent in agents:
            agent_datum = {}
            agent_datum['agent'] = agent
            agent_datum['permissions'] = agent_permissions.filter(agent=agent)
            agent_datum['role_permissions'] = agent_role_permissions.filter(agent=agent)
            agent_datum['permission_form'] = agent_permission_form_class(prefix="agent%s" % agent.pk, initial={'agent': agent.pk})
            agent_datum['role_permission_form'] = agent_role_permission_form_class(prefix="roleagent%s" % agent.pk, initial={'agent': agent.pk})
            agent_data.append(agent_datum)
        collection_data = []
        for collection in collections:
            collection_datum = {}
            collection_datum['collection'] = collection
            collection_datum['permissions'] = collection_permissions.filter(collection=collection)
            collection_datum['role_permissions'] = collection_role_permissions.filter(collection=collection)
            collection_datum['permission_form'] = collection_permission_form_class(prefix="collection%s" % collection.pk, initial={'collection': collection.pk})
            collection_datum['role_permission_form'] = collection_role_permission_form_class(prefix="rolecollection%s" % collection.pk, initial={'collection': collection.pk})
            collection_data.append(collection_datum)
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
            elif form_type == 'collectionpermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['permission_form'] = form
                collection_datum['permission_form_invalid'] = True
            elif form_type == 'collectionrolepermission':
                collection_datum = [datum for datum in collection_data if str(datum['collection'].pk) == form['collection'].data][0]
                collection_datum['role_permission_form'] = form
                collection_datum['role_permission_form_invalid'] = True
            elif form_type == 'defaultpermission':
                default_data['permission_form'] = form
                default_data['permission_form_invalid'] = True
            elif form_type == 'defaultrolepermission':
                default_data['role_permission_form'] = form
                default_data['role_permission_form_invalid'] = True

        new_agent_form_class = forms.models.modelform_factory(AgentGlobalPermission, fields=['agent'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))
        new_collection_form_class = forms.models.modelform_factory(CollectionGlobalPermission, fields=['collection'], formfield_callback=lambda f: super(models.ForeignKey, f).formfield(queryset=f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=f.rel.field_name))

        template = loader.get_template('item/globalpermissions.html')
        self.context['agent_data'] = agent_data
        self.context['collection_data'] = collection_data
        self.context['default_data'] = default_data
        self.context['new_agent_form'] = new_agent_form_class()
        self.context['new_collection_form'] = new_collection_form_class()
        return HttpResponse(template.render(self.context))


class GroupViewer(ItemViewer):
    item_type = Group
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
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        template = loader.get_template('group/show.html')
        return HttpResponse(template.render(self.context))


class ViewerRequestViewer(ItemViewer):
    item_type = ViewerRequest
    viewer_name = 'viewerrequest'

    def entry_show(self):
        site, custom_urls = self.item.calculate_full_path()
        self.context['site'] = site
        self.context['custom_urls'] = custom_urls
        self.context['child_urls'] = self.item.child_urls.filter(trashed=False)
        self.context['addsubpath_form'] = AddSubPathForm(initial={'parent_url':self.item.pk})
        template = loader.get_template('viewerrequest/show.html')
        return HttpResponse(template.render(self.context))


    def entry_addsubpath(self):
        form = AddSubPathForm(self.request.POST, self.request.FILES)
        if form.data['parent_url'] != str(self.item.pk):
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the parent url you are extending")
        if not self.cur_agent_can('add_sub_path', self.item):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add a sub path to this url")
        try:
            custom_url = CustomUrl.objects.get(parent_url=self.item, path=form.data['path'])
            form = AddSubPathForm(self.request.POST, self.request.FILES, instance=custom_url)
        except:
            pass
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(updater=self.cur_agent)
            if custom_url.trashed:
                custom_url.untrash(self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            site, custom_urls = self.item.calculate_full_path()
            self.context['site'] = site
            self.context['custom_urls'] = custom_urls
            self.context['child_urls'] = self.item.child_urls.filter(trashed=False)
            self.context['addsubpath_form'] = form
            template = loader.get_template('viewerrequest/show.html')
            return HttpResponse(template.render(self.context))


class CollectionViewer(ItemViewer):
    item_type = Collection
    viewer_name = 'collection'

    def entry_show(self):
        memberships = self.item.memberships_as_collection
        memberships = memberships.filter(trashed=False)
        memberships = memberships.filter(item__trashed=False)
        if not self.cur_agent_can_global('do_everything'):
            memberships = memberships.filter(permissions.filter_items_by_permission(self.cur_agent, 'view item'))
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.mass_learn(self.cur_agent, 'view name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can(self.cur_agent, 'view name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.memberships_as_collection.filter(trashed=False, item=self.cur_agent))
        self.context['addmember_form'] = NewMembershipForm()
        template = loader.get_template('collection/show.html')
        return HttpResponse(template.render(self.context))


    def entry_addmember(self):
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('add_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add this member to this Collection")
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if membership.trashed:
                membership.untrash(self.cur_agent)
        except:
            membership = Membership(collection=self.item, item=member)
            membership.save_versioned(updater=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


    def entry_removemember(self):
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('remove_self', self.item))):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to remove this member from this Collection")
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if not membership.trashed:
                membership.trash(self.cur_agent)
        except:
            pass
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


class ImageDocumentViewer(ItemViewer):
    item_type = ImageDocument
    viewer_name = 'imagedocument'

    def entry_show(self):
        template = loader.get_template('imagedocument/show.html')
        return HttpResponse(template.render(self.context))


class TextDocumentViewer(ItemViewer):
    item_type = TextDocument
    viewer_name = 'textdocument'

    def entry_show(self):
        template = loader.get_template('textdocument/show.html')
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))


    def entry_edit(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)


        transclusions = Transclusion.objects.filter(from_item=self.item, from_item_version_number=self.item.version_number).order_by('-from_item_index')
        body_as_list = list(self.item.body)
        for transclusion in transclusions:
            if issubclass(self.item_type, HtmlDocument):
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
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        abilities_for_item = self.permission_cache.item_abilities(self.cur_agent, self.item)
        can_edit = any(x.split(' ')[0] == 'edit' for x in abilities_for_item)
        if not can_edit:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to edit this item")
        new_item = self.item
        fields_can_edit = [x.split(' ')[1] for x in abilities_for_item if x.split(' ')[0] == 'edit']
        form_class = get_form_class_for_item_type('update', self.item_type, fields_can_edit)
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
                if issubclass(self.item_type, HtmlDocument):
                    transclusion_re = r'(?i)<img[^>]+transclusion_(\d+)[^>]*>'
                else:
                    transclusion_re = r'<deme_transclusion id="(\d+)"/>'
                new_item.body, n_subs = re.subn(transclusion_re, repl, new_item.body, 1)
                if n_subs == 0:
                    break
            
            new_item.save_versioned(updater=self.cur_agent)

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
                    transclusion.save_versioned(updater=self.cur_agent)

            return HttpResponseRedirect(reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            template = loader.get_template('item/edit.html')
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
            return HttpResponse(template.render(self.context))


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    item_type = DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def entry_render(self):
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
    __metaclass__ = ViewerMetaClass

    item_type = TextComment
    viewer_name = 'textcomment'

    def collection_new(self):
        try:
            commented_item = Item.objects.get(pk=self.request.GET.get('commented_item'))
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
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        try:
            commented_item = Item.objects.get(pk=self.request.POST.get('commented_item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are commenting on")
        can_comment_on = self.cur_agent_can('comment_on', commented_item)
        if not can_comment_on:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to comment on this item")
        form_class = NewTextCommentForm
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the Transclusion save at the same time as the Comment
            commented_item_index = form.cleaned_data['commented_item_index']
            item = form.save(commit=False)
            item.save_versioned(updater=self.cur_agent)
            commented_item = item.commented_item.downcast()
            if isinstance(commented_item, TextDocument) and commented_item_index is not None and self.permission_cache.agent_can(self.cur_agent, 'add_transclusion', commented_item):
                transclusion = Transclusion(from_item=commented_item, from_item_version_number=item.commented_item_version_number, from_item_index=commented_item_index, to_item=item)
                transclusion.save_versioned(updater=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update comments


class TransclusionViewer(ItemViewer):
    __metaclass__ = ViewerMetaClass

    item_type = Transclusion
    viewer_name = 'transclusion'

    def collection_new(self):
        try:
            from_item = Item.objects.get(pk=self.request.GET.get('from_item'))
        except:
            return self.render_error(HttpResponseBadRequest, 'Invalid URL', "You must specify the item you are adding a transclusion to")
        can_add_transclusion = self.cur_agent_can('add_transclusion', from_item)
        if not can_add_transclusion:
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add transclusions to this item")
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type('create', self.item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        form_class = get_form_class_for_item_type('create', self.item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the Transclusion save at the same time as the Comment
            item = form.save(commit=False)
            can_add_transclusion = self.cur_agent_can('add_transclusion', item.from_item)
            if not can_add_transclusion:
                return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to add transclusions to this item")
            item.save_versioned(updater=self.cur_agent)
            redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': self.viewer_name, 'noun': item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            self.context['is_html'] = issubclass(self.item_type, HtmlDocument)
            self.context['redirect'] = self.request.GET.get('redirect')
            return HttpResponse(template.render(self.context))

    #TODO copy/edit/update transclusions


class TextDocumentExcerptViewer(TextDocumentViewer):
    __metaclass__ = ViewerMetaClass

    item_type = TextDocumentExcerpt
    viewer_name = 'textdocumentexcerpt'

    def collection_createmultiexcerpt(self):
        if not self.cur_agent_can_global('create %s' % self.item_type.__name__):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to create %ss" % self.item_type.__name__)
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
        collection.save_versioned(updater=self.cur_agent)
        for excerpt in excerpts:
            excerpt.save_versioned(updater=self.cur_agent)
            Membership(item=excerpt, collection=collection).save_versioned(updater=self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_entry', kwargs={'viewer': 'collection', 'noun': collection.pk}))
        return HttpResponseRedirect(redirect)


class DemeSettingViewer(ItemViewer):
    item_type = DemeSetting
    viewer_name = 'demesetting'

    def collection_modify(self):
        if not self.cur_agent_can_global('do_everything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify DemeSettings")
        self.context['deme_settings'] = DemeSetting.objects.filter(trashed=False).order_by('key')
        template = loader.get_template('demesetting/modify.html')
        return HttpResponse(template.render(self.context))

    def collection_addsetting(self):
        if not self.cur_agent_can_global('do_everything'):
            return self.render_error(HttpResponseBadRequest, 'Permission Denied', "You do not have permission to modify DemeSettings")
        key = self.request.POST.get('key')
        value = self.request.POST.get('value')
        DemeSetting.set(key, value, self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('resource_collection', kwargs={'viewer': self.viewer_name, 'action': 'modify'}))
        return HttpResponseRedirect(redirect)


# Dynamically create default viewers for the ones we don't have.
for item_type in all_models():
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
            import new
            viewer_class_def = new.classobj(viewer_class_name, (parent_viewer_class,), {'item_type': item_type, 'viewer_name': viewer_name})
            exec('global %s;%s = viewer_class_def'%(viewer_class_name, viewer_class_name))
        else:
            pass

