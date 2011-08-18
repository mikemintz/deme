from django.db import models
import datetime
from cms.models import HtmlDocument, Collection, FixedBooleanField, Agent, FixedForeignKey, Item, Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget
from django.forms.extras.widgets import SelectDateWidget


__all__ = ['Poll'] 

class Poll(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Poll'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('poll')
        verbose_name_plural = _('polls')

    #fields:
    question = models.TextField(_('question'), blank=True)
    response_formats = (
        ('choice 1', 'c1'),
        ('choice 2', 'c2'),
        ('choice 3', 'c3'),
    )
    response_format = models.CharField(_('status'), default='Unassigned', max_length=16, choices=response_formats)
    begins = models.DateField(_('begins'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    deadline = models.DateField(_('deadline'), null=True, blank=True, default=None, help_text=_('Dates must be entered in the format "MM/DD/YY"'))
    eligibles = FixedForeignKey(Group, related_name='poll_participant', null=True, blank=True, default=None)
    visibility_choices = (
        ('responses visible' , 'responses visible - each eligible that has responded is visible' ),
        ('who responded visible', 'who responded visible - who has responded is visible, but not how they responded'),
        ('closed' , 'closed - neither who has responded nor how they have responded is visible'),
    )
    visibility = models.CharField(_('status'), default='Unassigned', max_length=36, choices=visibility_choices)
    display_write_ins = FixedBooleanField(_('display write ins'), default=False, help_text=_('Select this if you wish to display write ins'))
    
class Proposition(HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Proposition'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('proposition')
        verbose_name_plural = _('propositions')

    #fields:
    summary_text = models.TextField(_('summary text'), blank=True)
    is_write_in  = FixedBooleanField(_('is write in'), default=False, help_text=_('Select this if you wish to make a write in proposition'))

class PropositionResponse(HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PropositionResponse.poll', 'edit PropositionResponse.poll', 'view PropositionResponse.participant', 'edit PropositionResponse.participant',
                                    'view PropositionResponse.proposition', 'edit PropositionResponse.proposition'])
    introduced_global_abilities = frozenset(['create PropositionResponse'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('propositionresponse')
        verbose_name_plural = _('propositionresponses')

    #fields:
    poll = FixedForeignKey(Poll, related_name='poll_response', null=True, blank=True, default=None)
    participant = FixedForeignKey(Agent, related_name='poll_participant', null=True, blank=True, default=None)
    proposition = FixedForeignKey(Proposition, related_name='poll_proposition', null=True, blank=True, default=None)
    
    
    
    
    
