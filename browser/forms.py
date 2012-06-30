# -*- coding: utf-8 -*-

from django import forms
from models import Billboard, Language

LANG_CHOICES= tuple((e.title, e.title_orig) for e in Language.objects.all())


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput(render_value=False),
        max_length=100, label='Пароль')


class CelebrityNameForm(forms.Form):
    name= forms.CharField(max_length=400, label="Имя")

    def __init__(self, *args, **kwargs):
        initial= kwargs.pop('name', None)
        super(CelebrityNameForm, self).__init__(*args, **kwargs)
        if initial:
            self.fields['name'].initial= initial['name']


class SceneForm(forms.Form):
    lang= forms.CharField(widget=forms.TextInput(attrs={
        'class': 'span2', 'id': 'id_lang', 'readonly':''}))
    media_content= forms.ImageField(widget=forms.ClearableFileInput(attrs={
        'class': 'span2', 'id': 'id_media_content', 'size': '10',
        'onchange': "document.getElementById('isimage').value = '1';"}))
    media_src= forms.URLField(required=False, widget=forms.TextInput(attrs={
        'class': 'span2', 'id': 'id_media_src'}), label='URL')
    media_copyright= forms.CharField(widget=forms.TextInput(attrs={
        'class': 'span2', 'id': 'id_media_copyright'}), label='©')
    text_content= forms.CharField(widget=forms.Textarea(attrs={
        'class':'span4',
        'onKeyDown': """textDurCount(
            document.formAddScene.text_content,
            document.formAddScene.text_dur_ms,
            document.formAddScene.text_dur,
            document.getElementById('tableCNTR'),
            document.getElementById('id_raw_dur_total'),
            document.getElementById('id_text_dur_total'))""",
        'onKeyUp': """textDurCount(
            document.formAddScene.text_content,
            document.formAddScene.text_dur_ms,
            document.formAddScene.text_dur,
            document.getElementById('tableCNTR'),
            document.getElementById('id_raw_dur_total'),
            document.getElementById('id_text_dur_total'))"""}),
        label='Текст')
    billboard= forms.ModelChoiceField(
        queryset=Billboard.objects.all().order_by('title'), label='Биллборд')
    historical_date_input= forms.DateField(required=False,
        widget=forms.DateInput(attrs={'class': 'span2',
            'id': 'inputDate', 'data-date-format': "dd/mm/yyyy", 'size': '15'}),
        label='Историческая дата (dd/mm/[-]yyyy)',
        input_formats=('%d/%m/%Y',))
    historical_date= forms.CharField(required=False,
        widget=forms.TextInput(attrs={'id': 'id_historical_date', 'size':'15'}),
        label='Отображаемая дата')
    historical_place= forms.CharField(required=False,
        widget=forms.TextInput(attrs={'id': 'id_historical_place', 'size':'20'}),
        label='Историческое место')
    comment= forms.CharField(required=False, label='Комментарий',
	widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        initial= kwargs.pop('billboard', None)
        super(SceneForm, self).__init__(*args, **kwargs)
        if initial:
            for field in self.fields:
                try:
                    self.fields[field].initial= initial[field]
                except:
                    pass # Just ignore, if there's no initial value


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
