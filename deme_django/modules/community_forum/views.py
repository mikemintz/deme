from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from cms.views import PersonViewer, ItemViewer
from modules.community_forum.models import *

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

class DiscussionBoardViewer(ItemViewer):
    accepted_item_type = DiscussionBoard
    viewer_name = 'discussionboard'

    def item_show_html(self):
        self.context['action_title'] = 'View ongoing discussions'
        self.context['no_side_comment_box'] = True
        template = loader.get_template('discussionboard/show.html')
        return HttpResponse(template.render(self.context))
