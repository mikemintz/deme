#TODO completely clean up code

from django.core.urlresolvers import reverse
from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import *

class JustTextNoInputWidget(forms.Widget):
    """A form widget that just displays text without any sort of input."""
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        if attrs is None: attrs = {}
        #TODO this is small and gray
        return """<span id="%(id)s">%(value)s</span>""" % {'id': attrs.get('id', ''), 'value': value}

class AjaxModelChoiceWidget(forms.Widget):
    """Ajax auto-complete widget for ForeignKey fields."""
    def render(self, name, value, attrs=None):
        model = self.choices.queryset.model
        #field = self.choices.field
        try:
            if issubclass(model, Item):
                value_item = Item.objects.get(pk=value)
            elif issubclass(model, Item.Version):
                value_item = Item.Version.objects.get(pk=value)
            else:
                value_item = None
        except:
            value_item = None
        initial_search = value_item.name if value_item else '' #TODO this poses a permission problem. someone can set an initial item, and figure out its name
        if value is None: value = ''
        if attrs is None: attrs = {}
        ajax_url = reverse('item_type_url', kwargs={'viewer': model.__name__.lower(), 'format': 'json'})
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

class JavaScriptSpamDetectionWidget(forms.Widget):
    """Widget that uses JavaScript to detect spam."""

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
        """ % {'name': name, 'value': value, 'id': attrs.get('id', ''), 'required_value': self.required_value}
        return result

class AjaxModelChoiceField(forms.ModelChoiceField):
    """Ajax auto-complete field for ForeignKey fields."""
    widget = AjaxModelChoiceWidget

class HiddenModelChoiceField(forms.ModelChoiceField):
    """Hidden field for ForeignKey fields."""
    widget = forms.HiddenInput

class JavaScriptSpamDetectionField(forms.Field):
    """Hidden field that uses JavaScript to detect spam."""

    default_error_messages = {
        'wrong_value': _(u'If you are not logged in, you must have JavaScript and cookies enabled to submit this form (for spam detection).'),
    }
    
    def __init__(self, required_value):
        widget = JavaScriptSpamDetectionWidget(required_value)
        super(JavaScriptSpamDetectionField, self).__init__(widget=widget)
        self.required_value = required_value

    def clean(self, value):
        if value != self.required_value:
            raise forms.util.ValidationError(self.error_messages['wrong_value'])

class AddSubPathForm(forms.ModelForm):
    aliased_item = super(models.ForeignKey, CustomUrl._meta.get_field_by_name('aliased_item')[0]).formfield(queryset=CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.to._default_manager.complex_filter(CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.limit_choices_to), form_class=AjaxModelChoiceField, to_field_name=CustomUrl._meta.get_field_by_name('aliased_item')[0].rel.field_name)
    parent_url = super(models.ForeignKey, CustomUrl._meta.get_field_by_name('parent_url')[0]).formfield(queryset=CustomUrl._meta.get_field_by_name('parent_url')[0].rel.to._default_manager.complex_filter(CustomUrl._meta.get_field_by_name('parent_url')[0].rel.limit_choices_to), form_class=HiddenModelChoiceField, to_field_name=CustomUrl._meta.get_field_by_name('parent_url')[0].rel.field_name)
    action_summary = forms.CharField(label=_("Action summary"), help_text=_("Reason for adding this subpath"), widget=forms.TextInput, required=False)
    class Meta:
        model = CustomUrl
        fields = ['aliased_item', 'viewer', 'action', 'query_string', 'format', 'parent_url', 'path']

class NewMembershipForm(forms.ModelForm):
    item = AjaxModelChoiceField(Item.objects)
    action_summary = forms.CharField(label=_("Action summary"), help_text=_("Reason for adding this item"), widget=forms.TextInput, required=False)
    class Meta:
        model = Membership
        fields = ['item']

class NewTextCommentForm(forms.ModelForm):
    item = HiddenModelChoiceField(Item.objects)
    item_version_number = forms.IntegerField(widget=forms.HiddenInput())
    item_index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    name = forms.CharField(label=_("Comment title"), help_text=_("A brief description of the comment"), widget=forms.TextInput, required=False)
    class Meta:
        model = TextComment
        fields = ['name', 'body', 'item', 'item_version_number']

class NewDemeAccountForm(forms.ModelForm):
    agent = AjaxModelChoiceField(Agent.objects)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    action_summary = forms.CharField(label=_("Action summary"), help_text=_("Reason for creating this item"), widget=forms.TextInput, required=False)
    class Meta:
        model = DemeAccount
        exclude = ['password']
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    def save(self, commit=True):
        item = super(NewDemeAccountForm, self).save(commit=False)
        item.set_password(self.cleaned_data["password1"])
        if commit:
            item.save()
        return item

class EditDemeAccountForm(forms.ModelForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput)
    action_summary = forms.CharField(label=_("Action summary"), help_text=_("Reason for editing this item"), widget=forms.TextInput, required=False)
    class Meta:
        model = DemeAccount
        exclude = ['password', 'agent']
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2
    def save(self, commit=True):
        item = super(EditDemeAccountForm, self).save(commit=False)
        item.set_password(self.cleaned_data["password1"])
        if commit:
            item.save()
        return item

