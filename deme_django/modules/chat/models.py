from django.db import models
from cms.models import *
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

__all__ = ['ChatMessage'] 

class ChatMessage(models.Model): 
    agent = FixedForeignKey(Agent, related_name='chat_messages')
    created_at = models.DateTimeField()
    body = models.TextField()

