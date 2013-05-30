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
from django.utils.timesince import timesince
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist
import django.contrib.syndication.feeds
import django.contrib.syndication.views
from django.views.decorators.http import require_POST
import re
import math
import datetime
from urlparse import urljoin
from cms.models import *
from cms.forms import *
from cms.base_viewer import DemePermissionDenied, Viewer
from cms.permissions import all_possible_item_abilities, all_possible_item_and_global_abilities

class ItemViewer(Viewer):
    accepted_item_type = Item
    viewer_name = 'item'

    def default_metadata_menu_option(self):
        return 'item_details'

    def _type_list_helper(self, offset=None, limit=None, q=None):
        if self.request.GET.get('collection'):
            collection = Item.objects.get(pk=self.request.GET.get('collection')).downcast()
        else:
            collection = None
        offset = offset or int(self.request.GET.get('offset', 0))
        limit = limit or int(self.request.GET.get('limit', 100))
        active = self.request.GET.get('active', '1') == '1'
        self.context['search_query'] = q or self.request.GET.get('q', '')
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
        self.context['metabar_contents'] = u'List %s' % self.accepted_item_type._meta.verbose_name_plural
        self.context['item_type_lower'] = self.accepted_item_type.__name__.lower()
        self.context['item_create_ability'] = "create %s" % (self.accepted_item_type.__name__)
        self.context['search_query'] = self.request.GET.get('q', '')
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name_plural': x._meta.verbose_name_plural, 'item_type': x} for x in all_item_types() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['item_types'] = item_types
        if self.request.GET.get('collection'):
            collection = Item.objects.get(pk=self.request.GET.get('collection')).downcast()
        else:
            collection = None
        self.context['collection'] = collection
        self.context['all_collections'] = self.permission_cache.filter_items('view Item.name', Collection.objects.filter(active=True)).order_by('name')
        template = loader.get_template('item/list.html')
        return HttpResponse(template.render(self.context))

    def type_list_json(self):
        self._type_list_helper()
        data = [[item.name, item.pk] for item in self.context['items']]
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def type_grid_json(self):
        from cms.templatetags.item_tags import icon_url
        from django.utils.html import escape

        field_names = self.request.GET['fields'].split(',')
        n_rows = int(self.request.GET['rows'])
        page = int(self.request.GET['page'])
        search_field = self.request.GET.get('searchField', '')
        search_oper = self.request.GET.get('searchOper', '')
        search_string = self.request.GET.get('searchString', '')
        sort_field = self.request.GET.get('sidx', '')
        sort_ascending = self.request.GET['sord'] == 'asc'
        if self.request.GET.get('collection'):
            collection = Item.objects.get(pk=self.request.GET.get('collection')).downcast()
        else:
            collection = None

        offset = (page - 1) * n_rows
        active = True

        # Get the basic list of items
        items = self.accepted_item_type.objects
        items = items.filter(active=active)
        for ability in self.request.GET.getlist('ability'):
            items = self.permission_cache.filter_items(ability, items)
        # Filter by the search
        if search_field:
            field = self.accepted_item_type._meta.get_field_by_name(search_field)[0]
            # Make sure we can see the field
            ability = 'view %s.%s' % (field.model.__name__, field.name)
            items = self.permission_cache.filter_items(ability, items)
            # Generate the search query on the field
            operation_map = {
                'eq': (True, 'iexact'),
                'ne': (False, 'iexact'),
                'bw': (True, 'istartswith'),
                'bn': (False, 'istartswith'),
                'ew': (True, 'iendswith'),
                'en': (False, 'iendswith'),
                'cn': (True, 'icontains'),
                'nc': (False, 'icontains'),
                'nu': (True, 'isnull'),
                'nn': (False, 'isnull'),
                'in': (True, 'in'),#TODO
                'ni': (False, 'in'),#TODO
            }
            django_positive, django_operation = operation_map[search_oper]
            search_key = '%s__%s' % ('name' if isinstance(field, models.ForeignKey) else field.name, django_operation)
            search_value = True if django_operation == 'isnull' else search_string
            search_filter = Q(**{search_key: search_value})
            if not django_positive:
                search_filter = ~search_filter
            if isinstance(field, models.ForeignKey):
                foreign_items = field.rel.to.objects.filter(search_filter)
                foreign_items = self.permission_cache.filter_items('view Item.name', foreign_items)
                items = items.filter(**{field.name + "__in": foreign_items})
            else:
                items = items.filter(search_filter)
        # Filter by the filter parameter
        for filter_string in self.request.GET.getlist('filter'):
            if not filter_string: continue
            filter_string = str(filter_string) # Unicode doesn't work here
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
                    if issubclass(item_type, Item):
                        ability = 'view %s.%s' % (item_type.__name__, field.name)
                        result = self.permission_cache.filter_items(ability, result)
                elif isinstance(field, models.related.RelatedObject):
                    if issubclass(next_item_type, Item) and not isinstance(field.field, models.OneToOneField):
                        ability = 'view %s.%s' % (next_item_type.__name__, field.field.name)
                        next_queryset = self.permission_cache.filter_items(ability, next_queryset)
                    query_dict = {'pk__in': next_queryset.values(field.field.name).query}
                    result = queryset.filter(**query_dict)
                else:
                    assert False
                if issubclass(item_type, Item):
                    result = result.filter(active=True)
                return result
            items = filter_by_filter(items, fields, item_types)
        # Filter by collection
        if isinstance(collection, Collection):
            if self.cur_agent_can_global('do_anything'):
                recursive_filter = None
            else:
                visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
                recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
            items = items.filter(pk__in=collection.all_contained_collection_members(recursive_filter).values('pk').query)
        # Perform the ordering
        if sort_field:
            field = self.accepted_item_type._meta.get_field_by_name(sort_field)[0]
            # Make sure we can see the field
            ability = 'view %s.%s' % (field.model.__name__, field.name)
            items = self.permission_cache.filter_items(ability, items)
            if isinstance(field, models.ForeignKey):
                foreign_items = field.rel.to.objects
                foreign_items = self.permission_cache.filter_items('view Item.name', foreign_items)
                items = items.filter(**{field.name + '__in': foreign_items})
                sort_field = sort_field + "__name"
            items = items.order_by(('' if sort_ascending else '-') + sort_field)
        # Count and limit
        n_items = items.count()
        items = [item for item in items.all()[offset:offset+n_rows]]

        fields = [self.accepted_item_type._meta.get_field_by_name(field_name)[0] for field_name in field_names]

        def item_link(item):
            can_view_name = self.cur_agent_can('view Item.name', item)
            url = "%s?%s" % (item.get_absolute_url(), '&amp;'.join('crumb_filter=' + x for x in self.request.GET.getlist('filter')))
            icon = icon_url(item, 16)
            name = escape(item.display_name(can_view_name))
            return '<a class="imglink" href="%s"><img src="%s" /><span>%s</span></a>' % (url, icon, name)

        rows = []
        for item in items:
            cell = []
            for field in fields:
                if field.name == 'name':
                    cell.append(item_link(item))
                elif self.cur_agent_can('view %s.%s' % (field.model.__name__, field.name), item):
                    if isinstance(field, models.ForeignKey):
                        foreign_item = getattr(item, field.name)
                        if foreign_item:
                            cell.append(item_link(foreign_item))
                        else:
                            cell.append("")
                    else:
                        data = getattr(item, field.name)
                        if isinstance(field, models.FileField):
                            #TODO use .url
                            cell.append('<a href="%s%s">%s</a>' % (escape(settings.MEDIA_URL), escape(data), escape(data)))
                        elif isinstance(field, models.DateTimeField):
                            cell.append('<span title="%s ago">%s</span>' % (timesince(item.created_at), item.created_at.strftime("%Y-%m-%d %H:%M:%S")))
                        else:
                            truncate_length = 50
                            data = unicode(data)
                            truncated_data = data if len(data) < truncate_length else data[:truncate_length] + '...'
                            cell.append(escape(truncated_data))
                else:
                    cell.append("")
            row = {'id': item.pk, 'cell': cell}
            rows.append(row)
        data = {}
        data['page'] = page
        data['total'] = int(math.ceil(float(n_items) / n_rows))
        data['records'] = n_items
        data['rows'] = rows
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

    def type_newother_html(self):
        self.context['action_title'] = u'New'
        self.context['metabar_contents'] = u'Create a new item'
        sorted_item_types = sorted(all_item_types(), key=lambda x: x._meta.verbose_name_plural.lower())
        all_item_types_can_create = [{'item_type': x, 'url': reverse('item_type_url', kwargs={'viewer': x.__name__.lower(), 'action': 'new'})} for x in sorted_item_types if self.cur_agent_can_global('create %s' % x.__name__)]
        self.context['all_item_types_can_create'] = all_item_types_can_create
        template = loader.get_template('item/newother.html')
        return HttpResponse(template.render(self.context))

    def type_new_html(self, form=None):
        self.context['action_title'] = u'New %s' % self.accepted_item_type._meta.verbose_name
        self.context['metabar_contents'] = u'Create a new %s' % self.accepted_item_type._meta.verbose_name
        if not self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__):
            form = None
        else:
            if form is None:
                form_initial = self.get_populated_field_dict(self.accepted_item_type)
                form_class = self.get_form_class_for_item_type(self.accepted_item_type, True)
                form = form_class(initial=form_initial)
        self.context['form'] = form
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        self.context['redirect'] = self.request.GET.get('redirect')
        self.context['add_to_collection'] = self.request.GET.get('add_to_collection')
        item_types = [{'viewer': x.__name__.lower(), 'name': x._meta.verbose_name, 'name': x._meta.verbose_name, 'item_type': x} for x in all_item_types() if self.accepted_item_type in x.__bases__ + (x,)]
        item_types.sort(key=lambda x:x['name'].lower())
        self.context['item_types'] = item_types
        is_true = lambda value: bool(value) and value.lower() not in ('false', '0')
        if (is_true(self.request.GET.get('modal'))):
          template = loader.get_template('item/new_embed.html')
        else:
          template = loader.get_template('item/new.html')
        return HttpResponse(template.render(self.context))

    @require_POST
    def type_create_html(self):
        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        self.context['metabar_contents'] = u'Create a new %s' % self.accepted_item_type._meta.verbose_name
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
        self.context['metabar_contents'] = u'Display recent changes across this website'
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
        displayed_page_range = []
        for possible_page in page_range:
            if (possible_page < page + 10) and (possible_page > page-10):
                displayed_page_range.append(possible_page)

        self.context['action_notices'] = newPage
        self.context['count'] = paginator.count
        self.context['page_range'] = displayed_page_range

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
        edit_lock_response = self._edit_lock_response_pre_edit()
        if edit_lock_response:
            return edit_lock_response
        self.context['action_title'] = 'Edit'
        abilities_for_item = self.permission_cache.item_abilities(self.item)
        self.require_ability('edit ', self.item, wildcard_suffix=True)
        if form is None:
            form_initial = self.get_populated_field_dict(self.accepted_item_type)
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
        edit_lock_response = self._edit_lock_response_pre_update()
        if edit_lock_response:
            return edit_lock_response
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
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk, 'action': 'justdestroyed'}))
        return HttpResponseRedirect(redirect)

    def item_justdestroyed_html(self):
        if not self.item.destroyed:
            return self.render_error('Destroy error', "The item was not successfully destroyed due to an error in the application")
        self.context['action_title'] = 'Item destroyed'
        template = loader.get_template('item/justdestroyed.html')
        return HttpResponse(template.render(self.context))

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
            try:
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
            except KeyError:
                # malformed data, just pass instead of dying
                pass
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
        self.context['metabar_contents'] = u'Modify global permissions for this website'
        self.require_global_ability('do_anything')
        template = loader.get_template('item/globalpermissions.html')
        return HttpResponse(template.render(self.context))

    def type_admin_html(self):
        self.context['action_title'] = 'Admin'
        self.context['metabar_contents'] = u'Administrative options for this website'
        self.require_global_ability('do_anything')
        template = loader.get_template('item/admin.html')
        return HttpResponse(template.render(self.context))

    def type_permissionshelp_html(self):
        self.context['action_title'] = 'Permissions help'
        self.context['metabar_contents'] = u'Documentation on setting up permissions'
        template = loader.get_template('item/permissionshelp.html')
        return HttpResponse(template.render(self.context))

    def item_diff_html(self):
        self.context['action_title'] = 'Changes'
        self.context['reference_version_number'] = self.request.GET.get('reference_version', '')
        template = loader.get_template('item/diff.html')
        return HttpResponse(template.render(self.context))

    def type_recentlyviewedbox_json(self):
        pages = self.request.session.get('recentlyviewed', [])
        num_pages = int(self.request.REQUEST['num_pages'])
        new_url = self.request.REQUEST.get('new_url')
        new_title = self.request.REQUEST.get('new_title')
        clear_history = self.request.REQUEST.get('clear_history')
        if new_url and new_title and self.request.method == 'GET':
            pages = [x for x in pages if x[0] != new_url]
            pages.insert(0, (new_url, new_title))
            pages = pages[:100]
            self.request.session['recentlyviewed'] = pages
        if clear_history:
            pages = []
            self.request.session['recentlyviewed'] = pages
        data = pages[1:num_pages+1]
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def item_editlockrefresh_json(self):
        t = datetime.datetime.now()
        EditLock.objects.filter(item=self.item, editor=self.cur_agent).update(lock_refresh_time=t)
        return HttpResponse('', mimetype='application/json')

    def item_editlockremove_json(self):
        edit_locks = EditLock.objects.filter(item=self.item)
        if not self.cur_agent_can('do_anything', self.item):
            edit_locks = edit_locks.filter(editor=self.cur_agent)
        edit_locks.delete()
        return HttpResponse('', mimetype='application/json')

    def _edit_lock_response_pre_edit(self):
        t = datetime.datetime.now()
        min_refresh_time = t - datetime.timedelta(seconds=5)
        EditLock.objects.filter(item=self.item, lock_refresh_time__lt=min_refresh_time).delete()
        edit_locks = EditLock.objects.filter(item=self.item)
        if edit_locks:
            edit_lock = edit_locks[0]
            self.context['action_title'] = 'Edit'
            self.context['edit_lock'] = edit_lock
            self.context['can_remove_lock'] = self.cur_agent_can('do_anything', self.item) or edit_lock.editor.pk == self.cur_agent.pk
            template = loader.get_template('item/edit_locked.html')
            return HttpResponse(template.render(self.context))
        else:
            edit_lock = EditLock.objects.create(item=self.item, editor=self.cur_agent, lock_acquire_time=t, lock_refresh_time=t)
            return None

    def _edit_lock_response_pre_update(self):
        edit_locks = EditLock.objects.filter(item=self.item)
        edit_locks.delete()
        return None

    def item_metadata_html(self):
        metadata_menu_name = self.request.GET['name']
        self.context['original_full_path'] = self.request.GET['original_full_path']
        template_text = """{%% load item_tags %%}{%% metadata_%s %%}""" % metadata_menu_name
        template = django.template.Template(template_text)
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

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        # copied from symsys/views.py
        contact_method_fields = []
        contact_methods = self.permission_cache.filter_items('view ContactMethod.agent', self.item.contact_methods).filter(active=True)
        for contact_method in contact_methods:
            if issubclass(contact_method.actual_item_type(), EmailContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view EmailContactMethod.email', contact_method):
                    contact_method_fields.append(contact_method.email)
            if issubclass(contact_method.actual_item_type(), WebsiteContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view WebsiteContactMethod.url', contact_method):
                    link = ("""<a href="%s">%s</a>""" % (contact_method.url, contact_method.url))
                    contact_method_fields.append(mark_safe(link))
            if issubclass(contact_method.actual_item_type(), PhoneContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view PhoneContactMethod.phone', contact_method):
                    contact_method_fields.append(contact_method.phone)
            if issubclass(contact_method.actual_item_type(), FaxContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view FaxContactMethod.fax', contact_method):
                    contact_method_fields.append('(Fax) ' + contact_method.fax)
            if issubclass(contact_method.actual_item_type(), AIMContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view AIMContactMethod.screen_name', contact_method):
                    contact_method_fields.append('(AIM Screename) ' + contact_method.screen_name)
            if issubclass(contact_method.actual_item_type(), AddressContactMethod):
                contact_method = contact_method.downcast()
                if self.permission_cache.agent_can('view AddressContactMethod.street1', contact_method):
                    if contact_method.street2:
                        address = (""" %s <br> %s <br>%s, %s %s  %s """ % (contact_method.street1, contact_method.street2, contact_method.city, contact_method.state, contact_method.country, contact_method.zip))
                    else:
                        address = (""" %s <br>%s, %s %s  %s """ % (contact_method.street1, contact_method.city, contact_method.state, contact_method.country, contact_method.zip))
                    contact_method_fields.append(mark_safe(address))

        self.context['contact_methods'] = contact_method_fields

        template = loader.get_template('agent/show.html')
        return HttpResponse(template.render(self.context))

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
        self.context['metabar_contents'] = u'Login as a particular agent'
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
        self.request.session['recentlyviewed'] = []
        redirect = self.request.GET.get('redirect', '')
        full_redirect = '%s?redirect=%s' % (reverse('item_type_url', kwargs={'viewer': self.viewer_name, 'action': 'loggedinorout'}), urlquote(redirect))
        return HttpResponseRedirect(full_redirect)

    def type_loggedinorout_html(self):
        force_redirect_path = DemeSetting.get('cms.login_force_redirect_path')
        if force_redirect_path:
            return HttpResponseRedirect(force_redirect_path)
        if self.cur_agent.is_anonymous():
            self.context['action_title'] = 'Logged out'
            self.context['metabar_contents'] = u'You are now logged out'
        else:
            self.context['action_title'] = 'Logged in'
            self.context['metabar_contents'] = u'You are now logged in'
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('authenticationmethod/loggedinorout.html')
        return HttpResponse(template.render(self.context))

    def type_loginmenuitem_html(self):
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('authenticationmethod/loginmenuitem.html')
        login_as_agents = Agent.objects.filter(active=True).order_by('name')
        login_as_agents = self.permission_cache.filter_items('login_as', login_as_agents)
        can_login_as_anyone = True
        if login_as_agents.count() == 0:
            can_login_as_anyone = False
        self.context['can_login_as_anyone'] = can_login_as_anyone
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

    @require_POST
    def type_dialogcreate_html(self):
        if not self.request.POST.get('email'):
            return self.render_error('Invalid Subscription', "You must specify an email contact method by selecting it from the drop down menu")

        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        item = Item.objects.get(pk=self.request.POST.get('item'))
        email = EmailContactMethod.objects.get(pk=self.request.POST.get('email'))
        self.require_ability('add_subscription', email)

        new_subscription = Subscription(contact_method=email, item=item)
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_subscription.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_subscription.pk}))
        return HttpResponseRedirect(redirect)


class CollectionViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'collection'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        self.context['cur_agent_in_collection'] = self.item.child_memberships.filter(active=True, item=self.cur_agent).exists()
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
            return self.render_error('Invalid URL', "You must specify the member you are removing")
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
        from django.core.paginator import Paginator, InvalidPage, EmptyPage
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        collection_members = self.item.all_contained_collection_members(recursive_filter).order_by("name")

        members_per_page = 12
        p = Paginator(collection_members, members_per_page)

        try:
            page = int(self.request.GET.get('page','1'))
        except ValueError:
            page = 1

        try:
            entries = p.page(page)
        except (EmptyPage, InvalidPage):
            entries = p.page(p.num_pages)

        members = []

        for member in entries.object_list:
            if issubclass(member.actual_item_type(), Agent):
                member = member.downcast()
                member_details = {}
                member_details['item'] = member
                if member.photo:
                    if self.cur_agent_can('view Agent.photo', member):
                        member_details['photo'] = member.photo

                members.append(member_details)

        page_ranges = p.page_range
        displayed_page_range = []
        for possible_page in page_ranges:
            if (possible_page < page + members_per_page) and (possible_page > page-members_per_page):
                displayed_page_range.append(possible_page)

        self.context['members'] = members
        self.context['page_range'] = displayed_page_range

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

        try:
            membership = Membership.objects.get(collection=collection, item=item)
            if not membership.active:
                membership.reactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            membership = Membership(collection=collection, item=item)
        if self.request.POST.get('permissionenabled', '') == 'on':
            membership.permission_enabled = True
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        membership.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': membership.pk}))
        return HttpResponseRedirect(redirect)

    def type_itemmembercreate_html(self):
        collection_pk = self.request.POST.get('collection')
        if collection_pk == '':
            return self.render_error('Invalid Membership', "You must specify which collection to add this item to")

        self.require_global_ability('create %s' % self.accepted_item_type.__name__)
        collection = Collection.objects.get(pk=collection_pk)
        item = Item.objects.get(pk=self.request.POST['item'])

        try:
            membership = Membership.objects.get(collection=collection, item=item)
            if not membership.active:
                membership.reactivate(action_agent=self.cur_agent)
        except ObjectDoesNotExist:
            membership = Membership(collection=collection, item=item)
        if self.request.POST.get('permissionenabled', '') == 'on':
            membership.permission_enabled = True
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        membership.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))

        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': membership.pk}))
        return HttpResponseRedirect(redirect)


class DocumentViewer(ItemViewer):
    accepted_item_type = Document
    viewer_name = 'document'


class TextDocumentViewer(DocumentViewer):
    accepted_item_type = TextDocument
    viewer_name = 'textdocument'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.context['in_textdocument_show'] = True
        self.context['highlighted_transclusion_id'] = self.request.GET.get('highlighted_transclusion')
        self.context['highlighted_comment_id'] = self.request.GET.get('highlighted_comment')
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('textdocument/show.html')
        self.context['is_html'] = issubclass(self.accepted_item_type, HtmlDocument)
        return HttpResponse(template.render(self.context))

    def item_edit_html(self, form=None):
        edit_lock_response = self._edit_lock_response_pre_edit()
        if edit_lock_response:
            return edit_lock_response
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
            form_initial = self.get_populated_field_dict(self.accepted_item_type)
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
        self.context['redirect'] = self.request.GET.get('redirect');
        return HttpResponse(template.render(self.context))

    @require_POST
    def item_update_html(self):
        edit_lock_response = self._edit_lock_response_pre_update()
        if edit_lock_response:
            return edit_lock_response
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
            redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': new_item.pk}))
            return HttpResponseRedirect(redirect)
        else:
            return self.item_edit_html(form)


class DjangoTemplateDocumentViewer(TextDocumentViewer):
    accepted_item_type = DjangoTemplateDocument
    viewer_name = 'djangotemplatedocument'

    def default_metadata_menu_option(self):
        return None

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


class ImageDocumentViewer(FileDocumentViewer):
    accepted_item_type = ImageDocument
    viewer_name = 'imagedocument'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('imagedocument/show.html')
        return HttpResponse(template.render(self.context))


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
        self.context['metabar_contents'] = u'Create a new %s' % self.accepted_item_type._meta.verbose_name
        try:
            item = Item.objects.get(pk=self.request.REQUEST.get('populate_item' if form is None else 'item'))
        except:
            return self.render_error('Invalid URL', "You must specify the item you are commenting on")
        if not self.cur_agent_can_global('create %s' % self.accepted_item_type.__name__):
            form = None
        else:
            if form is None:
                form_initial = self.get_populated_field_dict(self.accepted_item_type)
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
        if self.cur_agent.is_anonymous():
            #code for the previously cracked addition captcha
            #if "sq_1" in self.request.POST:
             #   value = self.request.POST["sq_1"]
              #  response, value = value.strip().lower(), ''
               # if not hashlib.sha1(str(response)).hexdigest() == self.request.POST["sq_0"]:
                #    return self.render_error('Invalid Answer', 'Add up the numbers correctly to prove you are not a spammer')

            if not self.request.POST.get('simple_captcha', '') == "abc123":
                return self.render_error('Invalid Answer', 'Enter the phrase correctly to prove you are not a spammer')

        new_body = self.request.POST.get('comment_body')
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
        if self.request.POST.get('new_from_contact_method'):
            new_comment.from_contact_method = ContactMethod.objects.get(pk=self.request.POST.get('new_from_contact_method'))
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_comment.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions, action_summary=self.request.POST.get('actionsummary', ''))

        if self.request.GET.get('populate_item_index'):
            transclusion = Transclusion(from_item=item.downcast(), from_item_version_number=self.request.POST.get('item_version_number'), from_item_index=self.request.GET.get('populate_item_index'), to_item=new_comment)
            transclusion_permissions = [OneToOnePermission(source=self.cur_agent, ability='do anything', is_allowed=True)]
            transclusion.save_versioned(action_agent=self.cur_agent, initial_permissions=transclusion_permissions)

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
        self.context['metabar_contents'] = u'Modify global website settings'
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

