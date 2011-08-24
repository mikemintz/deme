from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.poll.models import Poll, Proposition, PropositionResponse, Decision, WriteInPropositions, PropositionResponseChoose, PropositionResponseApprove, ChooseNPoll, ApproveNPoll, UnanimousChooseNDecision
from modules.poll.models import PluralityChooseNDecision, ThresholdChooseNDecision, ThresholdEChooseNDecision, PluralityApproveNDecision, ThresholdApproveNDecision, ThresholdEApproveNDecision
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time
import math


class PollViewer(CollectionViewer):
    accepted_item_type = Poll
    viewer_name = 'poll' 


    def item_show_html(self):
        dependencies = PropositionResponse.objects.all()
        
        self.context['responses'] = dependencies.filter(poll=self.item.pk)
        
        self.context['maxPollTakers'] = len(Membership.objects.all().filter(collection=self.item.eligibles))
        
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        template = loader.get_template('poll/poll.html')
        return HttpResponse(template.render(self.context))

class ChooseNPollViewer(PollViewer):
    accepted_item_type = ChooseNPoll
    viewer_name = 'choosenpoll' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        template = loader.get_template('poll/choosenpoll.html')
        return HttpResponse(template.render(self.context))
        

class ApproveNPollViewer(PollViewer):
    accepted_item_type = ApproveNPoll
    viewer_name = 'approvenpoll' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        self.context['responses'] = PropositionResponseApprove.objects.all().filter(poll=self.item)
        eligible_agents = self.item.eligibles.child_memberships
        eligible_agents = eligible_agents.filter(active=True)
        eligible_agents = eligible_agents.filter(item__active=True)
        eligible_agents = self.permission_cache.filter_items('view Membership.item', eligible_agents)
        eligible_agents = eligible_agents.select_related('item')
        if eligible_agents:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agents]))
        self.context['eligible_agents'] = sorted(eligible_agents, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['participants'] = Agent.objects.filter(poll_participant__poll=self.item)
        Responses = dict()
        for agent in eligible_agents:
            Responses[agent.item] = PropositionResponseApprove.objects.all().filter(poll=self.item).filter(participant=agent.item)
        self.context['Responses'] = Responses
        self.context['decisions'] = Decision.objects.all().filter(poll=self.item)
        template = loader.get_template('poll/approvenpoll.html')
        return HttpResponse(template.render(self.context))

    #def respondtopropositions(self):
     #   if request.method == 'POST':
     #       form = ContactForm(self.request.POST)
     #       if form.is_valid():
     #   response = PropositionResponseChoose.objects.create(poll=self., participant= "", proposition = "", value = "")
     #  try:
     #       vote = RecursiveProject.objects.get(pk=self.request.POST.get('vote'))
     #   except:
     #       return self.render_error('Invalid URL', "There is something wrong....")
     #   print(vote)
        
class PropositionViewer(HtmlDocumentViewer):
    accepted_item_type = Proposition
    viewer_name = 'proposition' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        template = loader.get_template('poll/proposition.html')
        return HttpResponse(template.render(self.context))

class PropositionResponseViewer(HtmlDocumentViewer):
    accepted_item_type = PropositionResponse
    viewer_name = 'propositionresponse' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        template = loader.get_template('poll/propositionresponse.html')
        return HttpResponse(template.render(self.context))
        
class PropositionResponseChooseViewer(PropositionResponseViewer):
    accepted_item_type = PropositionResponseChoose
    viewer_name = 'propositionresponsechoose' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        template = loader.get_template('poll/propositionresponsechoose.html')
        return HttpResponse(template.render(self.context))

class PropositionResponseApproveViewer(PropositionResponseViewer):
    accepted_item_type = PropositionResponseApprove
    viewer_name = 'propositionresponseapprove' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        template = loader.get_template('poll/propositionresponseapprove.html')
        return HttpResponse(template.render(self.context))

class DecisionViewer(ItemViewer):
    accepted_item_type = Decision
    viewer_name = 'decision' 
    
    
    

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        
        if issubclass(self.item.poll.actual_item_type(), ChooseNPoll):
            self.context['type'] = 'ChooseNPoll'
        
        if issubclass(self.item.poll.actual_item_type(), ApproveNPoll):
            self.context['type'] = 'ApproveNPoll'
        
        
        maxPollTakers = len(Membership.objects.all().filter(collection=self.item.poll.eligibles))
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        print responses
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,2):
                for response in aggResponses:
                    if aggResponses[response] > maxNum:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0
                
        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        template = loader.get_template('poll/decision.html')
        return HttpResponse(template.render(self.context))
        

class PluralityChooseNDecisionViewer(DecisionViewer):
    accepted_item_type = PluralityChooseNDecision
    viewer_name = 'pluralitychoosendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item

        maxPollTakers = len(Membership.objects.all().filter(collection=self.item.poll.eligibles))
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        template = loader.get_template('poll/pluralitychoosendecision.html')
        return HttpResponse(template.render(self.context))

class ThresholdChooseNDecisionViewer(DecisionViewer):
    accepted_item_type = ThresholdChooseNDecision
    viewer_name = 'thresholdchoosendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        pollTakers = Membership.objects.all().filter(collection=self.item.poll.eligibles)
        participants = Agent.objects.filter(poll_participant__poll=self.item.poll)
        minForDecision = int(math.ceil(len(participants) * (self.item.p_decision/100.0)))
        maxPollTakers = len(pollTakers)
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum and aggResponses[response] >= minForDecision:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        self.context['people'] = int(math.ceil(maxPollTakers * (self.item.p_decision/100.0)))
        self.context['participants'] = Agent.objects.filter(poll_participant__poll=self.item.poll)
        self.context['minpeoplefordecision'] = minForDecision
        template = loader.get_template('poll/thresholdchoosendecision.html')
        return HttpResponse(template.render(self.context))

class ThresholdEChooseNDecisionViewer(DecisionViewer):
    accepted_item_type = ThresholdEChooseNDecision
    viewer_name = 'thresholdechoosendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        pollTakers = Membership.objects.all().filter(collection=self.item.poll.eligibles)
        minForDecision = int(math.ceil(len(pollTakers) * (self.item.e_decision/100.0)))
        maxPollTakers = len(pollTakers)
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum and aggResponses[response] >= minForDecision:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        self.context['people'] = int(math.ceil(maxPollTakers * (self.item.e_decision/100.0)))
        self.context['minpeoplefordecision'] = minForDecision
        self.context['participants'] = Agent.objects.filter(poll_participant__poll=self.item.poll)
        
        template = loader.get_template('poll/thresholdechoosendecision.html')
        return HttpResponse(template.render(self.context))

class UnanimousChooseNDecisionViewer(DecisionViewer):
    accepted_item_type = UnanimousChooseNDecision
    viewer_name = 'unanimouschoosendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        pollTakers = Membership.objects.all().filter(collection=self.item.poll.eligibles)
        minForDecision = len(pollTakers) - self.item.m_decision
        maxPollTakers = len(pollTakers)
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum and aggResponses[response] >= minForDecision:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = minForDecision
        self.context['minpeoplefordecision'] = minForDecision
        self.context['participants'] = Agent.objects.filter(poll_participant__poll=self.item.poll)
        
        template = loader.get_template('poll/unanimouschoosendecision.html')
        return HttpResponse(template.render(self.context))

class PluralityApproveNDecisionViewer(DecisionViewer):
    accepted_item_type = PluralityApproveNDecision
    viewer_name = 'pluralityapprovendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item

        maxPollTakers = len(Membership.objects.all().filter(collection=self.item.poll.eligibles))
        responses = PropositionResponseApprove.objects.all().filter(poll=self.item.poll.pk).filter(value='approve')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        template = loader.get_template('poll/pluralityapprovendecision.html')
        return HttpResponse(template.render(self.context))

class ThresholdApproveNDecisionViewer(DecisionViewer):
    accepted_item_type = ThresholdApproveNDecision
    viewer_name = 'thresholdapprovendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        pollTakers = Membership.objects.all().filter(collection=self.item.poll.eligibles)
        participants = Agent.objects.filter(poll_participant__poll=self.item.poll)
        minForDecision = int(math.ceil(len(participants) * (self.item.p_decision/100.0)))
        maxPollTakers = len(pollTakers)
        responses = PropositionResponseApprove.objects.all().filter(poll=self.item.poll.pk).filter(value='approve')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum and aggResponses[response] >= minForDecision:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        self.context['people'] = int(math.ceil(maxPollTakers * (self.item.p_decision/100.0)))
        self.context['participants'] = participants 
        self.context['minpeoplefordecision'] = minForDecision
        template = loader.get_template('poll/thresholdapprovendecision.html')
        return HttpResponse(template.render(self.context))
        

class ThresholdEApproveNDecisionViewer(DecisionViewer):
    accepted_item_type = ThresholdEApproveNDecision
    viewer_name = 'thresholdeapprovendecision' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        pollTakers = Membership.objects.all().filter(collection=self.item.poll.eligibles)
        minForDecision = int(math.ceil(len(pollTakers) * (self.item.e_decision/100.0)))
        maxPollTakers = len(pollTakers)
        responses = PropositionResponseApprove.objects.all().filter(poll=self.item.poll.pk).filter(value='approve')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
                    print response
                    if str(response.pk) in aggResponses:
                        aggResponses[str(response.pk)] = aggResponses[str(response.pk)] + 1 
                    else:
                        aggResponses[str(response.pk)] = 1
                        maxNum = 0;
            for x in range(0,self.item.num_decision):
                for response in aggResponses:
                    if aggResponses[response] > maxNum and aggResponses[response] >= minForDecision:
                        mostPopular = response
                        maxNum = aggResponses[response]
                topChoices.append(mostPopular)
                aggResponses[mostPopular] = -1
                maxNum = 0

        if mostPopular:
            self.context['mostPopular'] = Proposition.objects.all().filter(pk__in=topChoices)
        self.context['maxPollTakers'] = maxPollTakers
        self.context['numResponses'] = len(responses)
        self.context['minResponses'] = int(math.ceil(maxPollTakers * (self.item.quorum/100.0)))
        self.context['people'] = int(math.ceil(maxPollTakers * (self.item.e_decision/100.0)))
        self.context['minpeoplefordecision'] = minForDecision
        self.context['participants'] = Agent.objects.filter(poll_participant__poll=self.item.poll)
        
        template = loader.get_template('poll/thresholdechoosendecision.html')
        return HttpResponse(template.render(self.context))

class WriteInPropositionsViewer(CollectionViewer):
    accepted_item_type = WriteInPropositions 
    viewer_name = 'writeinpropositions' 


    def item_show_html(self):
        dependencies = PropositionResponse.objects.all()

        self.context['responses'] = dependencies.filter(poll=self.item.pk)

        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True)
        memberships = memberships.filter(item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
        self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
        template = loader.get_template('poll/writein.html')
        return HttpResponse(template.render(self.context))



