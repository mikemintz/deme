from django.http import HttpResponse
from django.template import loader
from cms.views import FileDocumentViewer
from modules.imagedocument.models import ImageDocument

class ImageDocumentViewer(FileDocumentViewer):
    accepted_item_type = ImageDocument
    viewer_name = 'imagedocument'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('imagedocument/show.html')
        return HttpResponse(template.render(self.context))

