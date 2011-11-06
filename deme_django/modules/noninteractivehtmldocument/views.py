from django.template import Context, loader
from cms.views import HtmlDocumentViewer
from modules.noninteractivehtmldocument.models import NonInteractiveHtmlDocument


class NonInteractiveHtmlDocumentViewer(HtmlDocumentViewer):
    accepted_item_type = NonInteractiveHtmlDocument
    viewer_name = 'noninteractivehtmldocument' 

    def default_metadata_menu_option(self):
        return None

