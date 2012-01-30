from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from cms.views import PersonViewer, ItemViewer
from modules.community_forum.models import *
from cms.models import *

class CommunityForumParticipantViewer(PersonViewer):
    accepted_item_type = CommunityForumParticipant
    viewer_name = 'communityforumparticipant'

    def type_webexlogin_html(self):
        participant = self.cur_agent.downcast()
        if isinstance(participant, CommunityForumParticipant):
            webex_id = participant.webex_id
            url = 'https://air-min.webex.com/p.php?AT=LI&WID=%s' % webex_id
            return HttpResponseRedirect(url)
        else:
            return self.render_error('Not a participant', "You must be a CommunityForumParticipant to access this")
    
    def type_gotomydiscussionboard_html(self):
        my_groups = Group.objects.filter(active=True, pk__in=self.cur_agent.memberships.values('collection').query)
        if(len(my_groups)!=1): return self.render_error('Multiple Group Memberships', "Agent can only be in one group")
        my_group = my_groups[0]
        my_folio = my_group.folios.all()[0]
        my_discussionboards = DiscussionBoard.objects.filter(pk__in=my_folio.all_contained_collection_members())
        if(len(my_discussionboards)==0): return self.render_error('No discusson board', "Your Group does not have an associated Discussion Board")
        my_discussionboard = my_discussionboards[0]
        return HttpResponseRedirect(my_discussionboard.get_absolute_url())

    def type_gotomypoll_html(self):
        my_groups = Group.objects.filter(active=True, pk__in=self.cur_agent.memberships.values('collection').query)
        if(len(my_groups)!=1): return self.render_error('Multiple Group Memberships', "Agent can only be in one group")
        my_group = my_groups[0]
        my_folio = my_group.folios.all()[0]
        my_polls = Poll.objects.filter(pk__in=my_folio.all_contained_collection_members())
        if(len(my_polls)==0): return self.render_error('No Poll', "Your Group does not have an associated Poll")
        my_poll = my_polls[0]
        return HttpResponseRedirect(my_poll.get_absolute_url())


class DiscussionBoardViewer(ItemViewer):
    accepted_item_type = DiscussionBoard
    viewer_name = 'discussionboard'

    def item_show_html(self):
        self.context['action_title'] = 'View ongoing discussions'
        self.context['no_side_comment_box'] = True
        template = loader.get_template('discussionboard/show.html')
        return HttpResponse(template.render(self.context))
