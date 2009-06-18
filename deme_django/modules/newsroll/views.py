from django.template import Context, loader
from django.db.models import Q
from django.http import HttpResponse
from cms.views import ItemViewer
from cms.models import *

class NewsRollViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'newsroll'

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        template = loader.get_template('newsroll/show.html')
        collection = self.item
        self.context['collection'] = collection

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        members = collection.all_contained_collection_members(recursive_filter).order_by('-created_at')

        #TODO pagination
        member_details = []
        for member in members:
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
 

        self.context['members'] = member_details
        return HttpResponse(template.render(self.context))

