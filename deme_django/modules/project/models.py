from django.db import models
import datetime
from cms.models import HtmlDocument, Collection, FixedBooleanField, Agent, FixedForeignKey, Item
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget
from django.forms.extras.widgets import SelectDateWidget



__all__ = ['Project', 'ProjectDependency'] 

class Project(Collection, HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Project.due_date', 'edit Project.due_date', 'view Project.beginning_date', 'edit Project.beginning_date',
                                     'view Project.due_time', 'edit Project.due_time', 'view Project.priority', 'edit Project.priority',
                                     'view Project.length', 'edit Project.length', 'view Project.status', 'edit Project.status',
                                     'view Project.repeat', 'edit Project.repeat', 'view Project.Project_handler', 'edit Project.Project_handler'])
    introduced_global_abilities = frozenset(['create Project'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('project')
        verbose_name_plural = _('projects')

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
    Project_handler = FixedForeignKey(Agent, related_name='Project_handler', null=True, blank=True, default=None)

   

    def _before_edit(self, action_agent, action_summary, action_time, multi_agent_permission_cache):
        super(Project, self)._before_edit(action_agent, action_summary, action_time, multi_agent_permission_cache)
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
    
	
class ProjectDependency(Item):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ProjectDependency.dependent_Project', 'view ProjectDependency.required_Project'])
    introduced_global_abilities = frozenset(['create ProjectDependency'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('Project dependency')
        verbose_name_plural = _('Project dependencies')

    #fields:
    dependent_Project = FixedForeignKey(Project, related_name='dependent_Project', null=True, blank=True, default=None)
    required_Project = FixedForeignKey(Project, related_name='required_Project', null=True, blank=True, default=None)
	
    
