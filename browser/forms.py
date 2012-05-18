from django import forms
from models import Billboard, Language

LANG_CHOICES= tuple((e.title, e.title_orig) for e in Language.objects.all())

class SceneForm(forms.Form):
    media_content= forms.FileField(label='Choose a picture',
				   widget=forms.FileInput)
    lang= forms.ChoiceField(widget=forms.Select, choices=LANG_CHOICES)
    text_content= forms.CharField(widget=forms.Textarea, label='Text')
    historical_date_input= forms.CharField(required=False, label='Date')
    historical_place= forms.CharField(required=False, label='Place')
    comment= forms.CharField(required=False, widget=forms.Textarea,
			     label='Comment')
