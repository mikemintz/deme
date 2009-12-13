from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from cms.views import ItemViewer
from cms.models import *

#This class is purely for displaying the guide to making a blog
class BlogGuide(ItemViewer):
    accepted_item_type = Item
    viewer_name = 'blogguide'

    def type_list_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('blogguide/show.html')
        self.context['host'] = self.request.get_host()

        return HttpResponse(template.render(self.context))

#This class is for displaying the recent posts and grouping posts together on the side of a blog
class BlogPostViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'blogpost'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('blogpost/show.html')
        
        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members = self.item.all_contained_collection_members(recursive_filter).order_by('-created_at')

        member_details = []
        for member in members:
            if issubclass(member.actual_item_type(), TextDocument):
                member = member.downcast()
                details = {}
                details["member"] = member
                details["name"] = member.display_name()
                details["url"] = member.get_absolute_url() 
                member_details.append(details)
                
        self.context['entries'] = member_details
        return HttpResponse(template.render(self.context))

#This class is for displaying "BlogRolls", i.e. collections of links 
#on the side of a blog
class BlogRollViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'blogroll'

    def item_show_html(self):
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('blogroll/show.html')
        
        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members = self.item.all_contained_collection_members(recursive_filter).order_by('-created_at')

        member_details = []
        for member in members:
            if issubclass(member.actual_item_type(), Webpage):
                member = member.downcast()
                details = {}
                details["member"] = member
                details["name"] = member.display_name()
                details["url"] = member.url
                member_details.append(details)
            
        self.context['webpages'] = member_details
        return HttpResponse(template.render(self.context))

class NewsRollViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'newsroll'

    def item_show_html(self):
        from django.core.paginator import Paginator, InvalidPage, EmptyPage
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        template = loader.get_template('newsroll/show.html')
        collection = self.item
        self.context['collection'] = collection

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members = collection.all_contained_collection_members(recursive_filter).order_by('-created_at')

        p = Paginator(members, 10)

        try:
            page = int(self.request.GET.get('page','1'))
        except ValueError:
            page = 1

        try:
            entries = p.page(page)
        except (EmptyPage, InvalidPage):
            entries = p.page(p.num_pages)

        member_details = []
        for member in entries.object_list:
            details = {}
            details["member"] = member
            details["name"] = member.display_name()
            details["url"] = member.get_absolute_url() 
            details["creator"] = member.creator.display_name()
            details["created_at"] = member.created_at
            details["creator_url"] = member.creator.get_absolute_url()
            if issubclass(member.actual_item_type(), TextDocument):
                member = member.downcast()
                details["display_body"] = True
                details["is_html"] = issubclass(member.actual_item_type(), HtmlDocument)
                details["body"] = member.body
            else:
                details["display_body"] = False
                details["body"] = "Empty"
                details["is_html"] = False

            member_details.append(details)

        page_ranges = p.page_range
        displayed_page_range = []
        for possible_page in page_ranges:
            if (possible_page < page + 10) and (possible_page > page-10):
                displayed_page_range.append(possible_page)

        self.context['redirect'] = reverse('item_url', kwargs={'viewer': 'newsroll', 'action': 'show', 'noun': collection.pk}) 
        self.context['members'] = member_details
        self.context['entries'] = entries
        self.context['page_range'] = displayed_page_range
        return HttpResponse(template.render(self.context))

