#
# Copyright (c) 2018 ISP RAS (http://www.ispras.ru)
# Ivannikov Institute for System Programming of the Russian Academy of Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pytz

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from users.models import User, SchedulerUser


class SematicUISelect(forms.Select):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget_class = {'ui', 'dropdown'}
        if 'class' in context['widget']['attrs']:
            widget_class |= set(context['widget']['attrs']['class'].split())
        context['widget']['attrs']['class'] = ' '.join(widget_class)
        return context


class SemanticUICheckbox(forms.CheckboxInput):

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget_class = {'hidden'}
        if 'class' in context['widget']['attrs']:
            widget_class |= set(context['widget']['attrs']['class'].split())
        context['widget']['attrs']['class'] = ' '.join(widget_class)
        return context


class FormColumnsMixin:
    form_columns = ()

    def column_iterator(self, column_id):
        for name in self.form_columns[column_id]:
            yield self[name]

    def __getitem__(self, item):
        if item.startswith('column_'):
            column_id = int(item.replace('column_', ''))
            if len(self.form_columns) > column_id:
                return self.column_iterator(column_id)
        return getattr(super(), '__getitem__')(item)


class BridgeAuthForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'placeholder': _('Username'), 'autofocus': True}))
    password = forms.CharField(
        label=_("Password"), strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': _('Password')}),
    )


class RegisterForm(FormColumnsMixin, UserCreationForm):
    form_columns = (
        ('username', 'password1', 'password2'),
        ('email', 'first_name', 'last_name'),
        ('accuracy', 'data_format', 'language', 'timezone')
    )

    timezone = forms.ChoiceField(
        label=_('Time zone'), widget=SematicUISelect(attrs={'class': 'search'}),
        choices=list((x, x) for x in pytz.common_timezones), initial=settings.DEF_USER['timezone']
    )
    accuracy = forms.IntegerField(
        widget=forms.NumberInput(), min_value=0, max_value=10, initial=settings.DEF_USER['accuracy']
    )
    first_name = forms.CharField(label=_('First name'), max_length=30, required=True)
    last_name = forms.CharField(label=_('Last name'), max_length=150, required=True)

    class Meta:
        model = User
        field_classes = {'username': UsernameField}
        fields = ('username', 'email', 'first_name', 'last_name', 'data_format', 'language')
        widgets = {'data_format': SematicUISelect(), 'language': SematicUISelect()}


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    retype_password = forms.CharField(widget=forms.PasswordInput(), help_text=_('Confirmation'), required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['password'].label = _("Password")
        self.fields['retype_password'].label = _("Confirmation")
        self.fields['email'].label = _("Email")
        self.fields['first_name'].label = _("First name")
        self.fields['last_name'].label = _("Last name")

    def clean_retype_password(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get("password")
        retyped = cleaned_data.get("retype_password")
        if password != retyped:
            raise forms.ValidationError("Passwords don't match")

    class Meta:
        model = User
        fields = ('username', 'password', 'retype_password', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(),
            'email': forms.EmailInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput()
        }


class EditProfileForm(FormColumnsMixin, forms.ModelForm):
    form_columns = (
        ('new_password1', 'new_password2', 'email', 'first_name', 'last_name'),
        ('accuracy', 'data_format', 'language', 'timezone', 'assumptions', 'triangles', 'coverage_data')
    )
    error_messages = {
        'password_mismatch': _("Passwords don't match."),
        'sch_login_required': _('Specify username')
    }

    new_password1 = forms.CharField(label=_("New password"), widget=forms.PasswordInput, required=False)
    new_password2 = forms.CharField(label=_("New password confirmation"), required=False, widget=forms.PasswordInput)
    timezone = forms.ChoiceField(
        label=_('Time zone'), widget=SematicUISelect(attrs={'class': 'search'}),
        choices=list((x, x) for x in pytz.common_timezones), initial=settings.DEF_USER['timezone']
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        elif password2:
            # Validate if passwords similar and both specified
            password_validation.validate_password(password2, self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["new_password1"]
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'data_format', 'language',
            'accuracy', 'assumptions', 'triangles', 'coverage_data'
        )
        widgets = {
            'data_format': SematicUISelect(),
            'language': SematicUISelect(),
            'assumptions': SemanticUICheckbox(),
            'triangles': SemanticUICheckbox(),
            'coverage_data': SemanticUICheckbox()
        }


class SchedulerUserForm(forms.ModelForm):
    error_messages = {
        'login_required': _('Specify username'),
        'password_required': _('Specify password'),
        'password_mismatch': _("Passwords don't match."),
    }
    login = UsernameField(label=_('Username'), max_length=128, required=False)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label=_("Confirmation"), required=False, widget=forms.PasswordInput)

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not getattr(self.instance, 'pk', None) and self.cleaned_data.get('login') and not password1:
            raise forms.ValidationError(self.error_messages['password_required'], code='password_required')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1') or ''
        password2 = self.cleaned_data.get('password2') or ''
        if password1 != password2:
            raise forms.ValidationError(self.error_messages['password_mismatch'], code='password_mismatch')
        elif password2:
            # Validate if passwords similar and both specified
            password_validation.validate_password(password2, self.instance)
        return password2

    def clean(self):
        if not self.cleaned_data.get('login') and self.cleaned_data.get('password2'):
            self.add_error('login', self.error_messages['login_required'])
        return super().clean()

    def save(self, commit=True):
        if self.cleaned_data['login']:
            self.instance.password = self.cleaned_data['password2']
            return super(SchedulerUserForm, self).save(commit)
        elif getattr(self.instance, 'pk', None):
            self.instance.delete()
        return None

    class Meta:
        model = SchedulerUser
        fields = ('login', 'password1', 'password2')


class EditUserForm(forms.ModelForm):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'off'}), required=False)
    retype_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'off'}), required=False)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.fields['new_password'].label = _("New password")
        self.fields['retype_password'].label = _("Confirmation")
        self.fields['first_name'].label = _("First name")
        self.fields['last_name'].label = _("Last name")

    def clean_retype_password(self):
        cleaned_data = super(EditUserForm, self).clean()
        new_pass = cleaned_data.get("new_password")
        retyped = cleaned_data.get("retype_password")
        if new_pass != retyped:
            raise forms.ValidationError(_("Passwords don't match"))

    class Meta:
        model = User
        fields = ('new_password', 'retype_password', 'email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput()
        }


class UserExtendedForm(forms.ModelForm):
    accuracy = forms.IntegerField(widget=forms.NumberInput(), min_value=0, max_value=10,
                                  initial=settings.DEF_USER['accuracy'])
    timezone = forms.ChoiceField(choices=list((x, x) for x in pytz.common_timezones))

    def __init__(self, *args, **kwargs):
        super(UserExtendedForm, self).__init__(*args, **kwargs)
        self.fields['accuracy'].label = _("The number of significant figures")
        self.fields['language'].label = _("Language")
        self.fields['data_format'].label = _("Data format")
        self.fields['assumptions'].label = _("Error trace assumptions")
        self.fields['triangles'].label = _("Error trace closing triangles")
        self.fields['coverage_data'].label = _("Coverage data")

    class Meta:
        # model = Extended
        fields = ('accuracy', 'data_format', 'language', 'assumptions', 'triangles', 'coverage_data')
        widgets = {
            'data_format': forms.Select(attrs={'class': 'ui selection dropdown'}),
            'language': forms.Select(attrs={'class': 'ui selection dropdown'}),
            'assumptions': forms.CheckboxInput(attrs={'class': 'hidden'}),
            'triangles': forms.CheckboxInput(attrs={'class': 'hidden'}),
            'coverage_data': forms.CheckboxInput(attrs={'class': 'hidden'})
        }
