from django.db import models
import datetime
from cms.models import HtmlDocument, Collection
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget

__all__ = ['Project'] 

class Project(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Project'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    #fields:
    due_date = models.DateField(_('due date'), help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_time = models.TimeField(_('due time'))