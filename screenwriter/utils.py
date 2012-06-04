# -*- coding: utf-8 -*-

from calendar import monthrange
from math import ceil, floor
from PIL import Image
from os import path, remove
from datetime import date, datetime, MAXYEAR
import string
import random

from bigpeople import settings
from bigpeople.browser import gridfsuploads, forms, models, utils
from bigpeople.browser.gridfsuploads import gridfs_storage


numerals = zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'))



# Processing data.

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
	scene.media_content= media_content # NO SAVE UNTIL nginx WORKS!
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
            scene.media_content= scene_old.media_thumb_url
            scene.media_content_thumb= scene_old.media_content_thumb
    return scene


# Utilities.

def id_generator(size=6, chars=string.ascii_lowercase+string.digits):
    """Generate unique filename to store in FS.
    """
    return ''.join(random.choice(chars) for x in range(size))


def handle_uploaded_file(f):
    """Upload file to filesystem.
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
    thumbnail_name= filename + "_thumb.jpg"
    thumbnail_path= path + "_thumb.jpg"
    im.save(thumbnail_path, "JPEG")
    thumburl= settings.MEDIA_URL + thumbnail_name
    return fileurl, thumburl


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

def reformat_date(date_in, date_bc):
    """Re-formatting the dates
    """
    date_iso, date_out= None, ''
    if date_in:
        # Parsing date.
        delimiters= ['/', '-', '.', ':', '\\']
        e= 'error'
        for delimiter in delimiters:
            try:
                d, m, y= (int(x) for x in date_in.split(delimiter))
                e= None
                break
            except ValueError as e:
                pass
        if e: # Date formatted real bad.
            return None, '', False

        # ISO formatting.
        e= 'error'
        while e:
            try:
                date_iso= date(y, m, d).isoformat()
                e= None
            except ValueError as e:
                if y < 0:
                    y= abs(y) # year absolute value to meet ISO format
                    if not date_bc:
                        date_bc= True # the year is negative, flag it as B.C.
                elif y > MAXYEAR:
                    y= MAXYEAR
                m= min(abs(m), 12) # not more than 12 months
                d= min(abs(d), monthrange(y, m)[1])
        date_out= "%d.%02d.%04d" % (d, m, y)
        if date_bc: # for dates B.C. only year and century matters
            yr= int(date_iso[0:4]) # year B.C.
            century= int2roman(int(date_iso[0:2])+1) # century B.C.
            date_out= '%s (%s в.) до н.э.' % (yr, century)
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
