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
        from cms.forms import CaptchaField 
        from cms.forms import AjaxModelChoiceField
        item = context['item']
        version_number = item.version_number
        full_path = context['full_path']
        try:
            default_from_contact_method_pk = EmailContactMethod.objects.filter(agent=context['cur_agent'])[:1].get().pk
        except ObjectDoesNotExist:
            default_from_contact_method_pk = None
        result = []
        result.append(u'<div class="comment_box">')
        result.append(u'<div class="comment_box_header">')
        if agentcan_helper(context, 'comment_on', item):
            result.append(u'<div style="font-weight: bold; font-size: larger;">Ongoing discussions</div><div><a href="#" onclick="openCommentDialog(\'comment%s\'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-comment"></span>Create a new discussion</a></div>' % item.pk)
            result.append(u'<div id="comment%s" style="display: none;"><form method="post" action="%s?redirect=%s">'% (item.pk, reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'accordioncreate'}), urlquote(full_path)))
            result.append(u'<p>Discussion subject: <input name="title" type="text" size="35" maxlength="255" /></p><p>Body: <br><textarea name="comment_body" style="height: 200px; width: 250px;"></textarea> ')
            if context['cur_agent'].is_anonymous():
                result.append(u'To verify you are not a spammer, please enter in "abc123" <input name="simple_captcha" type="text" size="25" />')
            result.append(u'<div id="advancedcomment%s" style="display: none;">Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br> From Contact Method: %s</div><br> ' % (item.pk, AjaxModelChoiceField(ContactMethod.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('new_from_contact_method', default_from_contact_method_pk, {'id':'commentajaxfield'})))
            result.append(u' <input type="submit" value="Submit" /> <input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" /> ' % (item.pk, item.version_number))
            result.append(u'<a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv(\'advancedcomment%s\'); return false;">Advanced</a> ' % (item.pk))
            result.append(u'</form></div>')
        result.append(u'<div style="clear: both;"></div>')
        result.append(u'</div>')
        def add_comment_to_div(comment_info, parents):
            comment = comment_info['comment']
            transclusions_to = []
            for node in parents + (comment_info,):
                transclusions_to.extend(node['transclusions_to'])
            relevant_transclusions = [x for x in transclusions_to if x.from_item_version_number == x.from_item.version_number]
            relevant_transclusions.sort(key=lambda x: (x.to_item_id != comment.pk, x.from_item_id == item.pk, x.from_item_index))
            for node in parents + (comment_info,):
                if node['siblings'][-1]['comment'].pk == node['comment'].pk:
                    result.append(u'<div class="subcomments_last">')
                else:
                    result.append(u'<div class="subcomments">')
            original_comment = parents[0]['comment'] if parents else comment
            result.append(u'<div id="comment%s" style="display: none;"><form method="post" action="%s?redirect=%s">'% (comment.pk, reverse('item_type_url', kwargs={'viewer': 'textcomment', 'action': 'accordioncreate'}), urlquote(full_path)))
            result.append(u'<input name="title" type="hidden" value="Re: %s" /><p>Body: <br><textarea name="comment_body" style="height: 200px; width: 250px;"></textarea> </p> ' % (comment.name))
            if context['cur_agent'].is_anonymous():
                result.append(u'To verify you are not a spammer, please enter in "abc123" <input name="simple_captcha" type="text" size="25" />')
            result.append(u'<div id="advancedcomment%s" style="display: none;">Action Summary: <input name="actionsummary" type="text" size="25" maxlength="255" /><br> From Contact Method: %s</div><br> ' % (comment.pk, AjaxModelChoiceField(ContactMethod.objects, permission_cache=context['_viewer'].permission_cache, required_abilities=[]).widget.render('new_from_contact_method', default_from_contact_method_pk)))
            result.append(u' <input type="submit" value="Submit" /> <input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" /> ' % (comment.pk, comment.version_number))
            result.append(u'<a href="#" style="float: right; font-size: 9pt;" onclick="displayHiddenDiv(\'advancedcomment%s\'); return false;">Advanced</a> ' % (comment.pk))
            result.append(u'</form></div>')
            result.append(u'<div style="position: relative;">')
            result.append(u'<div style="position: absolute; top: 10px; left: 0; width: 20px; border-top: 2px dotted #bbb;"></div>')
            if comment_info['subcomments']:
                result.append(u'<div style="position: absolute; top: 1px; left: -10px; border: 2px solid #bbb; background: #fff; width: 15px; height: 15px; text-align: center; vertical-align: middle; font-size: 12px; font-weight: bold;"></div>')
            result.append(u'</div>')
            result.append(u'<div class="comment_header" id="right_pane_comment_%d">' % comment.pk)
            result.append(u'<div style="position: relative;"><div style="position: absolute; top: 0; left: 0;">')
            if original_comment.item.pk == item.pk:
                #TODO point to all transclusions
                transclusion = relevant_transclusions[0] if relevant_transclusions else None
                if context.get('in_textdocument_show', False):
                    if transclusion:
                        transclusion_html_id = ('' if transclusion.to_item_id == comment.pk else 'replies') + ('%d' % transclusion.pk)
                        result.append(u'<a href="#" onclick="highlight_comment(\'%s\', \'%s\', true, false); return false;">' % (comment.pk, transclusion_html_id))
                    else:
                        result.append(u'<a href="#" onclick="highlight_comment(\'%s\', null, false, false); return false;">' % comment.pk)
                else:
                    result.append(u'<a href="#" onclick="return false;">')
            else:
                itemref_url = '%s?crumb_filter=recursive_memberships_as_child.parent.%d' % (original_comment.item.get_absolute_url(), item.pk)
                result.append(u'<a href="%s">' % itemref_url)
            result.append(u'</a>')
            result.append(u'</div></div>')
            result.append(u'<div style="margin-left: 7px; padding-left: 19px;%s">' % (' border-left: 2px dotted #bbb;' if comment_info['subcomments'] else ''))
            if comment.active:
                if agentcan_helper(context, 'view Item.name', comment):
                    comment_name = escape(truncate_words(comment.display_name(), 8))
                else:
                    comment_name = comment.display_name(can_view_name_field=False)
                if agentcan_helper(context, 'view TextDocument.body', comment):
                    comment_body = escape(truncate_words(comment.body, 8))
                else:
                    comment_body = ''
            else:
                comment_name = '(Inactive comment)'
                comment_body = ''
            result.append(u'<a href="#" onclick="$(\'#comment_body%s\').toggle(); return false;"><b>%s</b></a><span style="color: #888;">%s</span>' % (comment.pk, comment_name, ' - ' + comment_body if comment_body.strip() else ''))
            if agentcan_helper(context, 'view Item.created_at', comment):
                result.append(comment.created_at.strftime("Posted on %m/%d/%Y"))
            if agentcan_helper(context, 'view Item.creator', comment):
                result.append('By %s' % get_viewable_name(context, comment.creator))
            if comment.version_number > 1:
                result.append(' (updated)')
            result.append(u'</div>')
            result.append(u'</div>')
            for i in xrange(len(parents) + 1):
                result.append(u'</div>')
            transclusion_text = ''
            for transclusion in relevant_transclusions:
                transclusion_text += u'<div style="float: left; border: thin dotted #aaa; margin: 3px; padding: 3px;">'
                if transclusion.from_item_id == item.pk:
                    transclusion_html_id = ('' if transclusion.to_item_id == comment.pk else 'replies') + ('%d' % transclusion.pk)
                    transclusion_text += u'<a href="#" onclick="highlight_comment(\'%s\', \'%s\', true, false); return false;">%s</a>' % (comment.pk, transclusion_html_id, get_viewable_name(context, transclusion.from_item))
                else:
                    transclusion_text += u'<a href="%s?highlighted_transclusion=%s">%s</a>' % (transclusion.from_item.get_absolute_url(), transclusion.pk, get_viewable_name(context, transclusion.from_item))
                transclusion_text += u'</div>'
            transclusion_text += u'<div style="clear: both;"></div>'
            if isinstance(comment, TextComment):
                if agentcan_helper(context, 'view TextDocument.body', comment):
                    comment_body = escape(comment.body).replace('\n', '<br />')
                else:
                    comment_body = ''
            else:
                comment_body = ''
            comment_url = u'%s?crumb_filter=recursive_comments_as_child.parent.%d' % (comment.get_absolute_url(), item.pk)
            result.append(u'<div id="comment_body%d" class="comment_body" style="display: none;">' % comment.pk)
            if relevant_transclusions:
                result.append(u'<div style="margin-bottom: 5px; padding-bottom: 5px; border-bottom: thin solid #ccc;">%s</div>' % transclusion_text)
            result.append(u'<div>%s</div>' % comment_body)
            result.append(u'<div style="clear: both; font-size: smaller; margin-top: 5px; padding-top: 5px; border-top: thin solid #ccc;">')
            result.append(u'<a href="#" onclick="openCommentDialog(\'comment%s\'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-comment"></span>Respond</a>' % comment.pk)
            result.append(u'<div style="clear: both;"></div>')
            result.append(u'</div>')
            result.append(u'</div>')
            result.append(u'<div id="comment_children%s">' % comment.pk)
            for subcomment in comment_info['subcomments']:
                add_comment_to_div(subcomment, parents + (comment_info,))
            result.append(u'</div>')
        comment_dicts, n_comments = comment_dicts_for_item(item, version_number, context, isinstance(item, Collection))
        for comment_dict in comment_dicts:
            add_comment_to_div(comment_dict, ())
        result.append("</div>")
        if agentcan_helper(context, 'comment_on', item):
            result.append(u'<div style="margin-top: 1em;"><a href="#" onclick="openCommentDialog(\'comment%s\'); return false;" class="fg-button ui-state-default fg-button-icon-left ui-corner-all"><span class="ui-icon ui-icon-comment"></span>Create a new discussion</a></div>' % item.pk)
        context['communityforum_comment_box'] = mark_safe('\n'.join(result))
        return ''

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
            login_menu_text = u'%s [Logout]' % get_viewable_name(context, viewer.cur_agent)

        result.append("""
        <script type="text/javascript">
        $(function(){
            var menuContent = '<ul style="font-size: 85%%;">';
            $.each($('#login_menu_link').next().children().filter('li.loginmenuitem'), function(i, val){
                menuContent += '<li>' + $(val).html() + '</li>';
            });
            menuContent += '</ul>'
            $('#login_menu_link').menu({
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
        <a href="#" class="fg-button fg-button-icon-right ui-widget ui-state-default ui-corner-all" id="login_menu_link"><span class="ui-icon ui-icon-triangle-1-s"></span>%s</a>
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

