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

