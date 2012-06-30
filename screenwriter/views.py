# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

from bigpeople.browser import gridfsuploads, forms, models
from bigpeople.browser.decorators import screenwriter_required
from bigpeople.browser.gridfsuploads import gridfs_storage
from bigpeople.browser.utils import *
from bigpeople import settings, urls
from utils import *

@screenwriter_required
def celebrity_list(request, **kwargs):
    """List of 'Celebrity' objects
    """
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    celebrity= get_user_celebrities(request.user)
    message= request.session.pop('message', [])
    if not celebrity:
        message= get_alert_descr('empty_container', default_if_none=True)
    language= get_session_languages(request)
    return render_to_response(page_template,
        {'celebrity': celebrity, 'language': language,
         'display_form':display_form, 'message': message,
         'form':forms.CelebrityNameForm(initial={'name': ''}),
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@screenwriter_required
def celebrity_save(request, slug=None):
    """Save Celebrity record.
    """
    if request.method != 'POST':
        raise Http404
    if request.POST.get('cancel', None):
        return redirect(reverse('celebrity_list'))
    message= request.session.pop('message', [])
    form= forms.CelebrityNameForm(request.POST) # A form bound to the POST data.
    if form.is_valid(): # All validation rules pass.
        name= request.POST['name']
        if slug: # Save changes.
            celebrity= models.Celebrity.objects.get(slug=slug)
            celebrity.name= name
        else: # Insert new document.
            if models.Celebrity.objects.get(name=name): # Check if such redord already exists.
                message.append(get_alert_descr('already_exists',
                    default_if_none=True))
                request.session['message']= message
                return redirect(request.META.get('HTTP_REFERER'))
            celebrity= models.Celebrity(name=name)
        celebrity.name_lang= [] # Language specific names.
        language= models.Language.objects.all()
        for lang in language:
            id_name_lang= '_'.join(['name', lang.title.lower()])
            id_name_lang_aka= '_'.join(['name', lang.title.lower(), 'aka'])
            celebrity.name_lang.append(models.CelebrityName(lang=lang,
                name=request.POST.get(id_name_lang, '').strip(),
                name_aka=request.POST.get(id_name_lang_aka, '').strip()))
        celebrity.ensure_team_member(request.user)
        try:
            celebrity.save()
            message.append(get_alert_descr('save_successful',
                default_if_none=True))
        except Exception as e:
            message.append(('error', 'error', e))
        request.session['message']= message
        if request.POST.get('save_add', None):
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            return redirect(reverse('celebrity_list'))
    else:
        error= get_alert_descr('field_required', default_if_none=True)
        error= error[0:2] + (error[-1] % 'name',)
        message.append(error)
    request.session['message']= message
    if slug: # Save changes.
        return redirect(reverse(celebrity_edit, args=(slug,)))
    else: # Add new.
        return redirect(reverse('celebrity_list_form'))


@screenwriter_required
def celebrity_delete(request, slug):
    """Delete Celebrity record and redirect back to referrer
    """
    if request.method != 'POST':
        raise Http404
    celebrity= models.Celebrity.objects.get(slug=slug)
    try:
        celebrity.delete()
    except exception as e:
        pass
    return redirect(request.META.get('HTTP_REFERER'))


@screenwriter_required
def celebrity_edit(request, slug, **kwargs):
    """Edit Celebrity record
    """
    message= request.session.pop('message', [])
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    language= get_session_languages(request)
    celebrities= get_user_celebrities(request.user)
    try:
        celebrity= models.Celebrity.objects.only('name').get(slug=slug)
        initial={'name': celebrity.name}
    except:
        initial={'name': ''}
    return render_to_response(page_template,
        {'celebrity':celebrities, 'language':language, 'message': message,
         'display_form':display_form, 'slug':slug,
         'form':forms.CelebrityNameForm(initial=initial),
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@screenwriter_required
def celebrity_complete(request, slug):
    """Completes Celebrity record:
    - no more records can be added to the Script.
    - celebrity record cannot be edited.
    """
    if request.method != 'POST':
        raise Http404
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celebrity.completed= True
    message= []
    try:
        celebrity.save()
    except Exception as e:
        message.append(('error', 'error', e))
    return redirect(request.META.get('HTTP_REFERER'), {'message':message})


@staff_member_required
def celebrity_decline(request, slug):
    """Decline Celebrity record.
    Celebrity Script become editable again.
    """
    if request.method != 'POST':
        raise Http404
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celebrity.declined= True
    celebrity.completed= False
    celebrity.confirmed= False
    message=[]
    try:
        celebrity.save()
    except Exception as e:
        message.append(('error', 'error', e))
    return redirect(request.META.get('HTTP_REFERER'), {'message': message})


@staff_member_required
def celebrity_confirm(request, slug):
    """Confirm Celebrity record.
    """
    if request.method != 'POST':
        raise Http404
    if 'decline' in request.POST.keys():
        return celebrity_decline(request, slug)
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celebrity.declined= False
    celebrity.completed= True
    celebrity.confirmed= True
    message= []
    try:
        celebrity.save()
    except Exception as e:
        message.append(('error', 'error', e))
    return redirect(request.META.get('HTTP_REFERER'), {'message': message})


@screenwriter_required
def scene_list(request, slug, **kwargs):
    """List of scenes in a Celebrity script.
    Look for Celebrity by the parameter 'slug'.
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    if not celebrity.is_team_member(request.user):
        raise Http404 # Ban from view if not in the team
    display_form= kwargs.get('form', False)
    session_form= request.session.pop('session_form', None)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= request.session.pop('message', [])
    initial= {'lang': get_user_lang(request.user, default_if_none=True)}
    if not celebrity.script:
        celebrity.script= []
        message.append(get_alert_descr('empty_container', default_if_none=True))
    else: # Prepare container for display
        for scene in celebrity.script:
            scene_content_lang= scene.get_scene_content(initial['lang'])
            if scene_content_lang:
                scene.dur= scene_content_lang.text_dur
                scene.text= scene_content_lang.text
            # scene.gridfile= gridfs_storage.open(
            # settings.ROOT_PATH + scene.media_content.filename)
    if session_form is None:
        session_form= forms.SceneForm(initial=initial)
    return render_to_response(page_template,
        {'celebrity': celebrity, 'celeblist': get_user_celebrities(request.user),
         'form': session_form, 'display_form': display_form,
         'message': message, 'page_title': get_page_title(celebrity.name)},
        context_instance=RequestContext(request))


@screenwriter_required
def scene_edit(request, slug, scene_id, **kwargs):
    """Edit Scene in the script
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    display_form= kwargs.get('form', False)
    session_form= request.session.pop('session_form', None)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= request.session.pop('message', [])
    initial= {'lang': get_user_lang(request.user, default_if_none=True)}
    if not celebrity.script:
        celebrity.script= []
        message.append(get_alert_descr('empty_container', default_if_none=True))
    else: # Prepare container for display
        i= 0
        for scene in celebrity.script:
            scene_lang_content= scene.get_scene_content(initial['lang'])
            if scene_lang_content:
                scene.dur= scene_lang_content.text_dur
                scene.text= scene_lang_content.text
            if i == (int(scene_id)-1): # In case of edit.
                if session_form is None: # Re-display the form in case it was not valid.
                    initial.update({'media_src': scene.media_src,
                        'media_copyright': scene.media_copyright,
                        'text_content': scene.text, 'billboard': scene.billboard,
                        'historical_date_input': scene.historical_date_input,
                        'historical_date': scene.historical_date,
                        'historical_place': scene.historical_place,
                        'comment': scene.comment})
            i += 1
            # WARNING! add thumbnail from GridFS here
    if session_form is None:
        session_form= forms.SceneForm(initial=initial)
    return render_to_response(page_template, {'scene_id': int(scene_id),
        'celebrity': celebrity, 'message': message,
        'display_form': display_form, 'form': session_form,
        'page_title': get_page_title(celebrity.name),
        'lang': get_user_lang(request.user)},
        context_instance=RequestContext(request))


def define_scene(request, celebrity, index):
    """Fill the scene details from the request
    """
    # Billboard
    billboard= request.POST.get('billboard', '').strip()
    if billboard != '':
        billboard= models.Billboard.objects.get(id=billboard)
    else:
        billboard= None

    # Dates
    date_input= request.POST.get('historical_date_input', '')
    date_db= request.POST.get('historical_date', '')
    date_bc= request.POST.get('historical_date_bc', 0)
    if int(date_bc) == 1:
        date_bc= True
    else:
        date_bc= False
    if date_input == '': # Date cannot be empty string, but can be None
        date_input= None
    else:
        date_input, date_to_save, date_bc= reformat_date(date_input, date_bc)
        if date_db == '': # Re-format date only if the User didn't do it manually
            date_db= date_to_save

    # Place, text, comment
    place= request.POST.get('historical_place', '')
    text= request.POST.get('text_content', '')
    comment= request.POST.get('comment', '')

    # Scene media
    media_src= request.POST.get('media_src', '')
    media_copyright= request.POST.get('media_copyright', '')
    dur= request.POST.get('text_dur_ms', 0) # Duration stored in milliseconds

    # Language
    lang= request.POST.get('lang', '')
    if lang != '':
        lang= models.Language.objects.get(title=lang)
    else:
        lang= utils.get_user_lang(request.user, default_if_none=True)
    scene_lang= models.SceneLang(lang=lang, text=text, text_dur=dur)

    # Define object
    scene= models.Scene(
        scene_content= [scene_lang],
        billboard=billboard,
        media_src=media_src,
        media_copyright=media_copyright,
        historical_date_input=date_input,
        historical_date=date_db,
        historical_date_bc=date_bc,
        historical_place=place,
        comment=comment)

    # Scene media content
    media_content= request.FILES.get('media_content', None)
    is_image= int(request.POST['is_image'])
    scene.media_url, scene.media_thumb_url= None, None # Initial values
    if media_content:
	# scene.media_content= media_content # NO SAVE UNTIL nginx-gridfs WORKS!
        # scene.media_content_thumb= media_content_thumb # where to get it from?
        scene.media_url, scene.media_thumb_url= handle_uploaded_file(media_content)
        # WARNING!
        # If the scene is after edit, and there was file, but now is_image == 0,
        # the file should be deleted from the DB, and it's thumbnail - from HD.
        # If the image has changed, old files should be deleted both from DB and HD,
        # and substituted with new files.
    else: # The scene can already exist
        try:
            scene_old= celebrity.script[int(index)]
        except IndexError:
            scene_old= None
        if scene_old and is_image:
            scene.media_url= scene_old.media_url
            scene.media_thumb_url= scene_old.media_thumb_url
            scene.media_content= scene_old.media_content
            scene.media_content_thumb= scene_old.media_content_thumb
    return scene


@screenwriter_required
def scene_save(request, slug, scene_id=None):
    """Save current scene in the db
    """
    if request.method != 'POST':
        raise Http404
    if request.POST.get('cancel', None):
        # return redirect(reverse('scene_list'))
        return redirect('/celebrity/'+slug)
    if scene_id:
        scene_id0= int(scene_id)-1 # Django numbering starts at 1
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    if not celebrity.is_team_member(request.user):
        raise Http404 # Ban from action if not in the team
    message= request.session.pop('message', [])

    form= forms.SceneForm(request.POST) # A form bound to the POST data.
    is_valid= True
    if not form.is_valid(): # Some validation rules are specified in view.
        ignore_fields= ['lang', 'media_content', 'historical_date_input']
        for field in form.fields.keys():
            if (field in form.errors) and (field not in ignore_fields):
                is_valid= False
                break # One error field is enough to raise exception.
    if is_valid: # All validation rules pass.
        scene= define_scene(request, celebrity, scene_id0)
        try:
            celebrity.script[scene_id0]= scene
        except IndexError:
            celebrity.script.append(scene)
        celebrity.last_edited_on= datetime.now()
        try:
            celebrity.save()
            message.append(get_alert_descr('save_successful', default_if_none=True))
        except Exception as e:
            message.append(('error', 'error', e))
        request.session['message']= message
        if request.POST.get('save_add', None):
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            return redirect('/celebrity/'+slug)
    else:
        error= get_alert_descr('field_required', default_if_none=True)
        error= error[0:2] + (error[-1] % u"см. детали ниже",)
        message.append(error)
        request.session['message']= message
        request.session['session_form']= form
        print scene_id, len(celebrity.script)
        if int(scene_id) > len(celebrity.script): # New record
            return redirect(reverse(scene_list, args=(slug,)))
        else: # Edit record
            return redirect(reverse(scene_edit, args=(slug, scene_id)))


@screenwriter_required
def scene_move(request, slug, scene_id=None, **kwargs):
    """Save current scene in the db
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    page_template= kwargs.get('template', '')
    message= []
    if scene_id:
        dir= kwargs.get('dir', 1)
        scene_id= int(scene_id)-1 # django numbering starts at 1
        new_index= scene_id+int(dir)
        scene= celebrity.script.pop(scene_id)
        celebrity.script.insert(new_index, scene)
        try:
            celebrity.save()
        except Exception as e:
            message.append(('error', 'error', e))
    return redirect('/celebrity/'+slug, {'message': message})


@screenwriter_required
def scene_delete(request, slug, scene_id):
    """Delete Scene from Script
    """
    celebrity= models.Celebrity.objects.get(slug=slug)
    message= []
    try:
        celebrity.script.pop(int(scene_id)-1) # django counting starts at 1
        celebrity.save()
    except Exception as e:
        message.append(('error', 'error', e))
    return redirect(request.META.get('HTTP_REFERER'), {'message':message})
