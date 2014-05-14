from django.db import models
import datetime
from cms.models import HtmlDocument, Collection
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django import forms
from cms.forms import SelectTimeWidget

__all__ = ['Event', 'Calendar']

class Event(HtmlDocument):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset(['view Event.location', 'view Event.start_date', 'view Event.start_time',
                                      'view Event.end_date', 'view Event.end_time', 'edit Event.start_date', 'edit Event.start_time',
                                      'edit Event.end_date', 'edit Event.end_time',  'edit Event.location'])
    introduced_global_abilities = frozenset(['create Event'])
    dyadic_relations = {}

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    time_zones = (
        (settings.TIME_ZONE, u'(default) ' + settings.TIME_ZONE),
        (u'UTC-8', u'Pacific Standard Time (UTC -8)'),
        (u'UTC-7', u'Mountain Standard Time (UTC -7)'),
        (u'UTC-6', u'Central Standard Time (UTC -6)'),
        (u'UTC-5', u'Eastern Standard Time (UTC -5)'),
        (u'UTC-4', u'Western Brazilian Time (UTC -4)'),
        (u'UTC-3', u'Eastern Brazilian Time (UTC -3)'),
        (u'UTC-1', u'West African Time (UTC -1)'),
        (u'UTC', u'Greenwich Mean Time (UTC)'),
        (u'UTC+1', u'Central Europe Time (UTC +1)'),
        (u'UTC+2', u'Eastern Europe Time (UTC +2)'),
        (u'UTC+3', u'Moscow Time (UTC +3)'),
        (u'UTC+3:30', u'Iran Time (UTC +3:30)'),
        (u'UTC+4', u'Samara Time (UTC +4)'),
        (u'UTC+5', u'Pakistan Time (UTC +5)'),
        (u'UTC+6', u'Lankan/Bangla Desh Time (UTC +6)'),
        (u'UTC+7', u'West Indonesia/West Australia Time (UTC +7)'),
        (u'UTC+8', u'China/Central Indonesia Time (UTC +8)'),
        (u'UTC+9', u'Japan/Korea Standard Time (UTC +9)'),
        (u'UTC+9:30', u'Central Australian Standard Time (UTC +9:30)'),
        (u'UTC+10', u'Guam Standard Time (UTC +10)'),
        (u'UTC+12', u'New Zealand Standard Time (UTC +12)'),
        (u'UTC-9', u'Yukon Standard Time (UTC -9)'),
        (u'UTC-10', u'Alaska/Hawaii Standard Time (UTC -10)'),
    )

    #fields:
    start_date = models.DateField(_('start date'))
    start_time = models.TimeField(_('start time'))
    end_date   = models.DateField(_('end date'))
    end_time   = models.TimeField(_('end time'))
    location   = models.CharField(_('location'), max_length=255)
    time_zone  = models.CharField(_('time zone'), max_length=255, choices=time_zones, default=settings.TIME_ZONE)


    @classmethod
    def do_specialized_form_configuration(cls, item_type, is_new, attrs):
        super(Event, cls).do_specialized_form_configuration(item_type, is_new, attrs)
        attrs['start_time'] = forms.CharField(label=_("Start Time"), widget=SelectTimeWidget(twelve_hr=True))
        attrs['end_time'] = forms.CharField(label=_("End Time"), widget=SelectTimeWidget(twelve_hr=True))

class Calendar(Collection):

    #Setup
    introduced_immutable_fields = frozenset()
    introduced_abilities = frozenset()
    introduced_global_abilities = frozenset(['create Calendar'])
    dyadic_relations = {}
    default_membership_type = 'event'
    class Meta:
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendar')
