from django.template import Context, loader
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
        members = collection.all_contained_collection_members()

        #TODO permissions to view all_contained_collection_members (with recurisve filter)
        #TODO permission to view each field
        #TODO html document rendered
        #TODO order by date
        #TODO pagination
        member_details = []
        for member in members:
            details = {}
            details["name"] = member.display_name()
            details["url"] = member.get_absolute_url() 
            details["type"] = member.item_type_string
            details["creator"] = member.creator.display_name()
            details["created_at"] = member.created_at
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

