from django.db import models
import datetime
from cms.models import HtmlDocument, Collection, FixedBooleanField, Agent, FixedForeignKey, Item
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget
from django.forms.extras.widgets import SelectDateWidget


__all__ = ['RecursiveProject', 'RecursiveProjectDependency'] 

class RecursiveProject(Collection, HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view RecursiveProject.due_date', 'edit RecursiveProject.due_date', 'view RecursiveProject.beginning_date', 'edit RecursiveProject.beginning_date',
                                     'view RecursiveProject.due_time', 'edit RecursiveProject.due_time', 'view RecursiveProject.priority', 'edit RecursiveProject.priority',
                                     'view RecursiveProject.length', 'edit RecursiveProject.length', 'view RecursiveProject.status', 'edit RecursiveProject.status',
                                     'view RecursiveProject.repeat', 'edit RecursiveProject.repeat', 'view RecursiveProject.RecursiveProject_handler', 'edit RecursiveProject.RecursiveProject_handler'])
    introduced_global_abilities = frozenset(['create RecursiveProject'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('recursiveproject')
        verbose_name_plural = _('recursiveprojects')

    #fields:
    beginning_date = models.DateField(_('beginning date'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_date = models.DateField(_('due date'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    due_time = models.TimeField(_('due time'), null=True, blank=True, default=None)
    Priority_Choices = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'), 
        ('Other', 'Other'),
    )
    priority = models.CharField(_('priority'), max_length=10, default='Low', choices=Priority_Choices) 
    priority_text = models.CharField(_('other'), max_length=16, null=True, blank=True, default=None)
    length = models.DecimalField(_('length'), default=0, max_digits=6, decimal_places=2, help_text=_('in hours'))
    Status_Choices = (
        ('Unassigned', 'Unassigned'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
    )
    status = models.CharField(_('status'), default='Unassigned', max_length=16, choices=Status_Choices)
    Repeat_Choices = (
        ('Never', 'Never'),
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    )
    repeat = models.CharField(_('repeating?'), default='Never', max_length=16, choices=Repeat_Choices)
    RecursiveProject_handler = FixedForeignKey(Agent, related_name='RecursiveProject_handler', null=True, blank=True, default=None)

   

    def _before_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(RecursiveProject, self)._before_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
        if self.status == 'Completed' and self.repeat != 'Never':
            self.advance_due_date_one_period()
            self.change_status_to_assigned()
    _before_edit.alters_data = True

    def advance_due_date_one_period(self):
        from datetime import timedelta
        due_date = self.due_date
        if self.repeat == 'Daily':
            day = timedelta(days=1)
            self.due_date = due_date + day
        elif self.repeat == 'Weekly':
            week = timedelta(days=7)
            self.due_date = due_date + week
        elif self.repeat == 'Monthly':
            month = timedelta(months=1)
            self.due_date = due_date + month
        elif self.repeat == 'Yearly':
            year = timedelta(months=12)
            self.due_date = due_date + year

    def change_status_to_assigned(self):
        self.status = "Assigned"
        
"""    
class RecursiveProject($1ument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view RecursiveProject.due_date', 'edit RecursiveProject.due_date', 'view RecursiveProject.beginning_date', 'edit RecursiveProject.beginning_date',
                                     'view RecursiveProject.due_time', 'edit RecursiveProject.due_time', 'view RecursiveProject.priority', 'edit RecursiveProject.priority',
                                     'view RecursiveProject.length', 'edit RecursiveProject.length', 'view RecursiveProject.status', 'edit RecursiveProject.status',
                                     'view RecursiveProject.is_repeating', 'edit RecursiveProject.is_repeating', 'view RecursiveProject.RecursiveProject_handler', 'edit RecursiveProject.RecursiveProject_handler'])
    introduced_global_abilities = frozenset(['create RecursiveProject'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('RecursiveProject')
        verbose_name_plural = _('RecursiveProjects')

    #fields:
    due_date = models.DateField(_('due date'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    beginning_date = models.DateField(_('beginning date'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    
    due_time = models.TimeField(_('due time'), null=True, blank=True, default=None)
    
    Priority_Choices = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    priority = models.CharField(_('priority'), max_length=10, default='Low', choices=Priority_Choices)
    
    length = models.DecimalField(_('length'), default=0, max_digits=6, decimal_places=2, help_text=_('in hours'))
    
    Status_Choices = (
        ('Unassigned', 'Unassigned'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
    )
    status = models.CharField(_('status'), default='Unassigned', max_length=16, choices=Status_Choices)
	
    is_repeating = FixedBooleanField(_('is repeating'), default=False, help_text=_('Select this if this RecursiveProject will be repeated.'))
    
    RecursiveProject_handler = FixedForeignKey(Agent, related_name='RecursiveProject_handler', null=True, blank=True, default=None)
"""
class RecursiveProjectDependency(Item):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view RecursiveProjectDependency.dependent_RecursiveProject', 'view RecursiveProjectDependency.required_RecursiveProject'])
    introduced_global_abilities = frozenset(['create RecursiveProjectDependency'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('RecursiveProject dependency')
        verbose_name_plural = _('RecursiveProject dependencies')

    #fields:
    dependent_RecursiveProject = FixedForeignKey(RecursiveProject, related_name='dependent_RecursiveProject', null=True, blank=True, default=None)
    required_RecursiveProject = FixedForeignKey(RecursiveProject, related_name='required_RecursiveProject', null=True, blank=True, default=None)

    
    
    
