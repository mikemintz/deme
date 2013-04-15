from django import template
from django.core.urlresolvers import reverse

register = template.Library()

class ChatBox(template.Node):
    def __init__(self):
        pass

    def __repr__(self):
        return "<ChatBox>"

    def render(self, context):
        viewer = context['_viewer']
        chathistory_url = reverse('item_type_url', kwargs={'viewer': 'chat', 'action': 'history'})
        createchatmessage_url = reverse('item_type_url', kwargs={'viewer': 'chat', 'action': 'createchatmessage', 'format': 'json'})
        listchatmessage_url = reverse('item_type_url', kwargs={'viewer': 'chat', 'action': 'listchatmessage', 'format': 'json'})
        result = """
            <div>
                <a href="%(chathistory_url)s">View chat history</a>
            </div>
            <div style="border-style: solid; border-width: 1px; border-color: #888;">
                <div id="chat_messages" style="height: 250px; overflow-y: scroll;">
                </div>
            </div>
            <form onsubmit="if (this['body'].value) $.ajax({url: '%(createchatmessage_url)s', type: 'POST', data: {'body': this['body'].value}}); this['body'].value = ''; this['body'].focus(); return false;">
                <input type="text" name="body" style="width:184px; " autocomplete="off" />
                <input type="submit" style="display: none;" value="Send" />
            </form>
            <script type="text/javascript">
                $(function(){
                    var chat_message_poll_interval_millis = 1000;
                    var last_pk = null;
                    function update_chat_messages_timer() {
                        var queryData = (last_pk == null) ? {} : {'last_pk': last_pk};
                        $.getJSON('%(listchatmessage_url)s', queryData, function(data) {
                            if (data.length > 0) {
                                last_pk = data[data.length - 1].pk;
                            }
                            var chat_messages_div = $("#chat_messages");
                            var scrolled_to_bottom = chat_messages_div[0].scrollHeight - chat_messages_div.scrollTop() == chat_messages_div.outerHeight();
                            $.each(data, function(i, msg) {
                                var date = new Date();
                                date.setTime(msg.time * 1000);
                                date_string = date.toUTCString();
                                var time_elem = '<span style="color: #999;">[' + date_string + ']</span>';
                                var agent_elem = ' &lt;<a href="' + msg.agent_url + '">' + msg.agent_name + '</a>&gt;';
                                var body_elem = ' <span>' + msg.body + '</span>';
                                var chat_message_elem = $('<div style="margin-bottom: 0.5em;">' + time_elem + agent_elem + body_elem + '</div>');
                                chat_messages_div.append(chat_message_elem);
                            });
                            if (scrolled_to_bottom) {
                                chat_messages_div.scrollTop(chat_messages_div[0].scrollHeight);
                            }
                        });
                        //window.setTimeout(update_chat_messages_timer, chat_message_poll_interval_millis);
                    }
                    update_chat_messages_timer();
                });
            </script>
        """ % {
            "chathistory_url": chathistory_url,
            "createchatmessage_url": createchatmessage_url,
            "listchatmessage_url": listchatmessage_url,
        }
        return result

@register.tag
def chat_box(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 1:
        raise template.TemplateSyntaxError, "%r takes no arguments" % bits[0]
    return ChatBox()
