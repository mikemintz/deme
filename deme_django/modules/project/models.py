from django.db import models
import datetime
from cms.models import HtmlDocument, Collection
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget
from django.forms.extras.widgets import SelectDateWidget


__all__ = ['Project','Task'] 

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
    
class Task(HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Task'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('task')
        verbose_name_plural = _('tasks')

    #fields:
	start_date = models.DateField(_('due date'), help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_date = models.DateField(_('due date'), help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_time = models.TimeField(_('due time'))
    
    Priority_Choices = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    priority = models.CharField(_('priority'),max_length=10, choices=Priority_Choices)
    
    length = models.DecimalField(_('length'), max_digits=6, decimal_places = 2, help_text=_('in hours'))
    
    Status_Choices = (
        ('Unassigned', 'Unassigned'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
    )
    status = models.CharField(_('status'),max_length=16, choices=Status_Choices)

	Bool_Choices = (
		('Yes', 'Y'),
		('No', 'N'),
	)
	
	repeating = models.CharField(_('status'), max_length=16, choices=Bool_Choices)
    
