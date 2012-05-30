from calendar import monthrange
from math import ceil, floor
from PIL import Image
from os import path, remove
from datetime import date, datetime
import string
import random

from bigpeople import settings
from bigpeople.browser import gridfsuploads, forms, models
from bigpeople.browser.gridfsuploads import gridfs_storage


numerals = zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'))

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
