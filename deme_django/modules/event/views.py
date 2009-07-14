from django.template import Context, loader
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpRequest
from cms.views import HtmlDocumentViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.event.models import Event
from datetime import date, datetime, timedelta, tzinfo
import calendar
import time


class EventViewer(HtmlDocumentViewer):
    accepted_item_type = Event
    viewer_name = 'event' 
    

class CalendarViewer(ItemViewer):
    accepted_item_type = Collection
    viewer_name = 'calendar'

    def item_show_html(self):
        self.context['action_title'] = 'Show'
        template = loader.get_template('calendar/show.html')
        collection = self.item
        self.context['collection'] = collection

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        all_members = collection.all_contained_collection_members(recursive_filter)
        all_events = Event.objects.filter(pk__in=all_members.values('pk').query)
        all_events = self.permission_cache.filter_items('view Event.start_date', all_events)
        all_events = self.permission_cache.filter_items('view Event.start_time', all_events)
        all_events = self.permission_cache.filter_items('view Event.end_date', all_events)

        today = date.today()

        try:
            year = int(self.request.GET.get('year', today.year))
        except ValueError:
            year = today.year

        try:
            month = int(self.request.GET.get('month', today.month))
        except ValueError:
            month = today.month
            
        if month < 1 or month > 12:
            month = 1
        
        self.context['prev_month'] = month - 1
        self.context['prev_year'] = year
        self.context['next_month'] = month + 1
        self.context['next_year'] = year
        if month <= 1:
            self.context['prev_month'] = 12
            self.context['prev_year'] = year - 1
        elif month >= 12:
            self.context['next_month'] = 1
            self.context['next_year'] = year + 1
        
        this_month = calendar.Calendar(6)
        week_list = this_month.monthdatescalendar(year, month)
        begin_this_month = date(year, month, 1)
        end_this_month = date(year, month, calendar.monthrange(year, month)[1])
        events = {}

        for member in all_events:
            if end_this_month - member.start_date >= timedelta(days=0) and begin_this_month - member.end_date <= timedelta(days=0): 
                end_date = member.end_date.day
                start_date = member.start_date.day
                if member.end_date.month != month:
                    end_date = end_this_month.day
                if member.start_date.month != month:
                    start_date = 1

                for i in range(start_date, end_date + 1):
                    this_day = date(year, month, i)
                    day_event_list = []
                    if this_day in events.keys():
                        day_event_list = events[this_day]

                    details = {}
                    details["start_time"] = member.start_time
                    details["start_date"] = member.start_date
                    details["is_starting_date"] = (member.start_date == this_day)
                    details["end_date"] = member.end_date
                    details["end_time"] = member.end_time
                    details["location"] = member.location
                    details["body"] = member.body
                    details["name"] = member.display_name()
                    details["url"] = member.get_absolute_url() 
                    day_event_list.append(details)
                    events[this_day] = day_event_list

        event_week_list = []

        for week in week_list:
            event_week = []
            
            for day in week:
                days_events = {}
                days_events["day"] = day
                days_events["cur_events"] = events.get(day, [])
                days_events["in_cur_month"] = (day.month == month)
                days_events["is_today"] = (day == today)
                event_week.append(days_events)

            event_week_list.append(event_week)

        self.context['this_month'] = date(year, month, today.day)
        self.context['week_list'] = event_week_list
        self.context['redirect'] = reverse('item_url', kwargs={'viewer': 'calendar', 'action': 'show', 'noun': collection.pk}) 
        return HttpResponse(template.render(self.context))

    def item_export_html(self):
        try:
            from icalendar import Calendar as iCal
            from icalendar import Event as iEvent
        except ImportError:
            return self.render_error("Event Error", "Event exporting is not supported in this installation")
        cal = iCal()
        collection = self.item

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        all_members = collection.all_contained_collection_members(recursive_filter)
        all_events = Event.objects.filter(pk__in=all_members.values('pk').query)
        all_events = self.permission_cache.filter_items('view Event.start_date', all_events)
        all_events = self.permission_cache.filter_items('view Event.start_time', all_events)
        all_events = self.permission_cache.filter_items('view Event.end_date', all_events)

        cal.add('prodid', '-//Deme//Deme Calendar Module//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')

        for member in all_events:
            newEvent = iEvent()
            newEvent.add('summary', member.display_name())
            newEvent.add('dtstart', datetime.combine(member.start_date, member.start_time))
            newEvent.add('dtend', datetime.combine(member.end_date, member.end_time))
            newEvent.add('location', member.location)
            newEvent.add('description', member.body)
            cal.add_component(newEvent)

        response = HttpResponse(cal.as_string(), mimetype='text/calendar')
        response['Content-Disposition'] = 'attachment; filename=demeCalendar.ics'
        return response

    def item_exportguide_html(self):
        self.context['action_title'] = 'Export Guide'
        template = loader.get_template('calendar/exportguide.html')
        collection = self.item
        self.context['collection'] = collection
        self.context['export_url'] = reverse('item_url', kwargs={'viewer': 'calendar', 'action': 'export', 'noun': collection.pk}) 
        self.context['host'] = self.request.get_host()
        return HttpResponse(template.render(self.context))
