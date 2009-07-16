from django.db import models
import datetime
from cms.models import HtmlDocument, Collection
from django.utils.translation import ugettext_lazy as _

__all__ = ['Event', 'Calendar'] 

class Event(HtmlDocument): 

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Event.location', 'view Event.start_date', 'view Event.start_time',
                                      'view Event.end_date', 'view Event.end_time', 'edit Event.start_date', 'edit Event.start_time',
                                      'edit Event.end_date', 'edit Event.end_time',  'edit Event.location'])
    introduced_global_abilities = frozenset(['create Event'])

    class Meta:    
        verbose_name = _('event')
        verbose_name_plural = _('events')

    #fields:
    start_date = models.DateField(_('start date'))
    start_time = models.TimeField(_('start time'))
    end_date   = models.DateField(_('end date'))
    end_time   = models.TimeField(_('end time'))
    location   = models.CharField(_('location'), max_length=255) 

class Calendar(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Calendar'])
    class Meta:
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendar')
    

