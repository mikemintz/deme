from cms.models import FileDocument
from django.utils.translation import ugettext_lazy as _

__all__ = ['ImageDocument']

class ImageDocument(FileDocument):
    """
    An ImageDocument is a FileDocument that stores an image.
    
    Right now, the only difference is that viewers know the file can be
    displayed as an image. In the future, this may add metadata like EXIF data
    and thumbnails.
    """

    # Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create ImageDocument'])
    class Meta:
        verbose_name = _('image document')
        verbose_name_plural = _('image documents')

