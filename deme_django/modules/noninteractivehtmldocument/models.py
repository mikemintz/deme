from django.db import models
from cms.models import HtmlDocument
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

__all__ = ['NonInteractiveHtmlDocument'] 

class NonInteractiveHtmlDocument(HtmlDocument): 

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create NonInteractiveHtmlDocument'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('non-interactive HTML document')
        verbose_name_plural = _('non-interactive HTML documents')

