# -*- coding: utf-8 -*-

from django import forms
from models import Billboard, Language

LANG_CHOICES= tuple((e.title, e.title_orig) for e in Language.objects.all())

class SceneForm(forms.Form):
    media_content= forms.FileField(widget=forms.FileInput)
    media_src= forms.URLField(required=False, help_text="Источник ")
    media_copyright= forms.CharField(required=False, help_text="&#xa9; ")
    lang= forms.ChoiceField(widget=forms.Select, choices=LANG_CHOICES)
    text_content= forms.CharField(widget=forms.Textarea, label='Text')
    billboard= forms.ModelChoiceField(queryset=Billboard.objects.all(),
        label='Биллборд: ')
    historical_date_input= forms.CharField(required=False,
                                           label='Историческая дата ')
    historical_date= forms.CharField(required=False,
        widget=forms.TextInput(attrs={'size':'15'}), label='Отображаемая дата ')
    historical_place= forms.CharField(required=False,
        widget=forms.TextInput(attrs={'size':'20'}), label='Место ')
    comment= forms.CharField(required=False, label='Комментарий ',
	widget=forms.Textarea(attrs={'cols': 16, 'rows': 3}))

    def __init__(self, *args, **kwargs):
        initial= kwargs.pop('billboard', None)
        super(SceneForm, self).__init__(*args, **kwargs)
        if initial:
            self.fields['billboard'].initial= initial['billboard']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
        max_length=100, label='Пароль')
