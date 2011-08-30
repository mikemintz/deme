from django.db import models
import datetime
from cms.models import HtmlDocument, Collection, FixedBooleanField, Agent, FixedForeignKey, Item, Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget
from django.forms.extras.widgets import SelectDateWidget
from django.core.validators import  MaxLengthValidator

__all__ = ['Poll'] 

class Poll(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['edit Poll.visibility', 'view Poll.visibility', 'edit Poll.question', 'view Poll.question',
                                      'edit Poll.begins', 'view Poll.begins', 'edit Poll.deadline', 'view Poll.deadline', 
                                      'edit Poll.eligibles', 'view Poll.eligibles', 'edit Poll.display_write_ins', 
                                      'view Poll.display_write_ins'])
    introduced_global_abilities = frozenset(['create Poll'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('poll')
        verbose_name_plural = _('polls')

    #fields:
    question = models.TextField(_('question'), blank=True)
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

class ChooseNPoll(Poll):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ChooseNPoll.n', 'edit ChooseNPoll.n'])
    introduced_global_abilities = frozenset(['create ChooseNPoll'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('choose n poll')
        verbose_name_plural = _('choose n polls')
    
    #fields:
    n_choices = zip( range(0,101), range(0,101) )
    n = models.IntegerField(blank=True, choices=n_choices)
    

class ApproveNPoll(Poll):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ApproveNPoll.n', 'edit ApproveNPoll.n'])
    introduced_global_abilities = frozenset(['create ApproveNPoll'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('approve n poll')
        verbose_name_plural = _('approve n polls')

    #fields:
    n_choices = zip( range(0,101), range(0,101) )
    n = models.IntegerField(blank=True, choices=n_choices)

    
   
    
class Proposition(HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['edit Proposition.summary_text', 'view Proposition.summary_text', 
                                      'edit Proposition.is_write_in', 'view Proposition.is_write_in'])
    introduced_global_abilities = frozenset(['create Proposition'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('proposition')
        verbose_name_plural = _('propositions')

    #fields:
    summary_text = models.CharField(_('summary text'), blank=True, max_length=40)
    is_write_in  = FixedBooleanField(_('is write in'), default=False, help_text=_('Select this if you wish to make a write in proposition'))

class WriteInPropositions(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create WriteInPropositions'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('writeinproposition')
        verbose_name_plural = _('writeinpropositions')
        
    #fields:
    poll = FixedForeignKey(Poll, related_name='poll_writein', null=True, blank=True, default=None)

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

class PropositionResponseChoose(PropositionResponse):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PropositionResponseChoose.poll', 'edit PropositionResponseChoose.poll', 'view PropositionResponseChoose.participant', 
                                    'edit PropositionResponseChoose.participant','view PropositionResponseChoose.proposition', 'edit PropositionResponseChoose.proposition',
                                    'edit PropositionResponseChoose.value', 'view PropositionResponseChoose.value'])
    introduced_global_abilities = frozenset(['create PropositionResponseChoose'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('propositionresponsechoose')
        verbose_name_plural = _('propositionresponsechooses')

    #fields:
    value_choices = (
        ('chosen' , 'Chosen' ),
        ('not chosen', 'Not Chosen'),
    )
    value = models.CharField(_('status'), default='Unassigned', max_length=36, choices=value_choices)
    

class PropositionResponseApprove(PropositionResponse):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PropositionResponseApprove.poll', 'edit PropositionResponseApprove.poll', 'view PropositionResponseApprove.participant', 
                                    'edit PropositionResponseApprove.participant','view PropositionResponseApprove.proposition', 'edit PropositionResponseApprove.proposition',
                                    'edit PropositionResponseApprove.value', 'view PropositionResponseApprove.value'])
    introduced_global_abilities = frozenset(['create PropositionResponseApprove'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('propositionresponseapprove')
        verbose_name_plural = _('propositionresponseapprove')

    #fields:
    value_choices = (
        ('approve' , 'Approve' ),
        ('dissaprove', 'Disapprove'),
        ('no vote', 'No Vote'),
    )
    value = models.CharField(_('status'), default='Unassigned', max_length=36, choices=value_choices)    
    
class Decision(Item):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Decision.poll', 'edit Decision.poll'])
    introduced_global_abilities = frozenset(['create Decision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('decision')
        verbose_name_plural = _('decisions')

    #fields:
    
    #TODO: find out how to set max value in integer field
    quorum_choices = zip( range(0,101), range(0,101) )
    quorum = models.IntegerField(blank=True, choices=quorum_choices)
    poll = FixedForeignKey(Poll, related_name='polls_decision', null=True, blank=True, default=None)
    

class PluralityChooseNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PluralityChooseNDecision.poll', 'edit PluralityChooseNDecision.poll', 'view PluralityChooseNDecision.num_decision',
                                    'edit PluralityChooseNDecision.num_decision'])
    introduced_global_abilities = frozenset(['create PluralityChooseNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('PluralityChooseNDecision')
        verbose_name_plural = _('PluralityChooseNDecision')
    
    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)

class ThresholdChooseNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ThresholdChooseNDecision.poll', 'edit ThresholdChooseNDecision.poll' , 'view ThresholdChooseNDecision.num_decision'
                                    , 'edit ThresholdChooseNDecision.num_decision'  , 'view ThresholdChooseNDecision.p_decision' , 'edit ThresholdChooseNDecision.p_decision'])
    introduced_global_abilities = frozenset(['create ThresholdChooseNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('ThresholdChooseNDecision')
        verbose_name_plural = _('ThresholdChooseNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)
    p_choices = zip( range(0,101), range(0,101) )
    p_decision = models.IntegerField(blank=True, choices=p_choices)

class ThresholdEChooseNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ThresholdEChooseNDecision.poll', 'edit ThresholdEChooseNDecision.poll' , 'view ThresholdEChooseNDecision.num_decision'
                                    , 'edit ThresholdEChooseNDecision.num_decision'  , 'view ThresholdEChooseNDecision.e_decision' , 'edit ThresholdEChooseNDecision.e_decision'])
    introduced_global_abilities = frozenset(['create ThresholdEChooseNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('ThresholdEChooseNDecision')
        verbose_name_plural = _('ThresholdEChooseNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)
    e_choices = zip( range(0,101), range(0,101) )
    e_decision = models.IntegerField(blank=True, choices=e_choices)

class UnanimousChooseNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view UnanimousChooseNDecision.poll', 'edit UnanimousChooseNDecision.poll' , 'view UnanimousChooseNDecision.num_decision'
                                    , 'edit UnanimousChooseNDecision.num_decision'  , 'view UnanimousChooseNDecision.m_decision' , 'edit UnanimousChooseNDecision.m_decision'])
    introduced_global_abilities = frozenset(['create UnanimousChooseNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('UnanimousChooseNDecision')
        verbose_name_plural = _('UnanimousChooseNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)
    m_choices = zip( range(0,101), range(0,101) )
    m_decision = models.IntegerField(blank=True, choices=m_choices)

class PluralityApproveNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view PluralityApproveNDecision.poll', 'edit PluralityApproveNDecision.poll', 'view PluralityApproveNDecision.num_decision',
                                    'edit PluralityApproveNDecision.num_decision'])
    introduced_global_abilities = frozenset(['create PluralityApproveNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('PluralityApproveNDecision')
        verbose_name_plural = _('PluralityApproveNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)  

class ThresholdApproveNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ThresholdApproveNDecision.poll', 'edit ThresholdApproveNDecision.poll' , 'view ThresholdApproveNDecision.num_decision'
                                    , 'edit ThresholdApproveNDecision.num_decision'  , 'view ThresholdApproveNDecision.p_decision' , 'edit ThresholdApproveNDecision.p_decision'])
    introduced_global_abilities = frozenset(['create ThresholdApproveNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('ThresholdApproveNDecision')
        verbose_name_plural = _('ThresholdApproveNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)
    p_choices = zip( range(0,101), range(0,101) )
    p_decision = models.IntegerField(blank=True, choices=p_choices)

class ThresholdEApproveNDecision(Decision):
    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view ThresholdEApproveNDecision.poll', 'edit ThresholdEApproveNDecision.poll' , 'view ThresholdEApproveNDecision.num_decision'
                                    , 'edit ThresholdEApproveNDecision.num_decision'  , 'view ThresholdEApproveNDecision.e_decision' , 'edit ThresholdEApproveNDecision.e_decision'])
    introduced_global_abilities = frozenset(['create ThresholdEApproveNDecision'])
    dyadic_relations = {}

    class Meta:    
        verbose_name = _('ThresholdEApproveNDecision')
        verbose_name_plural = _('ThresholdEApproveNDecision')

    #fields
    n_choices = zip( range(0,101), range(0,101) )
    num_decision = models.IntegerField(blank=True, choices=n_choices)
    e_choices = zip( range(0,101), range(0,101) )
    e_decision = models.IntegerField(blank=True, choices=e_choices)
    
#class ApproveNForm(forms.Form):
#          ('approve' , 'Approve' ),
#           ('dissaprove', 'Disapprove'),
#           ('no vote', 'No Vote'),
#       )
#    vote = models.CharField(_('status'), default='Unassigned', max_length=36, choices=value_choices)  
    
    
    
