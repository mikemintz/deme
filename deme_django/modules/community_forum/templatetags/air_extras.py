from django import template
from cms.models import *
from django.utils.http import urlquote
from cms.templatetags.item_tags import *
from modules.community_forum.views import CommunityForumParticipantViewer

register = template.Library()

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
