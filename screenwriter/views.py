from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test

from bigpeople.browser import gridfsuploads, forms, models
from bigpeople.browser.decorators import screenwriter_required
from bigpeople.browser.gridfsuploads import gridfs_storage
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
    message= ''
    celebrity= models.Celebrity.objects.all().order_by('created_on')
    if not celebrity:
        message= 'No records (yet?)'
    language= models.Language.objects.all()
    return render_to_response(page_template,
        {'celebrity':celebrity, 'language':language, 'message':message,
         'display_form':display_form,
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@screenwriter_required
def celebrity_save(request, slug=None):
    """Save Celebrity record
    """
    if request.method == 'GET':
        raise Http404
    if request.POST.get('cancel', None):
        return redirect(reverse('celebrity_list'))
    name= request.POST.get('name', '').strip()
    if not name:
        pass # raise error - no name no save
    if slug:
        celebrity= models.Celebrity.objects.get(slug=slug)
        celebrity.name= name
    else:
        celebrity= models.Celebrity(name=name)
    celebrity.name_lang= [] # Language specific names
    language= models.Language.objects.all()
    for lang in language:
        id_name_lang= '_'.join(['name', lang.title.lower()])
        id_name_lang_aka= '_'.join(['name', lang.title.lower(), 'aka'])
        celebrity.name_lang.append(models.CelebrityName(lang=lang,
            name=request.POST.get(id_name_lang, '').strip(),
            name_aka=request.POST.get(id_name_lang_aka, '').strip()))
    try:
        celebrity.save()
        message= 'Celebrity %s saved!' % name
    except Exception as e:
        message= e #'ERROR! Celebrity %s not saved - name must be unique!' % name
    if request.POST.get('save_add', None):
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect(reverse('celebrity_list'))


@screenwriter_required
def celebrity_delete(request, slug):
    """Delete Celebrity record and redirect back to referrer
    """
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
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    celebrity= models.Celebrity.objects.all()
    language= models.Language.objects.all()
    return render_to_response(page_template,
        {'celebrity':celebrity, 'language':language,
         'display_form':display_form, 'slug':slug,
         'page_title': get_page_title('List of Celebrities')},
        context_instance=RequestContext(request))


@screenwriter_required
def celebrity_complete(request, slug):
    """Finalizes Celebrity record:
    - no more records can be added to the Script.
    - celebrity record cannot be edited.
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    celebrity.ready_to_assemble= True
    message=""
    try:
        celebrity.save()
    except Exception as e:
        message= e # WARNING! process exception
    return redirect(request.META.get('HTTP_REFERER'), {'message':message})


@screenwriter_required
def scene_list(request, slug, **kwargs):
    """List of scenes in a Celebrity script.
    Look for Celebrity by the parameter 'slug'.
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= ''
    if not celebrity.script:
        celebrity.script= []
        message= 'No scenes in the script (yet?)'
    else: # Prepare container for display
        for scene in celebrity.script:
            scene.dur= scene.scene_content[0].text_dur
            scene.text= scene.scene_content[0].text
            # scene.gridfile= gridfs_storage.open(
            # settings.ROOT_PATH + scene.media_content.filename)
    return render_to_response(page_template,
        {'celebrity': celebrity, 'celeblist': get_celeb_list(),
         'form': forms.SceneForm, 'display_form': display_form,
         'message': message, 'page_title': get_page_title(celebrity.name)},
        context_instance=RequestContext(request))


@screenwriter_required
def scene_save(request, slug, scene_id=None):
    """Save current scene in the db
    """
    if request.method == 'GET':
        raise Http404
    if request.POST.get('cancel', None):
        # return redirect(reverse('scene_list'))
        return redirect('/celebrity/'+slug)
    if scene_id:
        scene_id= int(scene_id)-1 # django numbering starts at 1
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    scene= define_scene(request, celebrity, scene_id)
    try:
        celebrity.script[scene_id]= scene
    except IndexError:
        celebrity.script.append(scene)
    celebrity.last_edited_on= datetime.now()
    message= "Scene successfully saved"
    try:
        celebrity.save()
    except Exception as e:
        message= e # WARNING! process exception
    if request.POST.get('save_add', None):
        return redirect(request.META.get('HTTP_REFERER'), {'message':message})
    else:
        return redirect('/celebrity/'+slug)


@screenwriter_required
def scene_move(request, slug, scene_id=None, **kwargs):
    """Save current scene in the db
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    page_template= kwargs.get('template', '')
    message= ''
    if scene_id:
        dir= kwargs.get('dir', 1)
        scene_id= int(scene_id)-1 # django numbering starts at 1
        new_index= scene_id+int(dir)
        scene= celebrity.script.pop(scene_id)
        celebrity.script.insert(new_index, scene)
        try:
            celebrity.save()
        except Exception as e:
            message= e
    return redirect('/celebrity/'+slug, {'message':message})


@screenwriter_required
def scene_delete(request, slug, scene_id):
    """Delete Scene from Script
    """
    celebrity= models.Celebrity.objects.get(slug=slug)
    message= ''
    try:
        celebrity.script.pop(int(scene_id)-1) # django counting starts at 1
        celebrity.save()
    except exception as e:
        message= e
    return redirect(request.META.get('HTTP_REFERER'), {'message':message})


@screenwriter_required
def scene_edit(request, slug, scene_id, **kwargs):
    """Edit Scene in the script
    """
    celebrity= get_object_or_404(models.Celebrity, slug=slug)
    display_form= kwargs.get('form', False)
    page_template= kwargs.get('template', '')
    if page_template:
        page_template= '.'.join([page_template, 'html'])
    message= ''
    if not celebrity.script:
        celebrity.script= []
        message= 'No scenes in the script (yet?)'
    else: # Prepare container for display
        i, billboard= 0, None
        for scene in celebrity.script:
            scene.dur= scene.scene_content[0].text_dur
            scene.text= scene.scene_content[0].text
            if i == (int(scene_id)-1): # In case it is for edit
                billboard= scene.billboard # grab billboard for display initial
            i += 1
            # WARNING! add thumbnail from GridFS here
    return render_to_response(page_template, {'scene_id':int(scene_id),
        'celebrity':celebrity, 'message':message, 'display_form':display_form,
        'page_title': get_page_title(celebrity.name),
        'form':forms.SceneForm(initial={'billboard':billboard})},
        context_instance=RequestContext(request))
