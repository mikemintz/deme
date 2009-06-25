from django.db import models
import datetime
from cms.models import HtmlDocument
from django.utils.translation import ugettext_lazy as _

__all__ = ['Event'] 

class Event(HtmlDocument): 

    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Event.location', 'view Event.start_date', 'view Event.start_time',
                                      'view Event.end_date', 'view Event.end_time', 'edit Event.start_date', 'edit Event.start_time',
                                      'edit Event.end_date', 'edit Event.end_time',  'edit Event.location'])
    introduced_global_abilities = frozenset(['create Event'])

    class Meta:    
        verbose_name = _('event')
        verbose_name_plural = _('events')

    #fields:
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date   = models.DateField()
    end_time   = models.TimeField()
    location   = models.CharField(_('location'), max_length=255) 



