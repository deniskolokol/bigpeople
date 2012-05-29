from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponse, Http404
from django.template import RequestContext
from calendar import monthrange
from math import ceil, floor
from PIL import Image
from os import path, remove
from datetime import date, datetime
import string
import random

from bigpeople import settings, urls
from bigpeople.browser import gridfsuploads, forms, models
from bigpeople.browser.gridfsuploads import gridfs_storage

numerals = zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'))


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


def celebrity_save(request, slug=None):
    """Save Celebrity record
    """
    if request.method == 'GET':
        raise Http404
    if request.POST.get('cancel', None):
        return redirect('/celebrity/')
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
        return redirect('/celebrity/')


def celebrity_delete(request, slug):
    """Delete Celebrity record and redirect back to referrer
    """
    celebrity= models.Celebrity.objects.get(slug=slug)
    try:
        celebrity.delete()
    except exception as e:
        pass
    return redirect(request.META.get('HTTP_REFERER'))


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


def scene_save(request, slug, scene_id=None):
    """Save current scene in the db
    """
    if request.method == 'GET':
        raise Http404
    if request.POST.get('cancel', None):
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


def define_scene(request, celebrity, index):
    """Fill the scene details from the request
    """
    lang= models.Language.objects.get(title=request.POST['lang'])
    billboard= None
    if request.POST.get('billboard', ''):
        billboard= models.Billboard.objects.get(id=request.POST['billboard'])        
    text= request.POST.get('text_content', '')
    date_input= request.POST.get('historical_date_input', None)
    date_input, date_db, date_bc= reformat_date(date_input)
    place= request.POST.get('historical_place', '')
    comment= request.POST.get('comment', '')
    media_src= request.POST.get('media_src', '')
    media_copyright= request.POST.get('media_copyright', '')
    dur= request.POST.get('text_dur_ms', 0) # Duration stored in milliseconds
    scene_lang= models.SceneLang(lang=lang, text=text, text_dur=dur)
    scene= models.Scene(scene_content= [scene_lang], billboard=billboard,
        media_src=media_src, media_copyright=media_copyright,
        historical_date_input=date_input, historical_date=date_db,
        historical_date_bc=date_bc, historical_place=place, comment=comment)
    media_content= request.FILES.get('media_content', None)
    if media_content:
	scene.media_content= media_content # NO SAVE UNTIL nginx WORKS!
        # scene.media_content_thumb= media_content_thumb # where to get it from?
        scene.media_url, scene.media_thumb_url= handle_uploaded_file(media_content)
    else: # The scene can already exist
        try:
            scene_old= celebrity.script[int(index)]
        except IndexError:
            scene_old= None
        if scene_old:
            scene.media_url= scene_old.media_url
            scene.media_thumb_url= scene_old.media_thumb_url
            scene.media_content= scene_old.media_thumb_url
            scene.media_content_thumb= scene_old.media_content_thumb
    return scene


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


def scene_details(request, slug, scene_id):
    pass


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



#----------
# Utilities
#----------

def id_generator(size=6, chars=string.ascii_lowercase+string.digits):
    """Generate unique filename to store in FS
    """
    return ''.join(random.choice(chars) for x in range(size))


def handle_uploaded_file(f):
    """Upload file to filesystem
    """
    ext= f.name.split('.')[-1]
    ext= '.'+ext if ext != f.name else '' # no extension
    filename= id_generator(settings.FILENAME_LEN)
    path= settings.MEDIA_ROOT + filename
    with open(path + ext, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    fileurl= settings.MEDIA_URL + filename + ext
    im= Image.open(path + ext) # Create thumbnail
    im.thumbnail(settings.THUMBNAIL_SIZE, Image.ANTIALIAS)
    thumbnail_name= filename + "_thumb" + ext
    thumbnail_path= path + "_thumb" + ext
    im.save(thumbnail_path, "JPEG")
    thumburl= settings.MEDIA_URL + thumbnail_name
    return fileurl, thumburl


def get_celeb_list():
    """Return sorted list of Celebrities' names
    """
    return models.Celebrity.objects.only('name', 'slug').order_by('name')


def get_page_title(lb):
    """Fill page title
    """
    page_ttl= settings.PROJECT_TITLE
    if lb:
        page_ttl += ': ' +  lb
    return page_ttl


def calc_seconds(ms):
    """Calculate seconds from milliseconds
    """
    return ms

def reformat_date(date_in):
    """Re-formatting the dates
    """
    date_iso, date_out, date_bc= None, '', False
    if date_in:
        m, d, y= (int(x) for x in date_in.split('/'))
        e= 'error'
        while e:
            try:
                date_iso= date(y, m, d).isoformat()
                e= None
            except ValueError as e:
                if y < 0:
                    y= abs(y) # year absolute value to meet ISO format
                    date_bc= True # flag it as B.C.
                m= min(abs(m), 12) # not more than 12 months
                d= min(abs(d), monthrange(y, m)[1])
        date_out= "%d.%02d.%04d" % (d, m, y)
        if date_bc: # for dates B.C. only year and century matters
            yr= int(date_iso[0:4]) # year B.C.
            century= int2roman(int(date_iso[0:2])+1) # century B.C.
            date_out= '%s (%s c.) B.C.' % (yr, century)
        if y < 1000: # for dates in the 1st century only year matters
            date_out= str(y)
    return date_iso, date_out, date_bc


def int2roman(i):
    """Converts integers to Roman literals
    """
    result= []
    for integer, numeral in numerals:
        count= int(i / integer)
        result.append(numeral * count)
        i -= integer * count
    return ''.join(result)


def roman2int(n):
    """Converts Roman literals to integers
    """
    n= unicode(n).upper()
    i= result = 0
    for integer, numeral in numerals:
        while n[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    return result
