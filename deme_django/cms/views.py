# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
from django.db.models import Q
import cms.models
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging
import permission_functions

### MODELS ###

resource_name_dict = {}
for model in cms.models.all_models():
    resource_name_dict[model.__name__.lower()] = model

def get_form_class_for_item_type(item_type, fields=None):
    exclude = []
    for field in item_type._meta.fields:
        if field.rel and field.rel.parent_link:
            exclude.append(field.name)
    if issubclass(item_type, cms.models.Group):
        exclude.append('folio')
    return forms.models.modelform_factory(item_type, exclude=exclude, fields=fields)

### VIEWERS ###

def comment_dicts_for_item(item):
    comments = item.comments_as_item.order_by('updated_at')
    result = []
    for comment in comments:
        comment_info = {}
        comment_info['comment'] = comment
        comment_info['subcomments'] = comment_dicts_for_item(comment)
        result.append(comment_info)
    return result


class ViewerMetaClass(type):
    viewer_name_dict = {}
    def __new__(cls, name, bases, attrs):
        result = super(ViewerMetaClass, cls).__new__(cls, name, bases, attrs)
        ViewerMetaClass.viewer_name_dict[attrs['viewer_name']] = result
        return result

def get_viewer_class_for_viewer_name(viewer_name):
    return ViewerMetaClass.viewer_name_dict.get(viewer_name, None)

class ItemViewer(object):
    __metaclass__ = ViewerMetaClass

    item_type = cms.models.Item
    viewer_name = 'item'

    def __init__(self):
        pass

    def init_from_http(self, request, cur_agent, url_info):
        self.layout = 'base.html'
        self.viewer_name = url_info['viewer']
        self.format = url_info['format'] or 'html'
        self.method = (request.REQUEST.get('_method', None) or request.method).upper()
        self.request = request # FOR NOW
        self.noun = url_info['noun']
        if self.noun == None:
            self.action = url_info['collection_action']
            if self.action == None:
                self.action = {'GET': 'list', 'POST': 'create', 'PUT': 'update', 'DELETE': 'delete'}.get(self.method, 'list')
        else:
            self.action = url_info['entry_action']
            if self.action == None:
                self.action = {'GET': 'show', 'POST': 'create', 'PUT': 'update', 'DELETE': 'delete'}.get(self.method, 'show')
            try:
                self.item = cms.models.Item.objects.get(pk=self.noun)
                if 'version' in self.request.REQUEST:
                    self.itemversion = cms.models.Item.VERSION.objects.get(current_item=self.noun, version_number=self.request.REQUEST['version'])
                else:
                    try:
                        self.itemversion = cms.models.Item.VERSION.objects.filter(current_item=self.noun, trashed=False).latest()
                    except ObjectDoesNotExist:
                        self.itemversion = cms.models.Item.VERSION.objects.filter(current_item=self.noun).latest()
            except ObjectDoesNotExist:
                self.item = None
                self.itemversion = None
            if self.item:
                self.item = self.item.downcast()
                self.itemversion = self.itemversion.downcast()
        self.context = Context()
        self.context['layout'] = self.layout
        self.context['item_type'] = self.item_type.__name__
        self.context['item_type_inheritance'] = [x.__name__ for x in reversed(self.item_type.mro()) if issubclass(x, cms.models.Item)]
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = cur_agent
        self.context['cur_agent'] = self.cur_agent

    def init_show_from_div(self, original_request, viewer_name, item, itemversion, cur_agent):
        self.layout = 'blank.html'
        self.request = original_request
        self.viewer_name = viewer_name
        self.format = 'html'
        self.method = 'GET'
        self.noun = item.pk
        self.item = item
        self.itemversion = itemversion
        self.action = 'show'
        self.context = Context()
        self.context['layout'] = self.layout
        self.context['item_type'] = self.item_type.__name__
        self.context['item_type_inheritance'] = [x.__name__ for x in reversed(self.item_type.mro()) if issubclass(x, cms.models.Item)]
        self.context['full_path'] = self.request.get_full_path()
        self.cur_agent = cur_agent
        self.context['cur_agent'] = self.cur_agent

    def dispatch(self):
        if ('do_something', 'Item') not in permission_functions.get_global_abilities_for_agent(self.cur_agent):
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
                if (self.action == 'edit' or self.action == 'update'):
                    if not issubclass(self.item_type, type(self.item)):
                        return self.render_item_not_found()
                else:
                    if not isinstance(self.item, self.item_type):
                        return self.render_item_not_found()
            return action_method()
        else:
            return None

    def render_item_not_found(self):
        template = loader.get_template('item_not_found.html')
        self.context['item'] = self.item
        self.context['noun'] = self.noun
        self.context['viewer'] = self.viewer_name
        return HttpResponseNotFound(template.render(self.context))

    def collection_list(self):
        #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
        offset = int(self.request.GET.get('offset', 0))
        limit = int(self.request.GET.get('limit', 100))
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        self.context['search_query'] = self.request.GET.get('q', '')
        if self.context['search_query']:
            items = self.item_type.objects.filter(description__icontains=self.request.GET['q'])
        else:
            items = self.item_type.objects
        if ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent):
            listable_items = items
        else:
            listable_items = items.filter(permission_functions.filter_for_agent_and_ability(self.cur_agent, 'view', 'id')).distinct()
        listable_items = listable_items.filter(trashed=False) #TODO add the ability to look at trashed items somewhere
        n_items = items.count()
        n_listable_items = listable_items.count()
        items = [item for item in listable_items.all()[offset:offset+limit]]
        template = loader.get_template('item/list.html')
        self.context['model_names'] = model_names
        self.context['items'] = items
        self.context['n_items'] = n_items
        self.context['n_listable_items'] = n_listable_items
        self.context['n_unlistable_items'] = n_items - n_listable_items
        self.context['offset'] = offset
        self.context['limit'] = limit
        self.context['list_start_i'] = offset + 1
        self.context['list_end_i'] = min(offset + limit, n_listable_items)
        return HttpResponse(template.render(self.context))

    def collection_new(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        can_create = ('create', self.item_type.__name__) in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        if not (can_do_everything or can_create):
            return HttpResponseBadRequest("you do not have permission to create %ss" % self.item_type.__name__)
        #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        form_class = get_form_class_for_item_type(self.item_type)
        form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        if 'redirect' in self.request.GET:
            self.context['redirect'] = self.request.GET['redirect']
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        can_create = ('create', self.item_type.__name__) in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        if not (can_do_everything or can_create):
            return HttpResponseBadRequest("you do not have permission to create %ss" % self.item_type.__name__)
        form_class = get_form_class_for_item_type(self.item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save_versioned(updater=self.cur_agent)
	    
	    # hacky email sender for comments
	    if isinstance(item, cms.models.Comment):
	        commented_item = item.commented_item.downcast()
		if isinstance(commented_item, cms.models.Group):
		    persons_in_group = cms.models.Person.objects.filter(group_memberships_as_agent__group=commented_item).all()
		    recipient_list = [x.email for x in persons_in_group]
		    if recipient_list:
		        from django.core.mail import send_mail
			subject = '[%s] %s' % (commented_item.get_name(), item.get_name())
			message = '%s wrote a comment in %s\n%s\n\n%s' % (self.cur_agent.get_name(), commented_item.get_name(), 'http://deme.stanford.edu/resource/group/%d' % commented_item.pk, item.body)
			from_email = 'noreply@deme.stanford.edu'
			send_mail(subject, message, from_email, recipient_list)

            redirect = self.request.GET.get('redirect', '/resource/%s/%d' % (self.viewer_name, item.pk))
            return HttpResponseRedirect(redirect)
        else:
            #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
            model_names.sort()
            template = loader.get_template('item/new.html')
            self.context['model_names'] = model_names
            self.context['form'] = form
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_view = ('view', 'id') in abilities_for_item
        if not (can_do_everything or can_view):
            return HttpResponseBadRequest("you do not have permission to view this item")
        comments = comment_dicts_for_item(self.item)
        def get_fields_for_item(item):
            #TODO we ignore OneToOneFields and ManyToManyFields
            fields = []
            for name in item._meta.get_all_field_names():
                field, model, direct, m2m = item._meta.get_field_by_name(name)
                model_class = type(item) if model == None else model
                model_class = model_class.NOTVERSION if issubclass(model_class, cms.models.Item.VERSION) else model_class
                model_name = model_class.__name__
                info = {'model_name': model_name, 'name': name, 'format': type(field).__name__}
                if type(field).__name__ == 'RelatedObject':
                    forward_field = field.field
                    if type(forward_field).__name__ == 'ForeignKey':
                        try:
                            obj = getattr(item, name)
                        except ObjectDoesNotExist:
                            obj = None
                        if obj:
                            #obj = [x.downcast() for x in obj.all()]
                            obj = [x for x in obj.all()]
                        info['field_type'] = 'collection'
                    else:
                        continue
                elif type(field).__name__ == 'ForeignKey':
                    try:
                        obj = getattr(item, name)
                    except ObjectDoesNotExist:
                        obj = None
                    if obj:
                        pass#obj = obj.downcast()
                    info['field_type'] = 'entry'
                elif type(field).__name__ == 'OneToOneField':
                    continue
                elif type(field).__name__ == 'ManyToManyField':
                    continue
                else:
                    obj = getattr(item, name)
                    info['field_type'] = 'regular'
                info['obj'] = obj
                info['can_view'] = ('view', name) in abilities_for_item or can_do_everything
                #TODO do something like can_view with collections
                fields.append(info)
            return fields
        roles = permission_functions.get_roles_for_agent_and_item(self.cur_agent, self.item)
        template = loader.get_template('item/show.html')
        self.context['inheritance'] = [x.__name__ for x in reversed(type(self.item).mro()) if issubclass(x, cms.models.Item)]
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['comments'] = comments
        self.context['item_fields'] = get_fields_for_item(self.item)
        self.context['itemversion_fields'] = get_fields_for_item(self.itemversion)
        self.context['direct_roles'] = roles[0].all()
        self.context['groupwide_roles'] = roles[1].all()
        self.context['default_roles'] = roles[2].all()
        self.context['abilities'] = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        return HttpResponse(template.render(self.context))

    def entry_edit(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = ('edit', 'id') in abilities_for_item
        if not (can_do_everything or can_edit):
            return HttpResponseBadRequest("you do not have permission to edit this item")
        fields_can_edit = [x[1] for x in abilities_for_item if x[0] == 'edit']
        form_class = get_form_class_for_item_type(self.item_type, fields_can_edit)
        form = form_class(instance=self.itemversion)
        template = loader.get_template('item/edit.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['form'] = form
        self.context['query_string'] = self.request.META['QUERY_STRING']
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, type(self.item))]
        model_names.sort()
        self.context['model_names'] = model_names
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_edit = ('edit', 'id') in abilities_for_item
        if not (can_do_everything or can_edit):
            return HttpResponseBadRequest("you do not have permission to edit this item")
        #TODO if specified specific version and uploaded file blank, it would revert to newest version uploaded file
        if issubclass(self.item_type, type(self.item)):
            new_item = self.item_type()
            for field in self.item._meta.fields:
                key = field.name
                val = getattr(self.item, key)
                setattr(new_item, key, val)
            new_item.pk = self.item.pk
            new_item.item_type = self.item_type.__name__
        else:
            new_item = self.item
        fields_can_edit = [x[1] for x in abilities_for_item if x[0] == 'edit']
        form_class = get_form_class_for_item_type(self.item_type, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(updater=self.cur_agent)
            return HttpResponseRedirect('/resource/%s/%d' % (self.viewer_name, new_item.pk))
        else:
            template = loader.get_template('item/edit.html')
            self.context['item'] = self.item
            self.context['itemversion'] = self.itemversion
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, type(self.item))]
            model_names.sort()
            self.context['model_names'] = model_names
            return HttpResponse(template.render(self.context))

    def entry_trash(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_trash = ('trash', 'id') in abilities_for_item
        if not (can_do_everything or can_trash):
            return HttpResponseBadRequest("you do not have permission to trash this item")
        if 'version' in self.request.GET:
            self.itemversion.trash()
        else:
            self.item.trash()
        return HttpResponseRedirect('/resource/%s/%d' % (self.viewer_name,self.item.pk))

    def entry_untrash(self):
        can_do_everything = ('do_everything', 'Item') in permission_functions.get_global_abilities_for_agent(self.cur_agent)
        abilities_for_item = permission_functions.get_abilities_for_agent_and_item(self.cur_agent, self.item)
        can_trash = ('trash', 'id') in abilities_for_item
        if not (can_do_everything or can_trash):
            return HttpResponseBadRequest("you do not have permission to untrash this item")
        if 'version' in self.request.GET:
            self.itemversion.untrash()
        else:
            self.item.untrash()
        return HttpResponseRedirect('/resource/%s/%d' % (self.viewer_name,self.item.pk))

    def entry_delete(self):
        #TODO this doesn't really work
        cms.models.Item.objects.get(pk=self.item.pk).delete()
        return HttpResponseRedirect('/resource/%s' % (self.viewer_name,))


class GroupViewer(ItemViewer):
    item_type = cms.models.Group
    viewer_name = 'group'

    def collection_create(self):
        #TODO if you self.update an Item into a Group, it doesn't make a Folio
        form_class = get_form_class_for_item_type(self.item_type)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(updater=self.cur_agent)
            folio = cms.models.Folio(name="Group Folio", group=new_item)
            folio.save_versioned(updater=self.cur_agent)
            return HttpResponseRedirect('/resource/%s/%d' % (self.viewer_name, new_item.pk))
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        folio = self.item.folios_as_group.get()
        folio_viewer_class = get_viewer_class_for_viewer_name('itemset')
        folio_viewer = folio_viewer_class()
        folio_viewer.init_show_from_div(self.request, 'itemset', folio, folio.versions.latest(), self.cur_agent)
        folio_html = folio_viewer.dispatch().content
        template = loader.get_template('group/show.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['comments'] = comments
        self.context['folio_html'] = folio_html
        return HttpResponse(template.render(self.context))


class ItemSetViewer(ItemViewer):
    item_type = cms.models.ItemSet
    viewer_name = 'itemset'

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        template = loader.get_template('itemset/show.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['comments'] = comments
        return HttpResponse(template.render(self.context))


class TextDocumentViewer(ItemViewer):
    item_type = cms.models.TextDocument
    viewer_name = 'textdocument'

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        template = loader.get_template('textdocument/show.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['comments'] = comments
        return HttpResponse(template.render(self.context))

    def collection_getregions(self):
        data = '[["refbase_123::14", "refbase_123::18"]]'
        return HttpResponse(data)


class HtmlDocumentViewer(TextDocumentViewer):
    item_type = cms.models.HtmlDocument
    viewer_name = 'htmldocument'

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        template = loader.get_template('htmldocument/show.html')
        self.context['item'] = self.item
        self.context['itemversion'] = self.itemversion
        self.context['comments'] = comments
        return HttpResponse(template.render(self.context))

    def collection_getregions(self):
        data = '[["refbase_123::14", "refbase_123::18"]]'
        return HttpResponse(data)


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    item_type = cms.models.DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def entry_show(self):
        code = self.itemversion.body
        template = loader.get_template_from_string(code)
        return HttpResponse(template.render(self.context))


class MagicViewer(ItemViewer):
    item_type = cms.models.Item
    viewer_name = 'blam'

    def collection_list(self):
        return HttpResponse('ka BLAM!')

    def entry_show(self):
        return HttpResponse('ka BLAM!')


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

