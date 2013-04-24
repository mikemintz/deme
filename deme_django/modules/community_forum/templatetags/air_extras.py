from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from cms.models import *
from django.utils.http import urlquote
from django.utils.html import escape
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import truncate_words
from django.utils.safestring import mark_safe
from cms.templatetags.item_tags import *
from modules.community_forum.views import CommunityForumParticipantViewer

register = template.Library()

class CommunityForumCalculateComments(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<CalculateCommentsNode>"

    def render(self, context):
        item = context['item']
        version_number = item.version_number
        full_path = context['full_path']
        result = []
        def add_comment_to_div(comment_info, parents):
            comment = comment_info['comment']
            if agentcan_helper(context, 'view TextDocument.body', comment):
                comment_body = escape(comment.body).replace('\n', '<br />')
            else:
                comment_body = ''
            result.append(u'<div style="margin-bottom: 5px; padding: 5px; border: 2px solid #000; background-color: #%s">' % ('def' if len(parents) == 0 else 'eee' if len(parents) % 2 == 0 else 'fff'))
            if agentcan_helper(context, 'view Item.creator', comment):
                result.append('<div style="font-weight: bold;">%s</div>' % get_viewable_name(context, comment.creator))
            result.append(u'<div>%s</div>' % comment_body)
            result.append(u'</div>')
            result.append(u'<div id="comment%s" style="display: none;"><form onsubmit="if (this[\'body\'].value.trim() == \'\') { alert(\'You must fill out a body for your reply\'); return false; } return true;" method="post" action="%s?redirect=%s">'% (comment.pk, reverse('item_url', kwargs={'viewer': 'discussion', 'noun': context['discussion_board'].pk, 'action': 'createreply'}), urlquote(full_path)))
            result.append(u'<input name="name" type="hidden" value="Re: %s" /><div><textarea name="body" style="height: 100px; width: 100%%;"></textarea></div>' % (comment.name))
            result.append(u'<div><input type="submit" value="Submit reply" /></div><input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" />' % (comment.pk, comment.version_number))
            result.append(u'</form></div>')
            result.append(u'<div style="margin-bottom: 10px;">')
            result.append(u'<div style="float: right;"><a href="#" onclick="$(\'#comment%s\').show(); return false;" class="fg-button ui-widget ui-state-default fg-button-icon-left ui-corner-all" style="background: #ffcc99;"><span class="ui-icon ui-icon-comment"></span>Reply</a></div>' % comment.pk)
            if agentcan_helper(context, 'view Item.created_at', comment):
                result.append('<div style="font-style: italic;">%s</div>' % comment.created_at.strftime("%a %b %d %Y %I:%M %p"))
            result.append(u'<div style="clear: both;"></div>')
            result.append(u'</div>')
            if len(parents) == 0:
                result.append(u'<div style="border-bottom: 2px solid #000; margin-top: 10px; margin-bottom: 15px;"></div>')
            for subcomment in reversed(sorted(comment_info['subcomments'], key=lambda x: x['comment'].created_at)):
                result.append(u'<div style="margin-left: 50px;">')
                add_comment_to_div(subcomment, parents + (comment_info,))
                result.append(u'</div>')
        comment_dicts, n_comments = comment_dicts_for_item(item.item, version_number, context, isinstance(item, Collection))
        for comment_dict in comment_dicts:
            if comment_dict['comment'].pk == item.pk:
                add_comment_to_div(comment_dict, ())
        return mark_safe('\n'.join(result))

@register.tag
def communityforum_calculatecomments(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CommunityForumCalculateComments()


class SimpleLoginMenu(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<SimpleLoginMenu>"

    def render(self, context):
        viewer = context['_viewer']
        result = []

        if viewer.cur_agent.is_anonymous():
            login_menu_text = 'Login'
        else:
            login_menu_text = u'Click here to log out <!-- %s -->' % get_viewable_name(context, viewer.cur_agent)

        result.append("""
        <script type="text/javascript">
        $(function(){
            var menuContent = '<ul style="font-size: 85%%;">';
            $.each($('#login_menu_link').next().children().filter('li.loginmenuitem'), function(i, val){
                menuContent += '<li>' + $(val).html() + '</li>';
            });
            menuContent += '</ul>'
            $('#login_menu_link').fgmenu({
                content: menuContent,
                showSpeed: 50,
                fixedPosition: true,
            });
            $('#login_menu_link').click(function(){
                $("#simple_login_menu_ul a").trigger('click');
                return false;
            });
        });
        </script>
        <a href="#" class="fg-button ui-widget ui-state-default ui-corner-all" id="login_menu_link">%s</a>
        <ul id="simple_login_menu_ul" style="display: none;">
        """ % login_menu_text)
        for viewer_class in [CommunityForumParticipantViewer]:
            viewer2 = viewer_class()
            if viewer.request.method == 'GET':
                query_string = 'redirect=%s' % urlquote(viewer.context['full_path'])
            else:
                query_string = ''
            viewer2.init_for_div(viewer, 'loginmenuitem', None, query_string)
            html = viewer2.dispatch().content
            result.append(html)
        result.append("</ul>")
        return '\n'.join(result)

@register.tag
def simple_login_menu(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return SimpleLoginMenu()

class InitialFontSize(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<InitialFontSize>"

    def render(self, context):
        viewer = context['_viewer']
        return viewer.request.session.get('communityforumfontsize', "85%")

@register.tag
def initial_font_size(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return InitialFontSize()


class IfAirGroup(template.Node):
    def __init__(self, ids, nodelist_in, nodelist_out):
        self.ids = [template.Variable(x) for x in ids]
        self.nodelist_in, self.nodelist_out = nodelist_in, nodelist_out

    def __repr__(self):
        return "<IfAirGroup>"

    def render(self, context):
        try:
            ids = [x.resolve(context) for x in self.ids]
        except template.VariableDoesNotExist:
            if settings.DEBUG:
                return "[Couldn't resolve ids variable]"
            else:
                return '' # Fail silently for invalid variables.
        viewer = context['_viewer']
        print ids
        in_group = RecursiveMembership.objects.filter(parent__in=ids, child=viewer.cur_agent).exists()
        nodelist = self.nodelist_in if in_group else self.nodelist_out
        return nodelist.render(context)

@register.tag
def ifairgroup(parser, token):
    bits = list(token.split_contents())
    end_tag = 'end' + bits[0]
    nodelist_in = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_out = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_out = template.NodeList()
    return IfAirGroup(bits[1:], nodelist_in, nodelist_out)
