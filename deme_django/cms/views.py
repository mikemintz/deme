#TODO completely clean up code

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.template import loader
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils import simplejson
from django.utils.text import capfirst
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist
import django.contrib.syndication.feeds
import django.contrib.syndication.views
from django.views.decorators.http import require_POST
import re
from urlparse import urljoin
from cms.models import *
from cms.forms import *
from cms.base_viewer import DemePermissionDenied, Viewer
from cms.permissions import all_possible_item_abilities, all_possible_item_and_global_abilities

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
        self.context['search_query'] = self.request.GET.get('q', '')
        self.context['item_type_lower'] = self.accepted_item_type.__name__.lower()
        self.context['item_create_ability'] = "create %s" % (self.accepted_item_type.__name__)
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
                visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
                recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
            items = items.filter(pk__in=collection.all_contained_collection_members(recursive_filter).values('pk').query)
        for filter_string in self.request.GET.getlist('filter'):
            filter_string = str(filter_string) # Unicode doesn't work here
            self.context['filter_string'] = filter_string
            parts = filter_string.split('.')
            target_pk = parts.pop()
            fields = []
            item_types = []
            cur_item_type = self.accepted_item_type
            for part in parts:
                field, model, direct, m2m = cur_item_type._meta.get_field_by_name(part)
                if model is None:
                    model = cur_item_type
                fields.append(field)
                item_types.append(model)
                if isinstance(field, models.ForeignKey):
                    cur_item_type = field.rel.to
                elif isinstance(field, models.related.RelatedObject):
                    cur_item_type = field.model
                else:
                    raise Exception("Cannot filter on field %s.%s (not a related field)" % (cur_item_type.__name__, field.name))
                if not issubclass(cur_item_type, Item):
                    raise Exception("Cannot filter on field %s.%s (non item-type model)" % (cur_item_type.__name__, field.name))

            def filter_by_filter(queryset, fields, item_types):
                if not fields:
                    return queryset.filter(pk=target_pk)
                field = fields[0]
                item_type = item_types[0]
                if isinstance(field, models.ForeignKey):
                    next_item_type = field.rel.to
                elif isinstance(field, models.related.RelatedObject):
                    next_item_type = field.model
                next_queryset = filter_by_filter(next_item_type.objects, fields[1:], item_types[1:])
                if isinstance(field, models.ForeignKey):
                    query_dict = {field.name + '__in': next_queryset}
                    result = queryset.filter(**query_dict)
                    ability = 'view %s.%s' % (item_type.__name__, field.name)
                    result = self.permission_cache.filter_items(ability, result)
                elif isinstance(field, models.related.RelatedObject):
                    if not isinstance(field.field, models.OneToOneField):
                        ability = 'view %s.%s' % (next_item_type.__name__, field.field.name)
                        next_queryset = self.permission_cache.filter_items(ability, next_queryset)
                    query_dict = {'pk__in': next_queryset.values(field.field.name).query}
                    result = queryset.filter(**query_dict)
                else:
                    assert False
                result = result.filter(active=True)
                return result
            items = filter_by_filter(items, fields, item_types)
        listable_items = self.permission_cache.filter_items('view Item.name', items)
        for ability in self.request.GET.getlist('ability'):
            listable_items = self.permission_cache.filter_items(ability, listable_items)
        listable_items = listable_items.filter(active=active)
        listable_items = listable_items.order_by('id')
        n_listable_items = listable_items.count()
        items = [item for item in listable_items.all()[offset:offset+limit]]
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name_plural': x._meta.verbose_name_plural, 'item_type': x} for x in all_item_types() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['item_types'] = item_types
        self.context['items'] = items
        self.context['n_listable_items'] = n_listable_items
        self.context['offset'] = offset
        self.context['limit'] = limit
        self.context['list_start_i'] = offset + 1
        self.context['list_end_i'] = min(offset + limit, n_listable_items)
        self.context['active'] = active
        self.context['collection'] = collection
        self.context['all_collections'] = self.permission_cache.filter_items('view Item.name', Collection.objects.filter(active=True)).order_by('name')

    def type_list_html(self):
        self.context['action_title'] = ''
        self._type_list_helper()
        template = loader.get_template('item/list.html')
        return HttpResponse(template.render(self.context))

    def type_list_json(self):
        self._type_list_helper()
        data = [[item.name, item.pk] for item in self.context['items']]
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def type_list_rss(self):
        self._type_list_helper()
        item_list = self.context['items'] #TODO probably not useful to get this ordering
        #TODO permissions to view Item.name/Item.description
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

    def type_new_html(self, form=None):
        self.context['action_title'] = u'New %s' % self.accepted_item_type._meta.verbose_name
        if not self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__):
            form = None
        else:
            if form is None:
                form_initial = self.get_populated_field_dict()
                form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
                form = form_class(initial=form_initial)
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        self.context['add_to_collection'] = self.request.GET.get('add_to_collection')
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name': x._meta.verbose_name, 'item_type': x} for x in all_item_types() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['item_types'] = item_types
        return HttpResponse(template.render(self.context))

    @require_POST
    def type_create_html(self):
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=form.cleaned_data['action_summary'], initial_permissions=permissions)
            if 'add_to_collection' in self.request.GET:
                new_membership = Membership(item=new_item, collection=Collection.objects.get(pk=self.request.GET['add_to_collection']))
                membership_permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
                new_membership.save_versioned(action_agent=self.cur_agent, initial_permissions=membership_permissions) 
            redirect = self.request.GET.get('redirect', new_item.get_absolute_url())
            return HttpResponseRedirect(redirect)
        else:
            return self.type_new_html(form)

    def type_recentchanges_html(self):
        self.context['action_title'] = 'Recent Changes'
        template = loader.get_template('item/recentchanges.html')    
        viewable_items = self.permission_cache.filter_items('view Item.action_notices', Item.objects)
        viewable_action_notices = ActionNotice.objects.filter(action_item__in=viewable_items.values("pk").query).order_by('-action_time')
        
        action_notice_pk_to_object_map = {}
        for action_notice_subclass in [DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, EditActionNotice, CreateActionNotice]:
            specific_action_notices = action_notice_subclass.objects.filter(pk__in=viewable_action_notices.values('pk').query)
            for action_notice in specific_action_notices:
                action_notice_pk_to_object_map[action_notice.pk] = action_notice

        action_notice_details = []
        for action_notice in viewable_action_notices:
            if action_notice.pk in action_notice_pk_to_object_map:
                specific_action_notice = action_notice_pk_to_object_map[action_notice.pk]           
                details = {}
                details["type"] = type(specific_action_notice).__name__
                details["action_notice"] = action_notice
                action_notice_details.append(details)

        paginator = Paginator(action_notice_details, 50)

        try:
            page = int(self.request.GET.get('page', '1'))
        except ValueError:
            page = 1

        try: 
            newPage = paginator.page(page)
        except (EmptyPage, InvalidPage):
            newPage = paginator.page(paginator.num_pages)

        page_range = paginator.page_range
        for possible_page in page_range:
            if (possible_page > page + 10):
                page_range.remove(possible_page)
            if (possible_page < page - 10):
                page_range.remove(possible_page)

        self.context['action_notices'] = newPage
        self.context['count'] = paginator.count
        self.context['page_range'] = page_range
           
        return HttpResponse(template.render(self.context))

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('item/show.html')
        return HttpResponse(template.render(self.context))

    def item_show_rss(self):
        from cms.templatetags.item_tags import get_viewable_name
        viewer = self
        self.require_ability('view Item.action_notices', self.item)
        action_notices = ActionNotice.objects.filter(Q(action_item=self.item) | Q(action_agent=self.item))
        action_notices = action_notices.order_by('-action_time')
        action_notices = action_notices[:50]
        action_notice_pk_to_object_map = {}
        for action_notice_subclass in [RelationActionNotice, DeactivateActionNotice, ReactivateActionNotice, DestroyActionNotice, CreateActionNotice, EditActionNotice]:
            specific_action_notices = action_notice_subclass.objects.filter(pk__in=action_notices.values('pk').query)
            if action_notice_subclass == RelationActionNotice:
                self.permission_cache.filter_items('view Item.name', Item.objects.filter(Q(pk__in=specific_action_notices.values('from_item').query)))
            for action_notice in specific_action_notices:
                action_notice_pk_to_object_map[action_notice.pk] = action_notice
        self.permission_cache.filter_items('view Item.name', Item.objects.filter(Q(pk__in=action_notices.values('action_item').query) | Q(pk__in=action_notices.values('action_agent').query)))
        class ItemShowFeed(django.contrib.syndication.feeds.Feed):
            title = get_viewable_name(viewer.context, viewer.item)
            description = viewer.item.description if viewer.cur_agent_can('view Item.description', viewer.item) else ''
            link = reverse('item_url', kwargs={'viewer': viewer.viewer_name, 'action': 'show', 'noun': viewer.item.pk, 'format': 'rss'})
            def items(self):
                result = []
                for action_notice in action_notices:
                    action_notice = action_notice_pk_to_object_map[action_notice.pk]
                    if isinstance(action_notice, RelationActionNotice):
                        if not viewer.cur_agent_can('view %s.%s' % (action_notice.from_field_model, action_notice.from_field_name), action_notice.from_item):
                            continue
                    item = {}
                    item['action_time'] = action_notice.action_time
                    item['action_agent_name'] = get_viewable_name(viewer.context, action_notice.action_agent)
                    item['action_agent_link'] = action_notice.action_agent.get_absolute_url()
                    item['action_item_name'] = get_viewable_name(viewer.context, action_notice.action_item)
                    item['action_summary'] = action_notice.action_summary
                    if isinstance(action_notice, RelationActionNotice):
                        item['from_item_name'] = get_viewable_name(viewer.context, action_notice.from_item)
                        item['from_field_name'] = action_notice.from_field_name
                        item['relation_added'] = action_notice.relation_added
                        item['link'] = action_notice.from_item.get_absolute_url()
                    else:
                        item['link'] = action_notice.action_item.get_absolute_url()
                    item['action_notice_type'] = type(action_notice).__name__
                    result.append(item)
                return result
            def item_link(self, item):
                return item['link']
            def item_pubdate(self, item):
                return item['action_time']
        return django.contrib.syndication.views.feed(self.request, 'item_show', {'item_show': ItemShowFeed})

    def item_copy_html(self):
        self.context['action_title'] = 'Copy'
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
        fields_to_copy = []
        for field_name in form_class.base_fields:
            try:
                model = self.item._meta.get_field_by_name(field_name)[1]
            except FieldDoesNotExist:
                # For things like action_summary
                continue
            if model is None:
                model = type(self.item)
            if self.cur_agent_can('view %s.%s' % (model.__name__, field_name), self.item):
                fields_to_copy.append(field_name)
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

    def item_edit_html(self, form=None):
        self.context['action_title'] = 'Edit'
        abilities_for_item = self.permission_cache.item_abilities(self.item)
        self.require_ability('edit ', self.item, wildcard_suffix=True)
        if form is None:
            form_initial = self.get_populated_field_dict()
            fields_can_edit = [x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('edit ')]
            form_class = self.get_form_class_for_item_type(self.accepted_item_type, False, fields_can_edit)
            form = form_class(instance=self.item, initial=form_initial)
            fields_can_view = set([x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('view ')])
            fields_can_view.add('action_summary')
            initial_fields_set = set(form.initial.iterkeys())
            fields_must_blank = initial_fields_set - fields_can_view
            for field_name in fields_must_blank:
                del form.initial[field_name]
        template = loader.get_template('item/edit.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    @require_POST
    def item_update_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.item)
        self.require_ability('edit ', self.item, wildcard_suffix=True)
        new_item = self.item
        fields_can_edit = [x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('edit ')]
        form_class = self.get_form_class_for_item_type(self.accepted_item_type, False, fields_can_edit)
        form = form_class(self.request.POST, self.request.FILES, instance=new_item)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=form.cleaned_data['action_summary'])
            return HttpResponseRedirect(reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            return self.item_edit_html(form)

    @require_POST
    def item_deactivate_html(self):
        if not self.item.can_be_deleted():
            return self.render_error('Cannot delete', "This item may not be deleted")
        self.require_ability('delete', self.item)
        self.item.deactivate(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    @require_POST
    def item_reactivate_html(self):
        if not self.item.can_be_deleted():
            return self.render_error('Cannot delete', "This item may not be deleted")
        self.require_ability('delete', self.item)
        self.item.reactivate(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    @require_POST
    def item_destroy_html(self):
        if not self.item.can_be_deleted():
            return self.render_error('Cannot delete', "This item may not be deleted")
        self.require_ability('delete', self.item)
        self.item.destroy(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'))
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def _get_permissions_from_post_data(self, item_type, target_level):
        if target_level == 'one':
            possible_abilities = all_possible_item_abilities(item_type)
        else:
            possible_abilities = all_possible_item_and_global_abilities()
        permission_data = {}
        for key, value in self.request.POST.iteritems():
            if key.startswith('newpermission'):
                permission_counter, name = key.split('_', 1)
                permission_datum = permission_data.setdefault(permission_counter, {})
                permission_datum[name] = value
        result = []
        if target_level == 'all':
            # Make sure admin keeps do_anything ability
            result.append(OneToAllPermission(source_id=1, ability='do_anything', is_allowed=True))
        for permission_datum in permission_data.itervalues():
            ability = permission_datum['ability']
            if ability not in possible_abilities:
                return self.render_error('Form Error', "Invalid ability")
            is_allowed = (permission_datum.get('is_allowed') == 'on')
            permission_type = permission_datum['permission_type']
            agent_or_collection_id = permission_datum['agent_or_collection_id']
            if permission_type == 'agent':
                agent = Agent.objects.get(pk=agent_or_collection_id)
                if target_level == 'one':
                    permission = OneToOnePermission(source=agent)
                elif target_level == 'some':
                    permission = OneToSomePermission(source=agent)
                elif target_level == 'all':
                    permission = OneToAllPermission(source=agent)
                else:
                    assert False
            elif permission_type == 'collection':
                collection = Collection.objects.get(pk=agent_or_collection_id)
                if target_level == 'one':
                    permission = SomeToOnePermission(source=collection)
                elif target_level == 'some':
                    permission = SomeToSomePermission(source=collection)
                elif target_level == 'all':
                    permission = SomeToAllPermission(source=collection)
                else:
                    assert False
            elif permission_type == 'everyone':
                if target_level == 'one':
                    permission = AllToOnePermission()
                elif target_level == 'some':
                    permission = AllToSomePermission()
                elif target_level == 'all':
                    permission = AllToAllPermission()
                else:
                    assert False
            else:
                return self.render_error('Form Error', "Invalid permission_type")
            permission.ability = ability
            permission.is_allowed = is_allowed
            # Make sure we don't add duplicates
            permission_key_fn = lambda x: (type(x), x.ability, getattr(x, 'source', None))
            if not any(permission_key_fn(x) == permission_key_fn(permission) for x in result):
                result.append(permission)
        return result

    @require_POST
    def item_updateprivacy_html(self):
        self.require_ability('modify_privacy_settings', self.item)
        new_permissions = self._get_permissions_from_post_data(self.item.actual_item_type(), 'one')
        for permission_class in [OneToOnePermission, SomeToOnePermission, AllToOnePermission]:
            permission_class.objects.filter(target=self.item, ability__startswith="view ").delete()
        for permission in new_permissions:
            permission.target = self.item
            permission.save()
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk, 'action': 'privacy'}))
        return HttpResponseRedirect(redirect)

    @require_POST
    def item_updateitempermissions_html(self):
        self.require_ability('do_anything', self.item)
        new_permissions = self._get_permissions_from_post_data(self.item.actual_item_type(), 'one')
        for permission_class in [OneToOnePermission, SomeToOnePermission, AllToOnePermission]:
            permission_class.objects.filter(target=self.item).delete()
        for permission in new_permissions:
            permission.target = self.item
            permission.save()
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk, 'action': 'itempermissions'}))
        return HttpResponseRedirect(redirect)

    @require_POST
    def item_updatecollectionpermissions_html(self):
        self.require_ability('do_anything', self.item)
        new_permissions = self._get_permissions_from_post_data(self.item.actual_item_type(), 'some')
        for permission_class in [OneToSomePermission, SomeToSomePermission, AllToSomePermission]:
            permission_class.objects.filter(target=self.item).delete()
        for permission in new_permissions:
            permission.target = self.item
            permission.save()
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk, 'action': 'collectionpermissions'}))
        return HttpResponseRedirect(redirect)

    @require_POST
    def type_updateglobalpermissions_html(self):
        self.require_global_ability('do_anything')
        new_permissions = self._get_permissions_from_post_data(None, 'all')
        for permission_class in [OneToAllPermission, SomeToAllPermission, AllToAllPermission]:
            permission_class.objects.filter().delete()
        for permission in new_permissions:
            permission.save()
        redirect = self.request.GET.get('redirect', reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'globalpermissions'}))
        return HttpResponseRedirect(redirect)

    def item_privacy_html(self):
        self.context['action_title'] = 'Privacy settings'
        self.require_ability('modify_privacy_settings', self.item)
        template = loader.get_template('item/privacy.html')
        return HttpResponse(template.render(self.context))

    def item_itempermissions_html(self):
        self.context['action_title'] = 'Item permissions'
        self.require_ability('view_permissions', self.item)
        template = loader.get_template('item/itempermissions.html')
        return HttpResponse(template.render(self.context))

    def item_collectionpermissions_html(self):
        self.context['action_title'] = 'Collection permissions'
        self.require_ability('view_permissions', self.item)
        template = loader.get_template('item/collectionpermissions.html')
        return HttpResponse(template.render(self.context))

    def type_globalpermissions_html(self):
        self.context['action_title'] = 'Global permissions'
        self.require_global_ability('do_anything')
        template = loader.get_template('item/globalpermissions.html')
        return HttpResponse(template.render(self.context))

    def type_admin_html(self):
        self.context['action_title'] = 'Admin'
        self.require_global_ability('do_anything')
        template = loader.get_template('item/admin.html')
        return HttpResponse(template.render(self.context))

    def type_permissionshelp_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('item/permissionshelp.html')
        return HttpResponse(template.render(self.context))


class WebpageViewer(ItemViewer):
    accepted_item_type = Webpage
    viewer_name = 'webpage'

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['url'] = self.item.url
        template = loader.get_template('webpage/show.html')
        return HttpResponse(template.render(self.context))


class AgentViewer(ItemViewer):
    accepted_item_type = Agent
    viewer_name = 'agent'


class AnonymousAgentViewer(AgentViewer):
    accepted_item_type = AnonymousAgent
    viewer_name = 'anonymousagent'


class GroupAgentViewer(AgentViewer):
    accepted_item_type = GroupAgent
    viewer_name = 'groupagent'


class AuthenticationMethodViewer(ItemViewer):
    accepted_item_type = AuthenticationMethod
    viewer_name = 'authenticationmethod'

    def type_login_html(self):
        self.context['action_title'] = 'Login'
        if self.request.method == 'GET':
            login_as_agents = Agent.objects.filter(active=True).order_by('name')
            login_as_agents = self.permission_cache.filter_items('login_as', login_as_agents)
            self.permission_cache.filter_items('view Item.name', login_as_agents)
            template = loader.get_template('authenticationmethod/login.html')
            self.context['redirect'] = self.request.GET.get('redirect', '')
            self.context['login_as_agents'] = login_as_agents
            return HttpResponse(template.render(self.context))
        else:
            # The user just submitted a login form, so we try to authenticate.
            redirect = self.request.GET.get('redirect', '')
            for key in self.request.POST.iterkeys():
                if key.startswith('login_as_'):
                    new_agent_id = key.split('login_as_')[1]
                    try:
                        new_agent = Agent.objects.get(pk=new_agent_id)
                    except ObjectDoesNotExist:
                        # There is no Agent with the specified id.
                        return self.render_error("Authentication Failed", "There was a problem with your login form")
                    if not new_agent.active:
                        # The specified agent is inactive.
                        return self.render_error("Authentication Failed", "There was a problem with your login form")
                    self.require_ability('login_as', new_agent)
                    self.request.session['cur_agent_id'] = new_agent.pk
                    full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
                    return HttpResponseRedirect(full_redirect)
   
    @require_POST
    def type_logout_html(self):
        if 'cur_agent_id' in self.request.session:
            del self.request.session['cur_agent_id']
        redirect = self.request.GET.get('redirect', '')
        full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
        return HttpResponseRedirect(full_redirect)

    def type_loggedinorout_html(self):
        if self.cur_agent.is_anonymous():
            self.context['action_title'] = 'Logged out'
        else:
            self.context['action_title'] = 'Logged in'
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('authenticationmethod/loggedinorout.html')
        return HttpResponse(template.render(self.context))
    
    def type_loginmenuitem_html(self):
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('authenticationmethod/loginmenuitem.html')
        return HttpResponse(template.render(self.context))
 

class PersonViewer(AgentViewer):
    accepted_item_type = Person
    viewer_name = 'person'


class ContactMethodViewer(ItemViewer):
    accepted_item_type = ContactMethod
    viewer_name = 'contactmethod'


class EmailContactMethodViewer(ContactMethodViewer):
    accepted_item_type = EmailContactMethod
    viewer_name = 'emailcontactmethod'


class PhoneContactMethodViewer(ContactMethodViewer):
    accepted_item_type = PhoneContactMethod
    viewer_name = 'phonecontactmethod'


class FaxContactMethodViewer(ContactMethodViewer):
    accepted_item_type = FaxContactMethod
    viewer_name = 'faxcontactmethod'


class WebsiteContactMethodViewer(ContactMethodViewer):
    accepted_item_type = WebsiteContactMethod
    viewer_name = 'websitecontactmethod'


class AIMContactMethodViewer(ContactMethodViewer):
    accepted_item_type = AIMContactMethod
    viewer_name = 'aimcontactmethod'


class AddressContactMethodViewer(ContactMethodViewer):
    accepted_item_type = AddressContactMethod
    viewer_name = 'addresscontactmethod'


class SubscriptionViewer(ItemViewer):
    accepted_item_type = Subscription
    viewer_name = 'subscription'


class CollectionViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'collection'

    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        template = loader.get_template('collection/show.html')
        return HttpResponse(template.render(self.context))

    def item_addmember_html(self):
        #TODO use a form
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error('Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('add_self', self.item))):
            raise DemePermissionDenied('modify_membership', None)
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if not membership.active:
                membership.reactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            membership = Membership(collection=self.item, item=member)
            permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
            membership.save_versioned(action_agent=self.cur_agent, action_summary=self.request.POST.get('action_summary'), initial_permissions=permissions)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


    def item_removemember_html(self):
        #TODO use a form
        try:
            member = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error('Invalid URL', "You must specify the member you are adding")
        if not (self.cur_agent_can('modify_membership', self.item) or (member.pk == self.cur_agent.pk and self.cur_agent_can('remove_self', self.item))):
            raise DemePermissionDenied('modify_membership', None)
        try:
            membership = Membership.objects.get(collection=self.item, item=member)
            if membership.active:
                membership.deactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            pass
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


class GroupViewer(CollectionViewer):
    accepted_item_type = Group
    viewer_name = 'group'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        try:
            folio = self.item.folios.get()
            if not self.permission_cache.agent_can('view Folio.group', folio):
                folio = None
        except:
            folio = None
        self.context['folio'] = folio
        template = loader.get_template('group/show.html')
        return HttpResponse(template.render(self.context))


class FolioViewer(CollectionViewer):
    accepted_item_type = Folio
    viewer_name = 'folio'


class MembershipViewer(ItemViewer):
    accepted_item_type = Membership
    viewer_name = 'membership'

    def type_collectioncreate_html(self):
        item_pk = self.request.POST.get('item')
        if item_pk == '':
            return self.render_error('Invalid Membership', "You must specify which item to add to the collection")
        
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        item = Item.objects.get(pk=item_pk)
        collection = Collection.objects.get(pk=self.request.POST['collection'])

        new_member = Membership(collection=collection, item=item) 
        if self.request.POST.get('permissionenabled', '') == 'on':
            new_member.permission_enabled = True
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_member.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))
        
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_member.pk}))
        return HttpResponseRedirect(redirect)


class DocumentViewer(ItemViewer):
    accepted_item_type = Document
    viewer_name = 'document'


class TextDocumentViewer(DocumentViewer):
    accepted_item_type = TextDocument
    viewer_name = 'textdocument'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('textdocument/show.html')
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    def item_edit_html(self, form=None):
        self.context['action_title'] = 'Edit'
        abilities_for_item = self.permission_cache.item_abilities(self.item)
        self.require_ability('edit ', self.item, wildcard_suffix=True)

        transclusions = Transclusion.objects.filter(from_item=self.item, from_item_version_number=self.item.version_number).order_by('-from_item_index')
        body_as_list = list(self.item.body)
        for transclusion in transclusions:
            if issubclass(self.accepted_item_type, HtmlDocument):
                transclusion_text = '<img id="transclusion_%s" src="%s" title="Item %s" style="margin: 0 2px 0 2px; background: #ddd; border: 1px dotted #777; height: 10px; width: 10px;"/>' % (transclusion.to_item_id, urljoin(settings.MEDIA_URL, 'spacer.gif'), transclusion.to_item_id)
            else:
                transclusion_text = '<deme_transclusion id="%s"/>' % transclusion.to_item_id
            i = transclusion.from_item_index
            body_as_list[i:i] = transclusion_text
        self.item.body = ''.join(body_as_list)

        if form is None:
            form_initial = self.get_populated_field_dict()
            fields_can_edit = [x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('edit ')]
            form_class = self.get_form_class_for_item_type(self.accepted_item_type, False, fields_can_edit)
            form = form_class(instance=self.item, initial=form_initial)
            fields_can_view = set([x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('view ')])
            fields_can_view.add('action_summary')
            initial_fields_set = set(form.initial.iterkeys())
            fields_must_blank = initial_fields_set - fields_can_view
            for field_name in fields_must_blank:
                del form.initial[field_name]
        template = loader.get_template('item/edit.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    @require_POST
    def item_update_html(self):
        abilities_for_item = self.permission_cache.item_abilities(self.item)
        self.require_ability('edit ', self.item, wildcard_suffix=True)
        new_item = self.item
        fields_can_edit = [x.split(' ')[1].split('.')[1] for x in abilities_for_item if x.startswith('edit ')]
        form_class = self.get_form_class_for_item_type(self.accepted_item_type, False, fields_can_edit)
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
            
            new_item.save_versioned(action_agent=self.cur_agent, action_summary=form.cleaned_data['action_summary'])

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
                    transclusion.save_versioned(action_agent=self.cur_agent, action_summary=form.cleaned_data['action_summary'])

            return HttpResponseRedirect(reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
        else:
            return self.item_edit_html(form)


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    accepted_item_type = DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def item_render_html(self):
        self.context['action_title'] = ''
        template = self.construct_template(self.item)
        return HttpResponse(template.render(self.context))


class HtmlDocumentViewer(TextDocumentViewer):
    accepted_item_type = HtmlDocument
    viewer_name = 'htmldocument'


class FileDocumentViewer(DocumentViewer):
    accepted_item_type = FileDocument
    viewer_name = 'filedocument'


class TransclusionViewer(ItemViewer):
    accepted_item_type = Transclusion
    viewer_name = 'transclusion'


class CommentViewer(ItemViewer):
    accepted_item_type = Comment
    viewer_name = 'comment'


class TextCommentViewer(TextDocumentViewer, CommentViewer):
    accepted_item_type = TextComment
    viewer_name = 'textcomment'

    def type_new_html(self, form=None):
        self.context['action_title'] = u'New %s' % self.accepted_item_type._meta.verbose_name
        try:
            item = Item.objects.get(pk=self.request.REQUEST.get('populate_item'))
        except:
            return self.render_error('Invalid URL', "You must specify the item you are commenting on")
        if not self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__):
            form = None
        else:
            if form is None:
                form_initial = self.get_populated_field_dict()
                form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
                form = form_class(initial=form_initial)
                if issubclass(item.actual_item_type(), Comment):
                    comment_name = item.display_name()
                    if not comment_name.lower().startswith('re: '):
                        comment_name = 'Re: %s' % comment_name
                    form.fields['name'].initial = comment_name
                    form.fields['name'].widget = JustTextNoInputWidget()
                    form.fields['name'].help_text = None
        template = loader.get_template('item/new.html')
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        self.context['add_to_collection'] = self.request.GET.get('add_to_collection')
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name': x._meta.verbose_name, 'item_type': x} for x in all_item_types() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['item_types'] = item_types
        return HttpResponse(template.render(self.context))

    @require_POST
    def type_create_html(self):
        #TODO do we need to allow action_summary here?
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        try:
            item = Item.objects.get(pk=self.request.POST.get('item'))
        except:
            return self.render_error('Invalid URL', "You must specify the item you are commenting on")
        self.require_ability('comment_on', item)
        form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
        form = form_class(self.request.POST, self.request.FILES)
        if form.is_valid():
            #TODO use transactions to make the Transclusion save at the same time as the Comment
            item_index = form.cleaned_data['item_index']
            comment = form.save(commit=False)
            item = comment.item.downcast()
            if not comment.name:
                #TODO permissions to view Item.name: technically you could figure out the name of an item by commenting on it here
                comment.name = item.display_name()
                if not comment.name.lower().startswith('re: '):
                    comment.name = 'Re: %s' % comment.name
            permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
            comment.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
            if isinstance(item, TextDocument) and item_index is not None and self.permission_cache.agent_can('add_transclusion', item):
                transclusion = Transclusion(from_item=item, from_item_version_number=comment.item_version_number, from_item_index=item_index, to_item=comment)
                #TODO seems like there should be a way to set custom permissions on the transclusions
                permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
                transclusion.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)

            if 'add_to_collection' in self.request.GET:
                new_membership = Membership(item=comment, collection=Collection.objects.get(pk=self.request.GET['add_to_collection']))
                new_membership.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions) 

            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': comment.pk}))
            return HttpResponseRedirect(redirect)
        else:
            return self.type_new_html(form)

    @require_POST
    def type_accordioncreate_html(self):
        value = self.request.POST["sq_1"]
        response, value = value.strip().lower(), ''
		
        if not hashlib.sha1(str(response)).hexdigest() == self.request.POST["sq_0"]:
            return self.render_error('Invalid Answer', 'Add up the numbers correctly to prove you are not a spammer')
        new_body = self.request.POST.get('body')
        if new_body == '':
            return self.render_error('Invalid Comment', "You must enter in a body for your comment")
        title = self.request.POST.get('title')
        if title == '':
            return self.render_error('Invalid Comment', "You must enter in a title for your comment")
        
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        item = Item.objects.get(pk=self.request.POST.get('item'))
        self.require_ability('comment_on', item)

        new_comment = TextComment(body=new_body, item=item, item_version_number=self.request.POST.get('item_version_number')) 
        new_comment.name = title
        if self.request.POST.get('new_from_contact_method') != '':
            new_comment.from_contact_method = ContactMethod.objects.get(pk=self.request.POST.get('new_from_contact_method'))
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_comment.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_comment.pk}))
        return HttpResponseRedirect(redirect)

class ExcerptViewer(ItemViewer):
    accepted_item_type = Excerpt
    viewer_name = 'excerpt'


class TextDocumentExcerptViewer(ExcerptViewer, TextDocumentViewer):
    accepted_item_type = TextDocumentExcerpt
    viewer_name = 'textdocumentexcerpt'

    def type_createmultiexcerpt_html(self):
        #TODO get action_summary
        #TODO there should be a way to specify permissions on a multi-excerpts as soon as you create them
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        self.require_global_ability('create Collection')
        excerpts = []
        for excerpt_form_datum in self.request.POST.getlist('excerpt'):
            try:
                text_document_id, text_document_version_number, start_index, length = excerpt_form_datum.split(' ')
                start_index = int(start_index)
                length = int(length)
            except ValueError:
                return self.render_error('Invalid Form Data', "Could not parse the excerpt data in the form")
            try:
                text_document = TextDocument.objects.get(pk=text_document_id)
                text_document.copy_fields_from_version(text_document_version_number)
            except:
                return self.render_error('Invalid Form Data', "Could not find the specified TextDocument")
            self.require_ability('view TextDocument.body', text_document)
            body = text_document.body[start_index:start_index+length]
            excerpt = TextDocumentExcerpt(body=body, text_document=text_document, text_document_version_number=text_document_version_number, start_index=start_index, length=length)
            excerpts.append(excerpt)
        if not excerpts:
            return self.render_error('Invalid Form Data', "You must submit at least one excerpt")
        collection = Collection()
        permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
        collection.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
        for excerpt in excerpts:
            permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
            excerpt.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
            permissions = [OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)]
            Membership(item=excerpt, collection=collection).save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': 'collection', 'noun': collection.pk}))
        return HttpResponseRedirect(redirect)


class ViewerRequestViewer(ItemViewer):
    accepted_item_type = ViewerRequest
    viewer_name = 'viewerrequest'

    def item_show_html(self, form=None):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        site, custom_urls = self.item.calculate_full_path()
        self.context['site'] = site
        self.context['custom_urls'] = custom_urls
        self.context['child_urls'] = self.item.child_urls.filter(active=True)
        template = loader.get_template('viewerrequest/show.html')
        return HttpResponse(template.render(self.context))


class SiteViewer(ViewerRequestViewer):
    accepted_item_type = Site
    viewer_name = 'site'


class CustomUrlViewer(ViewerRequestViewer):
    accepted_item_type = CustomUrl
    viewer_name = 'customurl'


class DemeSettingViewer(ItemViewer):
    accepted_item_type = DemeSetting
    viewer_name = 'demesetting'

    def type_modify_html(self):
        self.context['action_title'] = 'Modify settings'
        self.require_global_ability('do_anything')
        self.context['deme_settings'] = DemeSetting.objects.filter(active=True).order_by('key')
        template = loader.get_template('demesetting/modify.html')
        return HttpResponse(template.render(self.context))

    def type_addsetting_html(self):
        self.require_global_ability('do_anything')
        key = self.request.POST.get('key')
        value = self.request.POST.get('value')
        DemeSetting.set(key, value, self.cur_agent)
        redirect = self.request.GET.get('redirect', reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'modify'}))
        return HttpResponseRedirect(redirect)

