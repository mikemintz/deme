from django.core.urlresolvers import reverse
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from cms.views import ItemViewer
from modules.discussionboard.models import *
from cms.models import *

class DiscussionViewer(ItemViewer):
    accepted_item_type = Item
    viewer_name = 'discussion'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('discussionboard/show.html')
        top_level_comments = list(TextComment.objects.filter(item=self.item, active=True))
        last_posts = {}
        num_replies = {}
        for top_level_comment in top_level_comments:
            all_replies = TextComment.objects.filter(pk__in=RecursiveComment.objects.filter(parent=top_level_comment).values('child').query, active=True)
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
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_item.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
        redirect = reverse('item_url', kwargs={'viewer': 'discussion', 'action': 'show', 'noun': self.item.pk})
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
        permissions = self._get_permissions_from_post_data(self.accepted_item_type, 'one')
        new_item.save_versioned(action_agent=self.cur_agent, initial_permissions=permissions)
        redirect = self.request.GET['redirect']
        return HttpResponseRedirect(redirect)


class DiscussionBoardViewer(DiscussionViewer):
    accepted_item_type = DiscussionBoard
    viewer_name = 'discussionboard'


class DiscussionCommentViewer(ItemViewer):
    accepted_item_type = Comment
    viewer_name = 'discussioncomment'

    def item_show_html(self):
        self.context['action_title'] = ''
        template = loader.get_template('discussionboard/viewdiscussion.html')
        discussion_board = Item.objects.get(pk=self.request.GET['discussion_board'])
        self.context['discussion_board'] = discussion_board
        return HttpResponse(template.render(self.context))

