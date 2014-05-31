from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote
from cms.models import Item
from django.forms.fields import CharField, MultiValueField
from django.forms.widgets import TextInput, MultiWidget, HiddenInput
import hashlib
import random
from urlparse import urljoin
from django.conf import settings

class JustTextNoInputWidget(forms.Widget):
    """A form widget that just displays text without any sort of input."""
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        if attrs is None: attrs = {}
        #TODO this is small and gray, we need a better way to format help_text in CSS
        return """<span id="%(id)s">%(value)s</span>""" % {'id': attrs.get('id', ''), 'value': value}


class AjaxModelChoiceWidget(forms.Widget):
    #TODO completely clean up code for this class
    """Ajax auto-complete widget for ForeignKey fields."""

    def __init__(self, *args, **kwargs):
        self.required_abilities = kwargs.pop('required_abilities')
        self.permission_cache = kwargs.pop('permission_cache')
        super(AjaxModelChoiceWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        model = self.choices.queryset.model
        #field = self.choices.field
        try:
            if issubclass(model, Item):
                value_item = Item.objects.get(pk=value)
            else:
                value_item = None
        except:
            value_item = None
        if value_item:
            can_view_name = self.permission_cache.agent_can('view Item.name', value_item)
            initial_search = value_item.display_name(can_view_name_field=can_view_name)
        else:
            initial_search = ''

        if value is None: value = ''
        if attrs is None: attrs = {}
        base_type = model.__name__.lower()
        if attrs.get('override_type'):
            base_type = attrs.get('override_type')
        ajax_query_string = '&'.join('ability=' + urlquote(ability) for ability in self.required_abilities)
        ajax_url = reverse('item_type_url', kwargs={'viewer': base_type, 'format': 'json'}) + '?' + ajax_query_string
        new_modal_query_string = '?modal=1&id=' + attrs.get('id', '') + '&base_type=' + base_type
        new_modal_url = reverse('item_type_url', kwargs={'viewer': base_type, 'action': 'new'}) + new_modal_query_string
        list_modal_url = reverse('item_type_url', kwargs={'viewer': base_type, 'action': 'list'}) + new_modal_query_string
        result = """
        <div class="input-group ajax-model-choice-widget-group">
          <input type="hidden" name="%(name)s" value="%(value)s" data-model-name="%(model_name)s" data-input-id="%(id)s" data-ajax-url="%(ajax_url)s" data-new-modal-url="%(new_modal_url)s" data-list-modal-url="%(list_modal_url)s" class="ajax-model-choice-widget">
          <input type="text" class="form-control text-field" id="%(id)s" name="%(name)s_search" value="%(initial_search)s" placeholder="Search for item...">
        </div>
        """ % {
          'base_type': base_type,
          'name': name,
          'value': value,
          'id': attrs.get('id', ''),
          'ajax_url': ajax_url,
          'initial_search': initial_search,
          'model_name': model.__name__.lower(),
          'new_modal_url': new_modal_url,
          'list_modal_url': list_modal_url
        }
        # see /javascripts/deme/ajax-model-choice-widget.js for implementation
        #TODO fail in more obvious way if attrs['id'] is not set
        return result


class AjaxModelChoiceField(forms.ModelChoiceField):
    #TODO completely clean up code for this class
    """Ajax auto-complete field for ForeignKey fields."""

    default_error_messages = {
        'permission_denied': _(u'You do not have permission to set this field to this value.'),
    }

    def __init__(self, *args, **kwargs):
        self.permission_cache = kwargs.pop('permission_cache')
        self.required_abilities = kwargs.pop('required_abilities')
        self.widget = AjaxModelChoiceWidget(required_abilities=self.required_abilities,
                                            permission_cache=self.permission_cache)
        super(AjaxModelChoiceField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(AjaxModelChoiceField, self).clean(value)
        if value is not None:
            for ability in self.required_abilities:
                if not self.permission_cache.agent_can(ability, value):
                    raise forms.util.ValidationError(self.error_messages['permission_denied'])
        return value


#this widget is from djangosnippets.com and it was written by the user "bradmontgomery"
#it can be found at http://www.djangosnippets.org/snippets/1202/

import re
from django.forms.widgets import Widget, Select, MultiWidget
from django.forms.extras.widgets import SelectDateWidget
from django.utils.safestring import mark_safe

# Attempt to match many time formats:
# Example: "12:34:56 P.M."  matches:
# ('12', '34', ':56', '56', 'P.M.', 'P', '.', 'M', '.')
# ('12', '34', ':56', '56', 'P.M.')
# Note that the colon ":" before seconds is optional, but only if seconds are omitted
#time_pattern = r'(\d\d?):(\d\d)(:(\d\d))? *((a{1}|A{1}|p{1}|P{1})(\.)?(m{1}|M{1})(\.)?)?$'
time_pattern = r'(\d\d?):(\d\d)(:(\d\d))? *([aApP]\.?[mM]\.?)?$' # w/ Magus's suggestions

RE_TIME = re.compile(time_pattern)
# The following are just more readable ways to access re.matched groups:
HOURS = 0
MINUTES = 1
SECONDS = 3
MERIDIEM = 4

class SelectTimeWidget(Widget):
    """
    A Widget that splits time input into <select> elements.
    Allows form to show as 24hr: <hour>:<minute>:<second>,
    or as 12hr: <hour>:<minute>:<second> <am|pm>

    Also allows user-defined increments for minutes/seconds
    """
    hour_field = '%s_hour'
    minute_field = '%s_minute'
    second_field = '%s_second'
    meridiem_field = '%s_meridiem'
    twelve_hr = False # Default to 24hr.
    show_seconds = False # Default to hide seconds.

    def __init__(self, attrs=None, hour_step=None, minute_step=None, second_step=None, twelve_hr=False, show_seconds=False):
        '''
        hour_step, minute_step, second_step are optional step values for
        for the range of values for the associated select element
        twelve_hr: If True, forces the output to be in 12-hr format (rather than 24-hr)
        '''
        self.attrs = attrs or {}
        self.show_seconds = show_seconds

        if twelve_hr:
            self.twelve_hr = True # Do 12hr (rather than 24hr)
            self.meridiem_val = 'a.m.' # Default to Morning (A.M.)

        if hour_step and twelve_hr:
            self.hours = range(1,13,hour_step)
        elif hour_step: # 24hr, with stepping.
            self.hours = range(0,24,hour_step)
        elif twelve_hr: # 12hr, no stepping
            self.hours = range(1,13)
        else: # 24hr, no stepping
            self.hours = range(0,24)

        if minute_step:
            self.minutes = range(0,60,minute_step)
        else:
            self.minutes = range(0,60)

        if second_step:
            self.seconds = range(0,60,second_step)
        else:
            self.seconds = range(0,60)

    def render(self, name, value, attrs=None):
        try: # try to get time values from a datetime.time object (value)
            hour_val, minute_val, second_val = value.hour, value.minute, value.second
            if self.twelve_hr:
                if hour_val >= 12:
                    self.meridiem_val = 'p.m.'
                else:
                    self.meridiem_val = 'a.m.'
        except AttributeError:
            hour_val = minute_val = second_val = 0
            if isinstance(value, basestring):
                match = RE_TIME.match(value)
                if match:
                    time_groups = match.groups();
                    hour_val = int(time_groups[HOURS]) % 24 # force to range(0-24)
                    minute_val = int(time_groups[MINUTES])
                    if time_groups[SECONDS] is None:
                        second_val = 0
                    else:
                        second_val = int(time_groups[SECONDS])

                    # check to see if meridiem was passed in
                    if time_groups[MERIDIEM] is not None:
                        self.meridiem_val = time_groups[MERIDIEM]
                    else: # otherwise, set the meridiem based on the time
                        if self.twelve_hr:
                            if hour_val >= 12:
                                self.meridiem_val = 'p.m.'
                            else:
                                self.meridiem_val = 'a.m.'
                        else:
                            self.meridiem_val = None


        # If we're doing a 12-hr clock, there will be a meridiem value, so make sure the
        # hours get printed correctly
        if self.twelve_hr and self.meridiem_val:
            if self.meridiem_val.lower().startswith('p') and hour_val > 12 and hour_val < 24:
                hour_val = hour_val % 12
        elif hour_val == 0:
            hour_val = 12

        output = []
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        # NOTE: for times to get displayed correctly, the values MUST be converted to unicode
        # When Select builds a list of options, it checks against Unicode values
        hour_val = u"%.2d" % hour_val
        minute_val = u"%.2d" % minute_val
        second_val = u"%.2d" % second_val

        hour_choices = [("%.2d"%i, "%.2d"%i) for i in self.hours]
        local_attrs = self.build_attrs(id=self.hour_field % id_)
        select_html = Select(choices=hour_choices).render(self.hour_field % name, hour_val, local_attrs)
        output.append(select_html)

        minute_choices = [("%.2d"%i, "%.2d"%i) for i in self.minutes]
        local_attrs['id'] = self.minute_field % id_
        select_html = Select(choices=minute_choices).render(self.minute_field % name, minute_val, local_attrs)
        output.append(select_html)

        if self.show_seconds:
          second_choices = [("%.2d"%i, "%.2d"%i) for i in self.seconds]
          local_attrs['id'] = self.second_field % id_
          select_html = Select(choices=second_choices).render(self.second_field % name, second_val, local_attrs)

          output.append(select_html)

        if self.twelve_hr:
            #  If we were given an initial value, make sure the correct meridiem get's selected.
            if self.meridiem_val is not None and  self.meridiem_val.startswith('p'):
                    meridiem_choices = [('p.m.','p.m.'), ('a.m.','a.m.')]
            else:
                meridiem_choices = [('a.m.','a.m.'), ('p.m.','p.m.')]

            local_attrs['id'] = local_attrs['id'] = self.meridiem_field % id_
            select_html = Select(choices=meridiem_choices).render(self.meridiem_field % name, self.meridiem_val, local_attrs)
            output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_hour' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        # if there's not h:m:s data, assume zero:
        h = data.get(self.hour_field % name, 0) # hour
        m = data.get(self.minute_field % name, 0) # minute
        s = data.get(self.second_field % name, 0) # second
        meridiem = data.get(self.meridiem_field % name, None)

        #NOTE: if meridiem IS None, assume 24-hr
        if meridiem is not None:
            if meridiem.lower().startswith('p') and int(h) != 12:
                h = (int(h)+12)%24
            elif meridiem.lower().startswith('a') and int(h) == 12:
                h = 0

        if (int(h) == 0 or h) and m and s:
            return '%s:%s:%s' % (h, m, s)

        return data.get(name, None)

#This widget was found at http://www.djangosnippets.org/snippets/1548/
#Original author: user "gregb" on djangosnippets.org

class CaptchaTextInput(MultiWidget):
	def __init__(self,attrs=None):
		widgets = (
			HiddenInput(attrs),
			TextInput(attrs),
		)
		super(CaptchaTextInput,self).__init__(widgets,attrs)

	def decompress(self,value):
		if value:
			return value.split(',')
		return [None,None]


	def render(self, name, value, attrs=None):
		ints = (random.randint(0,9),random.randint(0,9),)
		answer = hashlib.sha1(str(sum(ints))).hexdigest()
		#print ints, sum(ints), answer

		extra = """<span style="font-size: 11pt;">What is %d + %d?</span><br>""" % (ints[0], ints[1])
		value = [answer, u'',]

		return mark_safe(extra + super(CaptchaTextInput, self).render(name, value, attrs=attrs))


class CaptchaField(MultiValueField):
	widget=CaptchaTextInput

	def __init__(self, *args,**kwargs):
		fields = (
			CharField(show_hidden_initial=True),
			CharField(),
		)
		super(CaptchaField,self).__init__(fields=fields, *args, **kwargs)

	def compress(self,data_list):
		if data_list:
			return ','.join(data_list)
		return None


	def clean(self, value):
		super(CaptchaField, self).clean(value)
		response, value[1] = value[1].strip().lower(), ''

		if not hashlib.sha1(str(response)).hexdigest() == value[0]:
			raise forms.ValidationError("Sorry, you got the security question wrong - to prove you're not a spammer, please try again.")
		return value
