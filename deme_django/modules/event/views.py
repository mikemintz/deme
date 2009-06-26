from django.template import Context, loader
from django.http import HttpResponse
from cms.views import HtmlDocumentViewer, ItemViewer
from cms.models import *
from django.db.models import Q
from modules.event.models import Event
from datetime import date
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

        this_month = calendar.Calendar(6)
        today = date.today()
        week_list = this_month.monthdatescalendar(today.year,today.month)
        events = {}

        for member in all_members:
            if issubclass(member.actual_item_type(), Event): 
                member = member.downcast()
                if member.start_date.month == today.month:
                    day_event_list = []
                    if member.start_date.day in events.keys():
                        day_event_list = events[member.start_date.day]

                    details = {}
                    details["start_time"] = member.start_time
                    details["start_date"] = member.start_date
                    details["end_date"] = member.end_date
                    details["name"] = member.display_name()
                    details["url"] = member.get_absolute_url() 
                    day_event_list.append(details)
                    events[member.start_date.day] = day_event_list

        event_week_list = []

        for week in week_list:
            event_week = []
            
            for day in week:
                days_events = {}
                days_events["day"] = day
                days_events["has_events"] = False
                if day.month == today.month:
                    if day.day in events.keys() :
                        days_events["cur_events"] = events[day.day]
                        days_events["has_events"] = True
                event_week.append(days_events)

            event_week_list.append(event_week)

        self.context['today'] = today
        self.context['today_string'] = today.strftime("%B %Y")
        self.context['week_list'] = event_week_list
        self.context['events'] = events
        self.context['event_keys'] = events.keys()
        return HttpResponse(template.render(self.context))


