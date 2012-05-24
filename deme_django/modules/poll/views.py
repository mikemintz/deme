from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from cms.views import HtmlDocumentViewer, CollectionViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.poll.models import Poll, Proposition, PropositionResponse, Decision, PropositionResponseChoose, PropositionResponseApprove, ChooseNPoll, ApproveNPoll, UnanimousChooseNDecision
from modules.poll.models import PluralityChooseNDecision, ThresholdChooseNDecision, ThresholdEChooseNDecision, PluralityApproveNDecision, ThresholdApproveNDecision, ThresholdEApproveNDecision
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time
import math
import csv
import cStringIO as StringIO


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
    
    def verifyCurAgentIsEligible(self):
        if not self.item.agent_eligible_to_vote(self.cur_agent):
            return self.render_error('Not an eligible agent', "You are not permitted to vote on this poll")
     
            
class ChooseNPollViewer(PollViewer):
    accepted_item_type = ChooseNPoll
    viewer_name = 'choosenpoll' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['responses'] = PropositionResponseChoose.objects.filter(poll=self.item)
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseChoose.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        self.context['responses'] = responses
        self.context['decisions'] = Decision.objects.filter(poll=self.item)
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        self.context['can_view_response_names'] = self.item.visibility != 'closed' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['can_view_response_names_and_values'] = self.item.visibility == 'responses visible' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['cur_agent_in_eligbles'] = self.item.agent_eligible_to_vote(self.cur_agent)
        self.context['cur_agent_can_make_a_decision'] = self.permission_cache.agent_can_global('create ThresholdChooseNDecision') or self.permission_cache.agent_can_global('create ThresholdEChooseNDecision')  or self.permission_cache.agent_can_global('create PluralityChooseNDecision') or self.permission_cache.agent_can_global('create UnanimousChooseNDecision')
        template = loader.get_template('poll/choosenpoll.html')
        return HttpResponse(template.render(self.context))
    
    def item_respondtopropositions_html(self):
        propositions = self.request.POST
        #verify that the cur agent is in the eligbles
        self.verifyCurAgentIsEligible()
        #verify that it is not before or after the deadline

        #verify that there are only n or less responses
        counter=0
        for response in propositions:    
            if propositions[response]=="chosen":
                counter=counter+1
        if counter!=self.item.n: #this needs to be changed for chooseN
            return self.render_error('Incorect input of votes', "Choose "+str(self.item.n)+".")

        #delete old response (even if one doesn't exist)
        PropositionResponseChoose.objects.filter(poll=self.item, participant=self.cur_agent).delete()
        #make a new response
        for response in propositions:
            newResponse = PropositionResponseChoose(poll=self.item, participant= self.cur_agent, proposition = Proposition.objects.get(pk=response), value = propositions[response])
            newResponse.save()
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    

        

class ApproveNPollViewer(PollViewer):
    accepted_item_type = ApproveNPoll
    viewer_name = 'approvenpoll' 


    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['responses'] = PropositionResponseApprove.objects.filter(poll=self.item)
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseApprove.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        self.context['responses'] = responses
        self.context['decisions'] = Decision.objects.filter(poll=self.item)
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        self.context['can_view_response_names'] = self.item.visibility != 'closed' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['can_view_response_names_and_values'] = self.item.visibility == 'responses visible' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['cur_agent_in_eligbles'] = self.item.agent_eligible_to_vote(self.cur_agent)
        self.context['cur_agent_can_make_a_decision'] = self.permission_cache.agent_can_global('create ThresholdApproveNDecision') or self.permission_cache.agent_can_global('create ThresholdEApproveNDecision')  or self.permission_cache.agent_can_global('create PluralityApproveNDecision') 
        cur_agent_has_voted = PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent)
        self.context['cur_agent_has_voted'] = cur_agent_has_voted
        vote_numbers = []
        propositions = Proposition.objects.filter(memberships__in=memberships)
        maxNumber = 0
        for proposition in propositions:
            agree = PropositionResponseApprove.objects.filter(poll=self.item, value='approve', proposition=proposition).count()
            disagree = PropositionResponseApprove.objects.filter(poll=self.item, value='disapprove', proposition=proposition).count()
            #no_vote = PropositionResponseApprove.objects.filter(poll=self.item, value='not sure', proposition=proposition).count()
            #maxTemp = max([agree, disagree, no_vote])
            no_vote = 12-agree-disagree
            #if(maxTemp > maxNumber): maxNumber = maxTemp
            vote_numbers.append({'agree': agree, 'agreeList': range(agree), 'disagree': disagree, 'disagreeList': range(disagree), 'no_vote':no_vote, 'no_voteList':range(no_vote), 'proposition': proposition})
        
        #self.context['maxVal'] = maxNumber
        self.context['vote_numbers_list'] = vote_numbers
        self.context['comments'] = TextComment.objects.filter(item=self.item)
        template = loader.get_template('poll/approvenpoll.html')
        return HttpResponse(template.render(self.context))

    def item_respondtopropositions_html(self):
        cur_agent_has_voted = PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent)
        if cur_agent_has_voted: return self.render_error('Duplicate Voting', "You have already voted in this poll")
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        propositions = Proposition.objects.filter(memberships__in=memberships)
        proposition_responses = {}
        for proposition in propositions:
            proposition_responses[proposition.pk] = self.request.POST[str(proposition.pk)]
        writein = self.request.POST['optional_writein_comment']
        #verify that the cur agent is in the eligbles
        self.verifyCurAgentIsEligible()
        #verify that it is not before or after the deadline

        #verify no duplicate rankings
        #usedVals = []
        #for value in proposition_responses.values():
        #    if value in usedVals:
        #        return self.render_error('Invalid Ranking', "You cannot have duplicate rankings.")
        #    else:
        #        usedVals.append(value)

        
        #verify that there are only n or less responses
        #counter=0
        #for response in propositionResponses:    
        #    if propositionResponses[response]=="approve" or propositionResponses[response]=="disapprove":
        #       counter=counter+1
        #        if counter>self.item.n: #this needs to be changed for chooseN
        #            return self.render_error('Too many votes', "Approve "+str(self.item.n)+" or fewer propositions.")
        if len(propositionResponses) != 3:
            return self.render_error('Not all statements responded to.', "Please agree or disagree with each statement")            
        #delete old response (even if one doesn't exist)
        #PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent).delete()
        #make a new response
        for response in proposition_responses:
            newResponse = PropositionResponseApprove(poll=self.item, participant= self.cur_agent, proposition = Proposition.objects.get(pk=response), value = proposition_responses[response])
            newResponse.save()
        
        if writein:
            newComment = TextComment(item=self.item, item_version_number=self.item.version_number, body=writein)
            newComment.save_versioned(action_agent=self.cur_agent, initial_permissions=[OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)])

        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        self.context['can_view_response_names_and_values'] = self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['cur_agent_in_eligbles'] = self.item.agent_eligible_to_vote(self.cur_agent)
        self.context['cur_agent_can_make_a_decision'] = self.permission_cache.agent_can_global('create ThresholdApproveNDecision') or self.permission_cache.agent_can_global('create ThresholdEApproveNDecision')  or self.permission_cache.agent_can_global('create PluralityApproveNDecision') 
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseApprove.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        
        vote_numbers = []
        maxNumber = 0
        for proposition in propositions:
            agree = PropositionResponseApprove.objects.filter(poll=self.item, value='approve', proposition=proposition).count()
            disagree = PropositionResponseApprove.objects.filter(poll=self.item, value='disapprove', proposition=proposition).count()
            #no_vote = PropositionResponseApprove.objects.filter(poll=self.item, value='not sure', proposition=proposition).count()
            #maxTemp = max([agree, disagree, no_vote])
            #if(maxTemp > maxNumber): maxNumber = maxTemp
            no_vote = 12-agree-disagree
            #if(maxTemp > maxNumber): maxNumber = maxTemp
            vote_numbers.append({'agree': agree, 'agreeList': range(agree), 'disagree': disagree, 'disagreeList': range(disagree), 'no_vote':no_vote, 'no_voteList':range(no_vote), 'proposition': proposition})

        #self.context['maxVal'] = maxNumber
        self.context['vote_numbers_list'] = vote_numbers
        self.context['comments'] = TextComment.objects.filter(item=self.item)
        
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def item_addawritein_html(self):

        writein = self.request.POST['optional_writein_comment']
        if writein:
            newComment = TextComment(item=self.item, item_version_number=self.item.version_number, body=writein)
            newComment.save_versioned(action_agent=self.cur_agent, initial_permissions=[OneToOnePermission(source=self.cur_agent, ability='do_anything', is_allowed=True)])
        self.context['comments'] = TextComment.objects.filter(item=self.item)
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)


class PropositionViewer(HtmlDocumentViewer):
    accepted_item_type = Proposition
    viewer_name = 'proposition' 

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        template = loader.get_template('poll/proposition.html')
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
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
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
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        maxPollTakers = len(Membership.objects.all().filter(collection=self.item.poll.eligibles))
        responses = PropositionResponseChoose.objects.all().filter(poll=self.item.poll.pk).filter(value='chosen')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
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
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
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
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
            
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
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
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
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        maxPollTakers = len(Membership.objects.all().filter(collection=self.item.poll.eligibles))
        responses = PropositionResponseApprove.objects.all().filter(poll=self.item.poll.pk).filter(value='approve')
        mostPopular = None
        topChoices = []
        if responses:
            aggResponses = {}
            for response in responses:
                if response.proposition:
                    response = response.proposition
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
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
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
        self.context['action_title'] = 'Show'
        self.context['item'] = self.item
        memberships = self.item.poll.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
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
        
        template = loader.get_template('poll/thresholdeapprovendecision.html')
        return HttpResponse(template.render(self.context))

# class WriteInPropositionsViewer(CollectionViewer):
#     accepted_item_type = WriteInPropositions 
#     viewer_name = 'writeinpropositions' 
# 
# 
#     def item_show_html(self):
#         dependencies = PropositionResponse.objects.all()
# 
#         self.context['responses'] = dependencies.filter(poll=self.item.pk)
# 
#         from cms.forms import AjaxModelChoiceField
#         self.context['action_title'] = ''
#         self.require_ability('view ', self.item, wildcard_suffix=True)
#         memberships = self.item.child_memberships
#         memberships = memberships.filter(active=True)
#         memberships = memberships.filter(item__active=True)
#         memberships = self.permission_cache.filter_items('view Membership.item', memberships)
#         memberships = memberships.select_related('item')
#         if memberships:
#             self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
#         self.context['memberships'] = sorted(memberships, key=lambda x: (not self.permission_cache.agent_can('view Item.name', x.item), x.item.name))
#         self.context['cur_agent_in_collection'] = bool(self.item.child_memberships.filter(active=True, item=self.cur_agent))
#         template = loader.get_template('poll/writein.html')
#         return HttpResponse(template.render(self.context))
class ODPSurveyViewer(PollViewer):
    accepted_item_type = ApproveNPoll
    viewer_name = 'odpsurvey'

    def item_show_html(self):
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        if memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in memberships]))
        self.context['responses'] = PropositionResponseApprove.objects.filter(poll=self.item)
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseApprove.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        self.context['responses'] = responses
        self.context['decisions'] = Decision.objects.filter(poll=self.item)
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        self.context['can_view_response_names'] = self.item.visibility != 'closed' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['can_view_response_names_and_values'] = self.item.visibility == 'responses visible' or self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['cur_agent_in_eligibles'] = self.item.agent_eligible_to_vote(self.cur_agent)
        self.context['cur_agent_can_make_a_decision'] = self.permission_cache.agent_can_global('create ThresholdApproveNDecision') or self.permission_cache.agent_can_global('create ThresholdEApproveNDecision')  or self.permission_cache.agent_can_global('create PluralityApproveNDecision') 
        cur_agent_has_voted = PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent)
        self.context['cur_agent_has_voted'] = cur_agent_has_voted
        vote_numbers = []
        propositions = Proposition.objects.filter(memberships__in=memberships)
        maxNumber = 0
        for proposition in propositions:
            disagreeStrong = PropositionResponseApprove.objects.filter(poll=self.item, value='no vote', proposition=proposition).count()
            agree = PropositionResponseApprove.objects.filter(poll=self.item, value='approve', proposition=proposition).count()
            agreeStrong = PropositionResponseApprove.objects.filter(poll=self.item, value='disapprove', proposition=proposition).count()
            disagree = PropositionResponseApprove.objects.filter(poll=self.item, value='not sure', proposition=proposition).count()
            vote_numbers.append({'agree': agree, 'disagree': disagree, 'agreeStrong': agreeStrong, "disagreeStrong": disagreeStrong})
        
        self.context['maxVal'] = maxNumber
        self.context['vote_numbers_list'] = vote_numbers
        self.context['comments'] = TextComment.objects.filter(item=self.item)
        template = loader.get_template('poll/odpSurvey.html')
        return HttpResponse(template.render(self.context))

    def item_respondtopropositions_html(self):
        cur_agent_has_voted = PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent)
        if cur_agent_has_voted: return self.render_error('Duplicate Voting', "You have already voted in this poll")
        from cms.forms import AjaxModelChoiceField
        self.context['action_title'] = ''
        self.require_ability('view ', self.item, wildcard_suffix=True)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        propositions = Proposition.objects.filter(memberships__in=memberships)
        proposition_responses = {}
        for proposition in propositions:
            proposition_responses[proposition.pk] = self.request.POST[str(proposition.pk)]
        #verify that the cur agent is in the eligbles
        self.verifyCurAgentIsEligible()
        #verify that it is not before or after the deadline
        
        #verify that there are only n or less responses
        #counter=0
        #for response in propositionResponses:    
        #    if propositionResponses[response]=="approve" or propositionResponses[response]=="disapprove":
        #       counter=counter+1
        #        if counter>self.item.n: #this needs to be changed for chooseN
        #            return self.render_error('Too many votes', "Approve "+str(self.item.n)+" or fewer propositions.")
                    
        #delete old response (even if one doesn't exist)
        #PropositionResponseApprove.objects.filter(poll=self.item, participant=self.cur_agent).delete()
        #make a new response
        for response in proposition_responses:
            newResponse = PropositionResponseApprove(poll=self.item, participant= self.cur_agent, proposition = Proposition.objects.get(pk=response), value = proposition_responses[response])
            newResponse.save()
        
        self.context['propositions'] = Proposition.objects.filter(memberships__in=memberships)
        self.context['can_view_response_names_and_values'] = self.permission_cache.agent_can('access_proposition_responses', self.item)
        self.context['cur_agent_in_eligbles'] = self.item.agent_eligible_to_vote(self.cur_agent)
        self.context['cur_agent_can_make_a_decision'] = self.permission_cache.agent_can_global('create ThresholdApproveNDecision') or self.permission_cache.agent_can_global('create ThresholdEApproveNDecision')  or self.permission_cache.agent_can_global('create PluralityApproveNDecision') 
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseApprove.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        
        vote_numbers = []
        maxNumber = 0
        for proposition in propositions:
            disagreeStrong = PropositionResponseApprove.objects.filter(poll=self.item, value='no vote', proposition=proposition).count()
            agree = PropositionResponseApprove.objects.filter(poll=self.item, value='approve', proposition=proposition).count()
            agreeStrong = PropositionResponseApprove.objects.filter(poll=self.item, value='disapprove', proposition=proposition).count()
            disagree = PropositionResponseApprove.objects.filter(poll=self.item, value='not sure', proposition=proposition).count()
            vote_numbers.append({'agree': agree, 'disagree': disagree, 'agreeStrong': agreeStrong, "disagreeStrong": disagreeStrong})

        self.context['vote_numbers_list'] = vote_numbers
        self.context['comments'] = TextComment.objects.filter(item=self.item)
        
        redirect = self.request.GET.get('redirect', reverse('item_url', kwargs={'viewer': self.viewer_name, 'noun': self.item.pk}))
        return HttpResponseRedirect(redirect)

    def item_createcsv_html(self):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=SurveyResults.csv'
        
        eligible_agent_memberships = self.item.eligibles.child_memberships
        eligible_agent_memberships = eligible_agent_memberships.filter(active=True, item__active=True)
        eligible_agent_memberships = self.permission_cache.filter_items('view Membership.item', eligible_agent_memberships)
        eligible_agent_memberships = eligible_agent_memberships.select_related('item')
        if eligible_agent_memberships:
            self.permission_cache.filter_items('view Item.name', Item.objects.filter(pk__in=[x.item_id for x in eligible_agent_memberships]))
        responses = {}
        for agent_membership in eligible_agent_memberships:
            responses[agent_membership.item] = PropositionResponseApprove.objects.filter(poll=self.item).filter(participant=agent_membership.item)
        memberships = self.item.child_memberships
        memberships = memberships.filter(active=True, item__active=True)
        memberships = self.permission_cache.filter_items('view Membership.item', memberships)
        memberships = memberships.select_related('item')
        propositions = Proposition.objects.filter(memberships__in=memberships)

        propList = ['Propositions']
        for proposition in propositions:
            propList.append(proposition.name)

        writer = csv.writer(response)
        writer.writerow(propList)

        for key,value in responses.items():
            chunk = []
            chunk.append(key.name)
            for resp in value:
                if resp.value=="no vote": answer = "Disagree Strongly"
                if resp.value=="not sure": answer = "Disagree"
                if resp.value=="approve": answer = "Agree"
                if resp.value=="disapprove": answer = "Agree Strongly"
                chunk.append(answer)
            writer.writerow(chunk)

        
    
        return response


