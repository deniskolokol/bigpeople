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
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail(settings.THUMBNAIL_SIZE, Image.ANTIALIAS)
    thumbnail_name= filename + "_thumb.jpg"
    thumbnail_path= path + "_thumb.jpg"
    im.save(thumbnail_path, "JPEG")
    thumburl= settings.MEDIA_URL + thumbnail_name
    return fileurl, thumburl


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
