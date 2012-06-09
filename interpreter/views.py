from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from datetime import datetime

from bigpeople.browser.decorators import interpreter_required, is_interpreter
from bigpeople.browser import forms, models
from bigpeople.browser.utils import *
from bigpeople import settings


def get_available_celebrities(user):
    """Celebrity is considered to be available for an interpreter,
    if the record meets 3 creterias:
    - is 'comfirmed'
    AND
    (- user is in the 'team'
      OR
     - no other interpreter is in the 'team' with the same Language)

    Also setting up celebrity.interpreter for display in the table
    """
    result_set= []
    user_lang= get_user_lang(user)
    confirmed_celebrities= models.Celebrity.objects.filter(confirmed=True)
    for celebrity in confirmed_celebrities:
        if celebrity.is_team_member(user):
            if user.is_staff:
                for team_member in celebrity.team:
                    if is_interpreter(team_member.user):
                        setattr(celebrity, 'interpreter',
                                team_member.user.get_full_name())
                        break
            else:
                setattr(celebrity, 'interpreter', user.get_full_name())
            result_set.append(celebrity)
        else:
            lang_interpreters= False
            for team_member in celebrity.team:
                if (team_member.lang == user_lang) and is_interpreter(team_member.user):
                    lang_interpreters= True
                    break
            if not lang_interpreters:
                setattr(celebrity, 'interpreter', '')
                result_set.append(celebrity)
    return result_set


@interpreter_required
def celebrity_translate(request, **kwargs):
    """List of 'Celebrity' objects
    """
    message= request.session.pop('message', [])
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    celebrity= get_available_celebrities(request.user)
    if not celebrity:
        message.append(get_alert_descr('empty_container', default_if_none=True))
    return render_to_response(page_template,
        {'celebrity': celebrity, 'uri': 'translate',
         'lang': get_user_lang(request.user),
         'display_form':display_form, 'message': message,
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@interpreter_required
def celebrity_translate_edit(request, slug, **kwargs):
    """List of 'Celebrity' objects
    """
    message= request.session.pop('message', [])
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celeblist= get_available_celebrities(request.user)
    if not celeblist:
        message.append(get_alert_descr('empty_container',
                default_if_none=True))
    if celebrity not in celeblist:
        message.append(get_alert_descr('not_in_team', default_if_none=True))
        request.session['message']= message
        return redirect(reverse('celebrity_translate'))
    language= get_session_languages(request)
    return render_to_response(page_template,
        {'celebrity': celeblist, 'language': language,
         'lang': get_user_lang(request.user), 'slug':slug,
         'display_form': display_form, 'message': message,
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@interpreter_required
def celebrity_translate_save(request, slug, **kwargs):
    """Save Celebrity record (language specific names)
    """
    def _get_form_data_lang(lang):
        id_name_lang= '_'.join(['name', lang.title.lower()])
        id_name_lang_aka= '_'.join(['name', lang.title.lower(), 'aka'])
        name=request.POST.get(id_name_lang, '').strip()
        name_aka=request.POST.get(id_name_lang_aka, '').strip()
        return name, name_aka
    
    if request.method != 'POST':
        raise Http404
    if request.POST.get('cancel', None):
        return redirect(reverse('celebrity_translate'))
    message= request.session.pop('message', [])
    celebrity= models.Celebrity.objects.get(slug=slug)

    if request.user.is_staff: # Staff members save names in all languages
        celebrity.name_lang= []
        for language in models.Language.objects.all():
            name, name_aka= _get_form_data_lang(language)
            celebrity.name_lang.append(models.CelebrityName(lang=language,
                name=name, name_aka=name_aka))
    else: # Ordinary user can only save name in designated language
        user_lang= get_user_lang(request.user)
        name, name_aka= _get_form_data_lang(user_lang)
        name_lang_new= models.CelebrityName(lang=user_lang,
            name=name, name_aka=name_aka)
        celebrity_name_lang= []
        for name_lang in celebrity.name_lang:
            if name_lang.lang == user_lang:
                celebrity_name_lang.append(name_lang_new)
            else:
                celebrity_name_lang.append(name_lang)
        celebrity.name_lang= celebrity_name_lang
    try:
        celebrity.save()
        message.append(get_alert_descr('save_successful', default_if_none=True))
    except Exception as e:
        message.append(('error', 'error', e))
    request.session['message']= message
    return redirect(reverse('celebrity_translate'))


@interpreter_required
def script_translate(request, slug, **kwargs):
    """View Celebrity Script
    """
    message= request.session.pop('message', [])
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celeblist= get_available_celebrities(request.user)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message.extend(fill_content_languages(celebrity, request.user))
    return render_to_response(page_template,
        {'celebrity': celebrity, 'celeblist': celeblist,
         'lang': get_user_lang(request.user), 'message': message,
         'page_title': get_page_title(celebrity.name)},
        context_instance=RequestContext(request))


@interpreter_required
def scene_translate(request, slug, scene_id, **kwargs):
    """Translate Scene
    """
    message= request.session.pop('message', [])
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celeblist= get_available_celebrities(request.user)
    if celebrity not in celeblist:
        message.append(get_alert_descr('not_in_team', default_if_none=True))
        request.session['message']= message
        return redirect(reverse('celebrity_translate'))
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
    return render_to_response(page_template, {'display_form': display_form,
        'celebrity': celebrity, 'scene_id': scene_id, 'message': message,
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
    """Save current scene translation
    """
    if request.method != 'POST':
        raise Http404
    else:
        form= forms.ScriptTranslateForm(request.POST)
    if 'cancel' in request.POST.keys():
        return redirect('/translate/'+slug, {'display_form': False})
    if scene_id:
        scene_id= int(scene_id)-1 # Django numbering starts at 1
    message= request.session.pop('message', [])
    if form.is_valid():
        celebrity= get_object_or_404(models.Celebrity, slug=slug)
        scene= celebrity.script[scene_id]
        lang_user= get_user_lang(request.user)
        text = form.cleaned_data['text_lang']
        dur= form.cleaned_data['dur_lang']

        set_index= scene.set_lang_text(text, dur, lang_user)
        celebrity.last_edited_on= datetime.now()
        if celebrity.ensure_team_member(request.user):
            try:
                celebrity.save()
                message.append(get_alert_descr('save_successful',
                    default_if_none=True))
            except Exception as e:
                message= ('error', 'Error!', e)
        else: # User is not a part of team, and cannot be one
            message.append(get_alert_descr('not_in_team',
                default_if_none=True))
    else:
        for err in form.errors:
            message.append(tuple(('error', 'Error!', err)))
    request.session['message']= message
    return redirect('/translate/'+slug, {'display_form': False})


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
    total_dur= 0
    # Empty records check
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
                # Summing up dur for the next check
                total_dur += scene_lang_content.text_dur
                if scene_lang_content.text.strip() == '':
                    success= False
                    break                    
    if success:
        # Duration check
        if (total_dur < settings.TEXT_DUR_FLOOR) or (total_dur > settings.TEXT_DUR_CEIL):
            error= get_alert_descr('text_dur_error', default_if_none=True)
            floor_minutes, floor_milliseconds= divmod(settings.TEXT_DUR_FLOOR, 60000)
            floor_seconds= float(floor_milliseconds) / 1000
            ceil_minutes, ceil_milliseconds= divmod(settings.TEXT_DUR_CEIL, 60000)
            ceil_seconds= float(ceil_milliseconds) / 1000
            error= error[0:2] + (error[-1] % (
                floor_minutes, floor_seconds, ceil_minutes, ceil_seconds),)
            message.append(error)
        else:
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
    request.session['message']= message
    return redirect(reverse(script_translate, args=(slug,)))


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
    # return redirect(reverse('script_translate', slug), kwargs={'message': message})
