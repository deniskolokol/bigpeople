# -*- coding: utf-8 -*-

from django import forms
from models import Billboard, Language

LANG_CHOICES= tuple((e.title, e.title_orig) for e in Language.objects.all())

class SceneForm(forms.Form):
    media_content= forms.FileField(widget=forms.FileInput)
    media_src= forms.URLField(required=False, label="Источник ")
    media_copyright= forms.CharField(required=False, label="&#xa9; ")
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


class ScriptTranslateForm(forms.Form):
    """Main form for translating the text
    """
    text_lang= forms.CharField(required=False, label='Перевод ',
        widget=forms.Textarea(attrs={'class':'span6',
            'name': 'text_lang',
            'onKeyDown': """textDurCount(
                document.actions_edit.text_lang,
                document.actions_edit.dur_lang,
                document.actions_edit.dur_lang_pretty,
                document.getElementById('tableCNTR'),
                document.getElementById('id_raw_dur_total'),
                document.getElementById('id_text_dur_total'))""",
            'onKeyUp': """textDurCount(
                document.actions_edit.text_lang,
                document.actions_edit.dur_lang,
                document.actions_edit.dur_lang_pretty,
                document.getElementById('tableCNTR'),
                document.getElementById('id_raw_dur_total'),
                document.getElementById('id_text_dur_total'))"""}))
    dur_lang= forms.CharField(required=True, label="Хронометраж ",
        widget=forms.TextInput(attrs={
            'class': 'span2 hide', 'name': 'dur_lang'}))
    dur_lang_pretty= forms.CharField(required=False, # Dur pretty print
        widget=forms.TextInput(attrs={
            'class': 'span2', 'name': 'dur_lang_pretty', 'readonly':''}))

    def __init__(self, *args, **kwargs):
        initial= kwargs.pop('text_lang', None)
        super(ScriptTranslateForm, self).__init__(*args, **kwargs)
        if initial:
            self.fields['text_lang'].initial= initial['text_lang']


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
        max_length=100, label='Пароль')
