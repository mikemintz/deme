from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote
from cms.models import Item

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
        ajax_query_string = '&'.join('ability=' + urlquote(ability) for ability in self.required_abilities)
        ajax_url = reverse('item_type_url', kwargs={'viewer': model.__name__.lower(), 'format': 'json'}) + '?' + ajax_query_string
        result = """
        <input type="hidden" name="%(name)s" value="%(value)s" />
        <input class="ajax_choice_field" type="text" id="%(id)s" name="%(name)s_search" value="%(initial_search)s" autocomplete="off" />
        <div class="ajax_choice_results" style="display: none;"></div>
        <script type="text/javascript">
        fn = function(){
          var search_onchange = function(e) {
            if (e.value === e.last_value) return;
            e.last_value = e.value;
            var hidden_input = $(e).prev()[0];
            var results_div = $(e).next()[0];
            if (e.value == '') {
              $(results_div.childNodes).remove();
              $(results_div).hide();
              hidden_input.value = '';
              return;
            }
            jQuery.getJSON('%(ajax_url)s', {q:e.value}, function(json) {
              json.splice(0, 0, ['[NULL]', '']);
              $(results_div.childNodes).remove();
              $.each(json, function(i, datum){
                var option = document.createElement('div');
                option.className = 'ajax_choice_option';
                option.innerHTML = datum[0];
                $(option).bind('click', function(event){
                  window.clearInterval(e.ajax_timer);
                  e.value = datum[0];
                  e.last_value = datum[0];
                  e.ajax_timer = window.setInterval(function(){search_onchange(e)}, 250); //TODO use bind on search_onchange?
                  hidden_input.value = datum[1];
                  $(results_div.childNodes).remove();
                  $(results_div).hide();
                });
                x = results_div;
                results_div.appendChild(option);
              });
              $(results_div).show();
            });
          };
          $('.ajax_choice_field:not(.ajax_choice_field_activated)').addClass('ajax_choice_field_activated').each(function(i, input){
            input.last_value = input.value;
            input.ajax_timer = window.setInterval(function(){search_onchange(input)}, 250); //TODO use bind on search_onchange?
          });
        };
        fn();
        </script>
        """ % {'name': name, 'value': value, 'id': attrs.get('id', ''), 'ajax_url': ajax_url, 'initial_search': initial_search}
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


class JavaScriptSpamDetectionWidget(forms.Widget):
    """
    Widget that uses JavaScript to detect spam (for JavaScriptSpamDetectionField).
    """

    is_hidden = True

    def __init__(self, required_value):
        super(JavaScriptSpamDetectionWidget, self).__init__()
        self.required_value = required_value

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        if attrs is None: attrs = {}
        result = """
        <input type="hidden" name="%(name)s" value="%(value)s" id="%(id)s" />
        <script type="text/javascript">
        document.getElementById('%(id)s').value = '%(required_value)s';
        </script>
        """ % {'name': name,
               'value': value,
               'id': attrs.get('id', ''),
               'required_value': self.required_value}
        return result


class JavaScriptSpamDetectionField(forms.Field):
    """
    Hidden field that uses JavaScript to detect spam. It just creates a simple
    hidden input and a line of JavaScript that sets the value of that input,
    under the assumption that spam bots do not execute JavaScript. On
    submission, if the value of this field is not correct, we raise a
    validation error.
    
    The `required_value` parameter must be the same when in the view where the
    form is created and in the view where the form is processed, but other than
    that it can be any string.
    """

    default_error_messages = {
        'wrong_value': _(u'You must either log in or enable JavaScript and cookies to submit this form (for spam detection).'),
    }
    
    def __init__(self, required_value):
        widget = JavaScriptSpamDetectionWidget(required_value)
        super(JavaScriptSpamDetectionField, self).__init__(widget=widget)
        self.required_value = required_value

    def clean(self, value):
        if value != self.required_value:
            raise forms.util.ValidationError(self.error_messages['wrong_value'])


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
    
    def __init__(self, attrs=None, hour_step=None, minute_step=None, second_step=None, twelve_hr=False):
        '''
        hour_step, minute_step, second_step are optional step values for
        for the range of values for the associated select element
        twelve_hr: If True, forces the output to be in 12-hr format (rather than 24-hr)
        '''
        self.attrs = attrs or {}
        
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

