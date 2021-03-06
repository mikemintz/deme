from django import template
from django.core.urlresolvers import reverse
from cms.models import *
from django.utils.http import urlquote
from django.utils.html import escape
from django.utils.safestring import mark_safe
from cms.templatetags.item_tags import *

register = template.Library()

class CalculateComments(template.Node):
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
            result.append(u'<div style="margin-bottom: 5px; padding: 5px; border: 1px solid #ddd; border-width: 1px 0; background-color: #%s">' % ('f9f9f9' if len(parents) == 0 else 'f9f9f9' if len(parents) % 2 == 0 else 'fff'))
            if agentcan_helper(context, 'view Item.creator', comment):
                result.append('<div style="font-weight: bold;">%s</div>' % get_viewable_name(context, comment.creator))
            result.append(u'<div>%s</div>' % comment_body)
            result.append(u'</div>')
            result.append(u'<div id="comment%s" style="display: none;"><form onsubmit="if (this[\'body\'].value.trim() == \'\') { alert(\'You must fill out a body for your reply\'); return false; } return true;" method="post" action="%s?redirect=%s">'% (comment.pk, reverse('item_url', kwargs={'viewer': 'discussion', 'noun': context['discussion_board'].pk, 'action': 'createreply'}), urlquote(full_path)))
            result.append(u'<input name="name" type="hidden" value="Re: %s" /><p><textarea name="body" style="height: 100px; width: 100%%;"></textarea></p>' % (comment.name))
            permission_editor_html = PermissionEditor(None, target_level='one', privacy_only=False, is_new_item=True, accordion_comment_parent=comment).render(context)
            result.append(u'<div style="display: none;">%s</div>' % permission_editor_html)
            result.append(u'<p><input type="submit" value="Submit reply" class="btn btn-primary" /></p><input type="hidden" name="item" value="%s" /><input type="hidden" name="item_version_number" value="%s" />' % (comment.pk, comment.version_number))
            result.append(u'</form></div>')
            result.append(u'<div style="margin-bottom: 5px;">')
            if agentcan_helper(context, 'comment_on', comment):
                result.append(u'<div style="float: right;"><a href="#" onclick="$(\'#comment%s\').show(); return false;" class="btn btn-default"><span class="glyphicon glyphicon-comment"></span> Reply</a></div>' % comment.pk)
            if agentcan_helper(context, 'view Item.created_at', comment):
                result.append('<div class="datetime" style="margin-left:5px">%s</div>' % comment.created_at.strftime("%B %d, %Y, %l:%M %p"))
            result.append(u'<div style="clear: both;"></div>')
            result.append(u'</div>')
            if len(parents) == 0:
                result.append(u'<div style="border-bottom: 1px solid #ddd; margin-top: 5px; margin-bottom: 15px;"></div>')
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
def calculatecomments(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return CalculateComments()


class NewDiscussionPermissions(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<NewDiscussionPermissionsNode>"

    def render(self, context):
        permission_editor_html = PermissionEditor(None, target_level='one', privacy_only=False, is_new_item=True, accordion_comment_parent=context['item']).render(context)
        return mark_safe(permission_editor_html)

@register.tag
def new_discussion_permission_editor(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return NewDiscussionPermissions()

