from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from cms.views import PersonViewer
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
