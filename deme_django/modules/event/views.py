from django.template import Context, loader
from django.http import HttpResponse
from cms.views import HtmlDocumentViewer
from modules.event.models import Event


class EventViewer(HtmlDocumentViewer):
    accepted_item_type = Event
    viewer_name = 'event' 

