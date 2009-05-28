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
        return HttpResponse(template.render(self.context))

