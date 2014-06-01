# Ajax upload backend
from ajaxuploader.backends.local import LocalUploadBackend
from deme_django.cms.models import FileDocument, ImageDocument
from datetime import date
from django.conf import settings
from io import FileIO, BufferedWriter


import datetime
import os

class FileDocumentLocalUploadBackend(LocalUploadBackend):
    def upload_to(self):
        d = datetime.datetime.now()
        return d.strftime('filedocument/%Y/%m/%d')


    def setup(self, filename, *args, **kwargs):
        self._path = os.path.join(
            settings.MEDIA_ROOT, self.upload_to(), filename)
        try:
            os.makedirs(os.path.realpath(os.path.dirname(self._path)))
        except:
            pass
        self._dest = BufferedWriter(FileIO(self._path, "w"))


    def upload_complete(self, request, filename, *args, **kwargs):
        cur_agent = kwargs['cur_agent']
        relative_path = self.upload_to() + "/" + filename
        full_path = settings.MEDIA_URL + relative_path
        name = filename
        new_item = FileDocument(name=name, datafile=relative_path)

        # TODO: auto categorize images
        # TODO: make images links
        new_item.save_versioned(action_agent=cur_agent) # TODO: permissions
        self._dest.close()
        return {"path": full_path}
