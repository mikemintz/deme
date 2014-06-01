# Ajax upload backend
from ajaxuploader.backends.local import LocalUploadBackend
from deme_django.cms.models import FileDocument, ImageDocument

class FileDocumentLocalUploadBackend(LocalUploadBackend):
    def upload_complete(self, request, filename, *args, **kwargs):
        cur_agent = kwargs['cur_agent']
        new_item = FileDocument(datafile=self.UPLOAD_DIR + '/' + filename)
        new_item.save_versioned(action_agent=cur_agent) # TODO: permissions
