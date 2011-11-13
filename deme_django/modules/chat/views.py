from django.template import Context, loader
from django.http import HttpResponse
from cms.models import Item
from cms.base_viewer import Viewer
from modules.chat.models import ChatMessage
import datetime
from django.utils import simplejson
from django.utils.html import escape

class ChatViewer(Viewer):
    accepted_item_type = Item
    viewer_name = 'chat' 

    def type_createchatmessage_json(self):
        body = self.request.REQUEST.get('body')
        chat_message = ChatMessage(agent=self.cur_agent, created_at=datetime.datetime.now(), body=body)
        chat_message.save()
        data = 'success'
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def type_listchatmessage_json(self):
        default_initial_history = 10 #TODO set to something like 50
        max_message_burst = 100
        last_chatmessage_pk = self.request.REQUEST.get('last_pk')
        if last_chatmessage_pk is None:
            last_chatmessage_pks = ChatMessage.objects.order_by('-pk')[:1].values_list('pk')
            last_chatmessage_pk = last_chatmessage_pks[0][0] if last_chatmessage_pks else 0
            last_chatmessage_pk -= default_initial_history
        new_chatmessages = ChatMessage.objects.filter(pk__gt=last_chatmessage_pk).order_by('pk')[:max_message_burst]
        data = [{
            'pk': x.pk,
            'body': escape(x.body),
            'time': x.created_at.strftime("%s"),
            'agent_name': escape(x.agent.display_name()),
            'agent_url': x.agent.get_absolute_url()
        } for x in new_chatmessages]
        json_str = simplejson.dumps(data, separators=(',',':'))
        return HttpResponse(json_str, mimetype='application/json')

    def type_history_html(self):
        self.context['action_title'] = 'Chat history'
        self.context['chat_messages'] = ChatMessage.objects.order_by('pk')
        template = loader.get_template('chat/history.html')
        return HttpResponse(template.render(self.context))
