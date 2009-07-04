from django.template import Context, loader
from django.http import HttpResponse
from cms.views import HtmlDocumentViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.event.models import Event
from datetime import date, datetime
from icalendar import Calendar as iCal
from icalendar import Event as iEvent
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
        all_members = collection.all_contained_collection_members(recursive_filter).order_by('-created_at')

        try:
            month_offset = int(self.request.GET.get('month_offset', '0'))
        except ValueError:
            month_offset = 0

        today = date.today()
        year = today.year
        month = today.month
        while month + month_offset > 12:
            year = year + 1
            month = month - 12
        while month + month_offset < 1:
            year = year - 1
            month = month + 12

        today = date(year, (month + month_offset), today.day)
        this_month = calendar.Calendar(6)
        week_list = this_month.monthdatescalendar(today.year, today.month)
        events = {}

        for member in all_members:
            if issubclass(member.actual_item_type(), Event): 
                member = member.downcast()
                if member.start_date.month == today.month: #delete to have events displayed not in current month?
                    for i in range(member.start_date.day, member.end_date.day + 1):
                        this_day = date(member.start_date.year, member.start_date.month, i)
                        day_event_list = []
                        if this_day in events.keys():
                            day_event_list = events[this_day]

                        details = {}
                        details["start_time"] = member.start_time
                        details["start_date"] = member.start_date
                        details["is_starting_date"] = (member.start_date == this_day)
                        details["end_date"] = member.end_date
                        details["name"] = member.display_name()
                        details["url"] = member.get_absolute_url() 
                        day_event_list.append(details)
                        events[this_day] = day_event_list

        event_week_list = []
        actual_today = date.today()

        for week in week_list:
            event_week = []
            
            for day in week:
                days_events = {}
                days_events["day"] = day
                days_events["cur_events"] = events.get(day, [])
                days_events["in_cur_month"] = (day.month == today.month)
                days_events["is_today"] = (day == actual_today)
                event_week.append(days_events)

            event_week_list.append(event_week)

        self.context['today'] = today
        self.context['week_list'] = event_week_list
        self.context['next_month_offset'] = month_offset + 1
        self.context['prev_month_offset'] = month_offset - 1
        return HttpResponse(template.render(self.context))

    def item_export_html(self):
        cal = iCal()
        collection = self.item

        if self.cur_agent_can_global('do_anything'):
            recursive_filter = None
        else:
            visible_memberships = self.permission_cache.filter_items('view Membership.item', Membership.objects)
            recursive_filter = Q(child_memberships__in=visible_memberships.values('pk').query)
        all_members = collection.all_contained_collection_members(recursive_filter).order_by('-created_at')

        for member in all_members:
            if issubclass(member.actual_item_type(), Event): 
                member = member.downcast()
                newEvent = iEvent()
                newEvent.add('summary', member.display_name())
                newEvent.add('dtstart', datetime.combine(member.start_date, member.start_time))
                newEvent.add('dtend', datetime.combine(member.start_date, member.start_time))
                newEvent.add('location', member.location)
                newEvent.add('description', member.body)
                cal.add_component(newEvent)

        response = HttpResponse(cal.as_string(), mimetype='ics')
        response['Content-Disposition'] = 'attachment; filename=demeCalendar.ics'
        return response


