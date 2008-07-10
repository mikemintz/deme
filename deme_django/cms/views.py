# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound
from django.template import Context, loader
import cms.models
from django import newforms as forms
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import QueryDict
from django.utils import datastructures
import logging

### MODELS ###

resource_name_dict = {}
for model in cms.models.all_models:
    resource_name_dict[model.__name__.lower()] = model

def get_viewer_class_for_item_type(item_type):
    while issubclass(item_type, cms.models.Item):
        try:
            viewer_class = eval("%sViewer" % item_type.__name__)
        except NameError:
            item_type = item_type.__base__
            continue
        return viewer_class

def get_form_class_for_item_type(item_type):
    while issubclass(item_type, cms.models.Item):
        try:
            form_class = eval("%sForm" % item_type.__name__)
        except NameError:
            item_type = item_type.__base__
            continue
        return form_class

def get_roles_for_agent_and_item(agent, item):
    """
    Return a triple (user_role_list, group_role_list, default_role_list)
    """
    if item:
        agent_role_with_item_filter = cms.models.Role.objects.filter(agent_item_relationships_as_role__item2=item)
        group_role_with_item_filter = cms.models.Role.objects.filter(group_item_relationships_as_role__item2=item)
    else:
        agent_role_with_item_filter = cms.models.Role.objects.filter(agent_item_relationships_as_role__item2__isnull=True)
        group_role_with_item_filter = cms.models.Role.objects.filter(group_item_relationships_as_role__item2__isnull=True)
    default_roles = agent_role_with_item_filter.filter(agent_item_relationships_as_role__item1__isnull=True)
    if agent:
        direct_roles = agent_role_with_item_filter.filter(agent_item_relationships_as_role__item1=agent)
        groupwide_roles = group_role_with_item_filter.filter(group_item_relationships_as_role__item1__agent_relationships__item1=agent)
    else:
        direct_roles = agent_role_with_item_filter.filter(agent_item_relationships_as_role__item1__is_anonymous=True)
        groupwide_roles = group_role_with_item_filter.filter(group_item_relationships_as_role__item1__agent_relationships__item1__is_anonymous=True)
    return (direct_roles, groupwide_roles, default_roles)

def get_abilities_for_roles(roles_triple, possible_abilities=None):
    abilities_yes = set()
    abilities_no = set()
    if possible_abilities:
        abilities_unset = set(possible_abilities)
    else:
        abilities_unset = set([x[0] for x in cms.models.RolePermission._meta.get_field('ability').choices])
    for role_list in roles_triple:
        if possible_abilities:
            role_permissions = cms.models.RolePermission.objects.filter(role__in=role_list, ability_in=possible_abilities).all()
        else:
            role_permissions = cms.models.RolePermission.objects.filter(role__in=role_list).all()
        for role_permission in role_permissions:
            ability = role_permission.ability
            if ability in abilities_unset:
                # yes takes precedence over no
                if role_permission.is_allowed:
                    abilities_yes.add(ability)
                    abilities_no.discard(ability)
                else:
                    if ability not in abilities_yes:
                        abilities_no.add(ability)
                abilities_unset.discard(ability)
    # anything left over in abilities_unset is effectively "no"
    return abilities_yes

### VIEWS ###

def index(request):
    template = loader.get_template('index.html')
    context = Context()
    context['layout'] = 'base.html'
    context['full_path'] = request.get_full_path()
    context['recent_items'] = [x.downcast() for x in cms.models.Item.objects.order_by('-updated_at').all()[0:10]]
    #TODO add versions here
    return HttpResponse(template.render(context))

def resource(request, *args, **kwargs):
    item_type = resource_name_dict.get(kwargs['item_type'], None)
    if item_type:
        viewer_class = get_viewer_class_for_item_type(item_type)
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
        template = loader.get_template('item_type_not_found.html')
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

def alias(request, *args, **kwargs):
    hostname = request.META['HTTP_HOST'].split(':')[0]
    try:
        current_site = cms.models.Site.objects.filter(site_domains_as_site__hostname=hostname)[0:1].get()
    except ObjectDoesNotExist:
        try:
            current_site = cms.models.Site.objects.filter(is_default_site=True)[0:1].get()
        except ObjectDoesNotExist:
            current_site = None
    path_parts = [x for x in request.path.split('/') if x]
    parent_url = None
    alias_url = None
    for path_part in path_parts:
        try:
            alias_url = cms.models.AliasUrl.objects.filter(site=current_site, path=path_part, parent_url=parent_url)[0:1].get()
            parent_url = alias_url
        except ObjectDoesNotExist:
            template = loader.get_template('alias_not_found.html')
            context = Context()
            context['layout'] = 'base.html'
            context['hostname'] = request.META['HTTP_HOST']
            context['path'] = request.path
            return HttpResponseNotFound(template.render(context))
    if alias_url:
        item = alias_url.aliased_item
        kwargs = {}
        kwargs['item_type'] = alias_url.viewer
        kwargs['format'] = 'html'
        if item:
            kwargs['noun'] = str(item.pk)
            kwargs['collection_action'] = None
            kwargs['entry_action'] = alias_url.action
        else:
            kwargs['noun'] = None
            kwargs['collection_action'] = alias_url.action
            kwargs['entry_action'] = None
        query_dict = QueryDict(alias_url.query_string).copy()
        #TODO this is quite hacky, let's fix this when we finalize sites and stuff
        query_dict.update(request.GET)
        request.GET = query_dict
        request._request = datastructures.MergeDict(request.POST, request.GET)
        return resource(request, **kwargs)
    else:
        return index(request)

### FORMS ###

import new
for model in cms.models.all_models:
    meta_class_dict = {}
    meta_class_dict['model'] = model
    meta_class_dict['exclude'] = ()
    for field in model._meta.fields:
        if field.rel and field.rel.parent_link:
            meta_class_dict['exclude'] += (field.name,)
    meta_class_def = new.classobj('Meta', (), meta_class_dict)
    form_class_name = '%sForm' % model.__name__
    form_class_def = new.classobj(form_class_name, (forms.ModelForm,), {'Meta': meta_class_def})
    exec('global %s;%s = form_class_def'%(form_class_name, form_class_name))

class GroupForm(forms.ModelForm):
    class Meta:
        model = cms.models.Group
        exclude = ()
        for field in model._meta.fields:
            if field.rel and field.rel.parent_link:
                exclude += (field.name,)
        exclude += ('folio',)

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


class ItemViewer(object):

    def __init__(self):
        pass

    def init_from_http(self, request, url_info):
        self.layout = 'base.html'
        self.item_type = resource_name_dict.get(url_info['item_type'], None)
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
                if self.request.has_key('version'):
                    self.itemrev = cms.models.Item.REV.objects.get(current_item=self.noun, version=self.request['version'])
                else:
                    self.itemrev = cms.models.Item.REV.objects.filter(current_item=self.noun).order_by('-version')[0]
            except ObjectDoesNotExist:
                self.item = None
                self.itemrev = None
            if self.item:
                self.item = self.item.downcast()
                self.itemrev = self.itemrev.downcast()
        self.form_class = get_form_class_for_item_type(self.item_type)
        self.context = Context()
        self.context['layout'] = self.layout
        self.context['item_type'] = self.item_type.__name__
        self.context['item_type_inheritance'] = [x.__name__ for x in reversed(self.item_type.mro()) if issubclass(x, cms.models.Item)]
        self.context['full_path'] = self.request.get_full_path()
        account_unique_id = self.request.session.get('account_unique_id', None)
        if account_unique_id != None:
            try:
                self.context['cur_account'] = cms.models.Account.objects.get(pk=account_unique_id)
            except ObjectDoesNotExist:
                self.context['cur_account'] = None
                del self.request.session['account_unique_id']
        else:
            self.context['cur_account'] = None
        if not self.context['cur_account']:
            try:
                self.context['cur_account'] = cms.models.Account.objects.filter(agent__is_anonymous=True)[0:1].get()
            except ObjectDoesNotExist:
                pass
        if self.context['cur_account']:
            self.context['cur_agent'] = self.context['cur_account'].agent
        else:
            self.context['cur_agent'] = None
        self.context['all_accounts'] = cms.models.Account.objects.all()

    def init_show_from_div(self, original_request, item_type, item, itemrev):
        self.layout = 'blank.html'
        self.request = original_request
        self.item_type = item_type
        self.format = 'html'
        self.method = 'GET'
        self.noun = item.pk
        self.item = item
        self.itemrev = itemrev
        self.action = 'show'
        self.context = Context()
        self.context['layout'] = self.layout
        self.context['item_type'] = self.item_type.__name__
        self.context['full_path'] = self.request.get_full_path()
        account_unique_id = self.request.session.get('account_unique_id', None)
        if account_unique_id != None:
            try:
                self.context['cur_account'] = cms.models.Account.objects.get(pk=account_unique_id)
            except ObjectDoesNotExist:
                self.context['cur_account'] = None
                del self.request.session['account_unique_id']
        else:
            self.context['cur_account'] = None
        if self.context['cur_account']:
            self.context['cur_agent'] = self.context['cur_account'].agent
        else:
            self.context['cur_agent'] = None
        self.context['all_accounts'] = cms.models.Account.objects.all()

    def dispatch(self):
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
        return HttpResponseNotFound(template.render(self.context))

    def collection_list(self):
        #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        if 'q' in self.request:
            items = self.item_type.objects.filter(description__contains=self.request['q'])
            self.context['search_query'] = self.request['q']
        else:
            items = self.item_type.objects.all()
            self.context['search_query'] = ''
        template = loader.get_template('item/list.html')
        self.context['model_names'] = model_names
        self.context['items'] = items
        return HttpResponse(template.render(self.context))

    def collection_search(self):
        #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        items = self.item_type.objects.filter(description__contains=self.request['q'])
        template = loader.get_template('item/list.html')
        self.context['model_names'] = model_names
        self.context['items'] = items
        return HttpResponse(template.render(self.context))

    def collection_new(self):
        #model_names = [model.__name__ for model in resource_name_dict.itervalues()]
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, self.item_type)]
        model_names.sort()
        form_initial = dict(self.request.GET.items())
        if self.context['cur_account']:
            form_initial['last_author'] = self.context['cur_account'].agent.pk
        form = self.form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['model_names'] = model_names
        self.context['form'] = form
        if 'redirect' in self.request.GET:
            self.context['redirect'] = self.request.GET['redirect']
        return HttpResponse(template.render(self.context))

    def collection_create(self):
        form = self.form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.save_versioned()
            redirect = self.request.GET.get('redirect', '/resource/%s/%d' % (item.item_type.lower(), item.pk))
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
        comments = comment_dicts_for_item(self.item)
        def get_fields_for_item(item):
            fields = []
            for name in item._meta.get_all_field_names():
                field, model, direct, m2m = item._meta.get_field_by_name(name)
                model_class = type(item) if model == None else model
                model_class = model_class.NOTREV if issubclass(model_class, cms.models.Item.REV) else model_class
                model_name = model_class.__name__
                info = {'model_name': model_name, 'name': name, 'format': type(field).__name__}
                if type(field).__name__ == 'RelatedObject':
                    forward_field = field.field
                    if type(forward_field).__name__ == 'OneToOneField':
                        continue # ignore onetoonefields
                        try:
                            obj = getattr(item, name)
                        except ObjectDoesNotExist:
                            obj = None
                        info['field_type'] = 'entry'
                    elif type(forward_field).__name__ == 'ForeignKey':
                        try:
                            obj = getattr(item, name)
                        except ObjectDoesNotExist:
                            obj = None
                        if obj:
                            obj = obj.all()
                        info['field_type'] = 'collection'
                    else:
                        obj = None
                        info['field_type'] = 'unknown'
                elif type(field).__name__ == 'OneToOneField':
                    continue # ignore onetoonefields
                    try:
                        obj = getattr(item, name)
                    except ObjectDoesNotExist:
                        obj = None
                    info['field_type'] = 'entry'
                elif type(field).__name__ == 'ForeignKey':
                    try:
                        obj = getattr(item, name)
                    except ObjectDoesNotExist:
                        obj = None
                    info['field_type'] = 'entry'
                else:
                    obj = getattr(item, name)
                    info['field_type'] = 'regular'
                info['obj'] = obj
                fields.append(info)
            return fields
        roles = get_roles_for_agent_and_item(self.context['cur_agent'], self.item)
        template = loader.get_template('item/show.html')
        self.context['inheritance'] = [x.__name__ for x in reversed(type(self.item).mro()) if issubclass(x, cms.models.Item)]
        self.context['item'] = self.item
        self.context['itemrev'] = self.itemrev
        self.context['comments'] = comments
        self.context['item_fields'] = get_fields_for_item(self.item)
        self.context['itemrev_fields'] = get_fields_for_item(self.itemrev)
        self.context['direct_roles'] = roles[0].all()
        self.context['groupwide_roles'] = roles[1].all()
        self.context['default_roles'] = roles[2].all()
        self.context['abilities'] = get_abilities_for_roles(roles)
        return HttpResponse(template.render(self.context))

    def entry_edit(self):
        if self.context['cur_account']:
            self.itemrev.last_author = self.context['cur_account'].agent
        form = self.form_class(instance=self.itemrev)
        template = loader.get_template('item/edit.html')
        self.context['item'] = self.item
        self.context['itemrev'] = self.itemrev
        self.context['form'] = form
        self.context['query_string'] = self.request.META['QUERY_STRING']
        model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, type(self.item))]
        model_names.sort()
        self.context['model_names'] = model_names
        return HttpResponse(template.render(self.context))

    def entry_update(self):
        #TODO if specified specific version and uploaded file blank, it would revert to newest version uploaded file
        if issubclass(self.item_type, type(self.item)):
            new_item = self.item_type(**self.item.__dict__)
            new_item.pk = self.item.pk
            new_item.item_type = self.item_type.__name__
        else:
            new_item = self.item
        form = self.form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned()
            return HttpResponseRedirect('/resource/%s/%d' % (new_item.item_type.lower(), new_item.pk))
        else:
            template = loader.get_template('item/edit.html')
            self.context['item'] = self.item
            self.context['itemrev'] = self.itemrev
            self.context['form'] = form
            self.context['query_string'] = self.request.META['QUERY_STRING']
            model_names = [model.__name__ for model in resource_name_dict.itervalues() if issubclass(model, type(self.item))]
            model_names.sort()
            self.context['model_names'] = model_names
            return HttpResponse(template.render(self.context))

    def entry_delete(self):
        #TODO this doesn't really work
        cms.models.Item.objects.get(pk=self.item.pk).delete()
        return HttpResponseRedirect('/resource/%s' % (self.item_type.__name__.lower(),))


class GroupViewer(ItemViewer):

    def collection_create(self):
        #TODO if you update an Item into a Group, it doesn't make a Folio
        form = self.form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            folio = cms.models.Folio(description='Group Folio')
            folio.save_versioned()
            new_item.folio = folio
            new_item.save_versioned()
            return HttpResponseRedirect('/resource/%s/%d' % (new_item.item_type.lower(), new_item.pk))
        else:
            template = loader.get_template('item/new.html')
            self.context['form'] = form
            return HttpResponse(template.render(self.context))

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        folio = self.item.folio.downcast()
        folio_viewer_class = get_viewer_class_for_item_type(type(folio))
        folio_viewer = folio_viewer_class()
        folio_viewer.init_show_from_div(self.request, type(folio), folio, folio.revisions.order_by('-version').get())
        folio_html = folio_viewer.dispatch().content
        template = loader.get_template('group/show.html')
        self.context['item'] = self.item
        self.context['comments'] = comments
        self.context['folio_html'] = folio_html
        return HttpResponse(template.render(self.context))


class ItemSetViewer(ItemViewer):

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        template = loader.get_template('itemset/show.html')
        self.context['item'] = self.item
        self.context['itemrev'] = self.itemrev
        self.context['comments'] = comments
        return HttpResponse(template.render(self.context))


class TextDocumentViewer(ItemViewer):

    def entry_show(self):
        comments = comment_dicts_for_item(self.item)
        template = loader.get_template('textdocument/show.html')
        self.context['item'] = self.item
        self.context['itemrev'] = self.itemrev
        self.context['comments'] = comments
        return HttpResponse(template.render(self.context))

    def collection_getregions(self):
        data = '[["refbase_123::14", "refbase_123::18"]]'
        return HttpResponse(data)


class DynamicPageViewer(ItemViewer):

    def entry_run(self):
        code = self.itemrev.code
        template = loader.get_template_from_string(code)
        return HttpResponse(template.render(self.context))


