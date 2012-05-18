from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from datetime import date

from bigpeople import settings
from bigpeople.browser import forms
from bigpeople.browser import models as browser_model

def view_scenes(request, slug, **kwargs):
    """List of scenes in a Celebrity script.
    Look for Celebrity by the parameter 'slug'.
    """
    celebrity= get_object_or_404(browser_model.Celebrity, slug=slug)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
	page_template= '.'.join([page_template, 'html'])
    message= ''
    scene= celebrity.get_scene()
    if len(scene) == 0:
	message= 'No scenes in the script (yet?)'
    else: # Prepare container for display
	for current_scene in scene:
	    current_scene.dur= current_scene.text_content[0].dur
	    current_scene.text= current_scene.text_content[0].text
    return render_to_response(page_template, {'scene':scene,
	'celebrity':celebrity, 'message':message, 'display_form':display_form,
	'page_title': get_page_title(celebrity.name), 'form':forms.SceneForm},
	context_instance=RequestContext(request))


def save_scene(request, slug, scene_id):
    """Save current scene in the db
    """
    if request.method == 'GET':
	raise Http404
    celebrity= get_object_or_404(browser_model.Celebrity, slug=slug)
    media_content= request.FILES['media_content']
    lang= request.POST.get('lang', '')
    text_content= request.POST.get('text_content', '')
    historical_place= request.POST.get('historical_place', '')
    historical_date_input= request.POST.get('historical_date_input', '')
    comment= request.POST.get('comment', '')

    if lang:
    	lang= browser_model.Language.objects.get(title=lang)
    else:
    	pass # raise Error - no lang, no save

    lang_text= browser_model.SceneText(lang=lang, text=text_content, dur=1)

    celebrity_scene= browser_model.CelebrityScene(
	celebrity=celebrity, media_content=media_content,
	historical_date_input=historical_date_input,
	historical_place=historical_place, comment=comment,
	text_content= list([lang_text])
	)
    celebrity_scene.save()

    return render_to_response('test_static.html',
    	context_instance=RequestContext(request))


def scene_details(request, slug, scene_id):
    pass


def remove_scene(request, slug, scene_id):
    pass


def edit_scene(request, slug, scene_id):
    pass


def get_page_title(lb):
    """Fill page title
    """
    page_ttl= settings.PROJECT_TITLE
    if lb:
	page_ttl += ': ' +  lb

    return page_ttl
