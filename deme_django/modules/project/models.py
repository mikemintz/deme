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
    due_date = models.DateField(_('due date'), help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_time = models.TimeField(_('due time'))
    
    Priority_Choices = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    priority = models.CharField(_('priority'),max_length=10, choices=Priority_Choices)
    
    length = models.DecimalField(_('length'), max_digits=6, decimal_places = 2)
    
    Status_Choices = (
        ('None', 'None - This is the default status of a newly created task.'),
        ('Next Action', 'Next Action - This can be used to indicate which tasks must be completed next.'),
        ('Active', 'Active - Indicates a task that must be completed.'),
        ('Planning', 'Planning - A task that you are planning, so it may not be active yet.'),
        ('Delegated ', 'Delegated - A task that you have given to someone else.'),
        ('Waiting', 'Waiting - You are waiting on something external.'),
        ('Hold', 'Hold - This task has been placed on hold indefinitely, or until you take it off hold.'),
        ('Postponed', 'Postponed - This task has been delayed.'),
        ('Someday', "Someday- An optional task, or something that you don't know if you want to do, but you still want to record it for the future."),
        ('Canceled', "Canceled- You don't want to complete this task, but you still need it recorded for some reason."),
        ('Reference', "Reference - Use this for tasks that aren't really tasks, but are more of a piece of reference info."),
    )
    status = models.CharField(_('priority'),max_length=16, choices=Status_Choices)
    
