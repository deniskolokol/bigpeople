from django import forms
from models import Billboard, Language

LANG_CHOICES= tuple((e.title, e.title_orig) for e in Language.objects.all())

class SceneForm(forms.Form):
    media_content= forms.FileField(label='Choose a picture',
	widget=forms.FileInput)
    media_src= forms.URLField(required=False, help_text="Media URL")
    media_copyright= forms.CharField(required=False, help_text="Media (C)")
    lang= forms.ChoiceField(widget=forms.Select, choices=LANG_CHOICES)
    text_content= forms.CharField(widget=forms.Textarea, label='Text')
    billboard= forms.ModelChoiceField(queryset=Billboard.objects.all(),
        label='Billboard')
    historical_date_input= forms.CharField(required=False, label='Date')
    historical_place= forms.CharField(required=False, label='Place')
    comment= forms.CharField(required=False,
	widget=forms.Textarea(attrs={'cols': 16, 'rows': 5}),
	label='Comment')

    def __init__(self, *args, **kwargs):
        print args, kwargs
        initial= kwargs.pop('billboard', None)
        super(SceneForm, self).__init__(*args, **kwargs)
        if initial:
            self.fields['billboard'].initial= initial['billboard']
