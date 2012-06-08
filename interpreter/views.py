from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from datetime import datetime

from bigpeople.browser.decorators import interpreter_required
from bigpeople.browser import forms, models
from bigpeople.browser.utils import *


def celebrity_translate(request, **kwargs):
    """List of 'Celebrity' objects
    """
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])

    # WARNING! get only 'confirmed' celebrities
    celebrity= models.Celebrity.objects.filter(confirmed=True)
    message= ''
    if not celebrity:
        message= get_error_descr('empty_container', 'Russian')
    return render_to_response(page_template,
        {'celebrity': celebrity, 'uri': 'translate',
         'lang': get_user_lang(request.user),
         'display_form':display_form, 'message': message,
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))

@interpreter_required
def script_translate(request, slug, **kwargs):
    """View Celebrity Script
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celeblist= models.Celebrity.objects.filter(confirmed=True)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= fill_content_languages(celebrity, request.user)
    return render_to_response(page_template,
        {'celebrity': celebrity, 'celeblist': celeblist,
         'lang': get_user_lang(request.user), 'message': message,
         'page_title': get_page_title(celebrity.name)},
        context_instance=RequestContext(request))


@interpreter_required
def scene_translate(request, slug, scene_id, **kwargs):
    """Translate Scene
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= fill_content_languages(celebrity, request.user)
    initial= {'text_lang': ''}
    if scene_id:
        scene_id= int(scene_id)-1 # Django numbering starts at 1
        initial['text_lang']= celebrity.script[scene_id].lang_to_text
    else:
        raise Http404
    return render_to_response(page_template, {'scene_id': scene_id,
        'celebrity':celebrity, 'message':message, 'display_form':display_form,
        'page_title': get_page_title(celebrity.name),
        'lang': get_user_lang(request.user),
        'form':forms.ScriptTranslateForm(initial=initial)},
        context_instance=RequestContext(request))


def fill_content_languages(celebrity, user):
    """Extract Celebrity text in the default Language
    and in the User's Language.
    Warnings and errors are in the 'message' (list of tuples)
    """
    def _fill_content_lang(lang, label):
        success= True
        for scene in celebrity.script:
            content_lang= scene.get_scene_content(lang)
            if content_lang:
                setattr(scene, label+'_dur', content_lang.text_dur)
                setattr(scene, label+'_text', content_lang.text)
            else:
                setattr(scene, label+'_dur', 0)
                setattr(scene, label+'_text', '')
                success= False
        return success

    def _fill_content_empty(label):
        for scene in celebrity.script:
            setattr(scene, label+'_dur', 0)
            setattr(scene, label+'_text', '')

    message= []
    lang_default= get_default_language()
    success= _fill_content_lang(lang_default, 'lang_from')
    if not success:
        message.append(get_alert_descr('no_text_lang', lang=lang_default))
    
    lang_user= get_user_lang(user)
    if lang_user:
        if lang_default == lang_user:
            message.append(get_alert_descr('wrong_usr_lang', lang=lang_default))
            _fill_content_empty('lang_to')
        else:
            success= _fill_content_lang(lang_user, 'lang_to')
    else:
        message.append(get_alert_descr('no_usr_lang', lang=lang_default))
        _fill_content_empty('lang_to')

    return message


@interpreter_required
def save_translation(request, slug, scene_id, **kwargs):
    """Save translation for the current scene in the db
    """
    if request.method != 'POST':
        raise Http404
    else:
        form= forms.ScriptTranslateForm(request.POST)
    if 'cancel' in request.POST.keys():
        # return redirect(reverse('script_translate'))
        return redirect('/translate/'+slug, {'display_form': False})
    if scene_id:
        scene_id= int(scene_id)-1 # Django numbering starts at 1
    message= []
    if form.is_valid():
        celebrity= get_object_or_404(models.Celebrity, slug=slug)
        # if not celebrity.is_team_member(request.user):
        #     raise Http404 # Ban from action if not in the team
        scene= celebrity.script[scene_id]
        lang_user= get_user_lang(request.user)
        text = form.cleaned_data['text_lang']
        dur= form.cleaned_data['dur_lang']

        set_index= scene.set_lang_text(text, dur, lang_user)
        celebrity.last_edited_on= datetime.now()
        try:
            celebrity.save()
        except Exception as e:
            message= ('error', 'error', e)
        return redirect('/translate/'+slug, {'message': message})
    else:
        for err in form.errors:
            message.append(tuple(('error', 'Error!', err)))
        return redirect('/translate/'+slug, {'message': message})


@interpreter_required
def script_complete_translation(request, slug, **kwargs):
    """Sets the flag 'translated' to Celebrity
    """
    if request.method != 'POST':
        raise Http404
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= []
    lang_user= get_user_lang(request.user)
    success= True
    for scene in celebrity.script:
        if len(scene.scene_content) < 2:
            success= False # Content given only in the base language
            break
        else:
            scene_lang_content= scene.get_scene_content(lang_user)
            if scene_lang_content is None:
                success= False
                break
            else:
                if scene_lang_content.text.strip() == '':
                    success= False
                    break                    
    if success:
        if not celebrity.translated:
            celebrity.translated= []
        celebrity.translated.append(lang_user)
        try:
            celebrity.save()
            message.append(get_alert_descr('translation_complete',
                default_if_none=True))
        except Exception as e:
            message.append(('error', 'error', e))
    else:
        message.append(get_alert_descr('translation_not_complete',
            default_if_none=True))
    return redirect('/translate/'+slug, kwargs={'message': message})
    # return redirect(reverse('scene_translate', slug), kwargs={'message': message})


@interpreter_required
def script_revert_translation(request, slug, **kwargs):
    """Reset the flag 'translated' from Celebrity
    """
    if request.method != 'POST':
        raise Http404
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= []
    lang_user= get_user_lang(request.user)
    if lang_user in celebrity.translated:
        celebrity.translated.remove(lang_user)
        try:
            celebrity.save()
            message.append(get_alert_descr('translation_complete',
                default_if_none=True))
        except Exception as e:
            message.append(('error', 'error', e))
    return redirect('/translate/'+slug, kwargs={'message': message})
    # return redirect(reverse('scene_translate', slug), kwargs={'message': message})
