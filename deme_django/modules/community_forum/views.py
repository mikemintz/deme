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
            #url = 'https://air-min.webex.com/p.php?AT=LI&WID=%s' % webex_id
            url = webex_id
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

    def type_loginmenuitem_html(self):
        self.context['redirect'] = self.request.GET.get('redirect', '')
        template = loader.get_template('communityforumparticipant/loginmenuitem.html')
        return HttpResponse(template.render(self.context))

    def type_rememberfontsize_json(self):
        font_size = self.request.REQUEST['font_size']
        self.request.session['communityforumfontsize'] = font_size
        return HttpResponse('')


class DiscussionBoardViewer(ItemViewer):
    accepted_item_type = DiscussionBoard
    viewer_name = 'discussionboard'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('discussionboard/show.html')
        top_level_comments = list(TextComment.objects.filter(item=self.item))
        last_posts = {}
        num_replies = {}
        for top_level_comment in top_level_comments:
            all_replies = TextComment.objects.filter(pk__in=RecursiveComment.objects.filter(parent=top_level_comment).values('child').query)
            for reply in all_replies.order_by('-created_at')[:1]:
                last_posts[top_level_comment] = reply
            num_replies[top_level_comment] = all_replies.count()
        top_level_comments.sort(key=lambda x: last_posts.get(x, x).created_at)
        top_level_comments.reverse()
        self.context['discussions'] = [{'comment':x, 'last_post':last_posts.get(x), 'num_replies':num_replies[x]} for x in top_level_comments]
        return HttpResponse(template.render(self.context))

    def item_newdiscussion_html(self):
        self.require_global_ability('create TextComment')
        self.require_ability('comment_on', self.item)
        self.context['action_title'] = 'Create new discussion'
        template = loader.get_template('discussionboard/newdiscussion.html')
        return HttpResponse(template.render(self.context))

    def item_creatediscussion_html(self):
        self.require_global_ability('create TextComment')
        self.require_ability('comment_on', self.item)
        new_item = TextComment()
        new_item.name = self.request.POST['name']
        new_item.body = self.request.POST['body']
        new_item.item = self.item
        new_item.item_version_number = self.item.version_number
        new_item.save_versioned(action_agent=self.cur_agent)
        redirect = self.item.get_absolute_url()
        return HttpResponseRedirect(redirect)

    def item_createreply_html(self):
        self.require_global_ability('create TextComment')
        parent = Item.objects.get(pk=self.request.POST['item'])
        self.require_ability('comment_on', parent)
        new_item = TextComment()
        new_item.name = self.request.POST['name']
        new_item.body = self.request.POST['body']
        new_item.item = parent
        new_item.item_version_number = self.request.POST['item_version_number']
        new_item.save_versioned(action_agent=self.cur_agent)
        redirect = self.request.GET['redirect']
        return HttpResponseRedirect(redirect)


class DiscussionBoardCommentViewer(ItemViewer):
    accepted_item_type = Comment
    viewer_name = 'discussionboardcomment'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('discussionboard/viewdiscussion.html')
        discussion_board = DiscussionBoard.objects.get(pk=self.request.GET['discussion_board'])
        self.context['discussion_board'] = discussion_board
        return HttpResponse(template.render(self.context))

