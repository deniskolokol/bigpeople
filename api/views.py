#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson as json

from bigpeople.browser import models
from bigpeople.browser.utils import get_default_language

lang_default= get_default_language()

def get_description(request):
    """General description and next URL
    """
    result= {'description': 'Big People API',
        'this_uri': request.build_absolute_uri(),
        'language': [], 'status': 'OK'}
    result.update({'uri': {'celebrity': result['this_uri']+'celebrity/',
        'billboard': result['this_uri']+'billboard/'}})

    for lang in models.Language.objects.all():
        result['language'].append(
            " %s (%s)" % (lang.title.strip(), lang.title_orig.strip()))
    return HttpResponse(json.dumps(result, ensure_ascii=False, encoding='utf-8'), 'application/json')


def get_billboard_list(request):
    """List of billboards from the database
    """
    result= {'billboard': []}
    result['this_uri']= request.build_absolute_uri()
    for billboard in models.Billboard.objects.all().order_by('title'):
        result['billboard'].append({'title': billboard.title,
            'uri': result['this_uri'] + billboard.pk})
    if result['billboard']:
        result['status']= 'OK'
    else:
        result['status']= 'EMPTY_SET'
    return HttpResponse(json.dumps(
        result, ensure_ascii=False, encoding='utf-8'), 'application/json')


def get_billboard(request, id):
    """Billboard specific record details
    """
    result= {'billboard': {'_id':id}}
    try:
        billboard= models.Billboard.objects.get(pk=id)
    except Exception as e:
        billboard= None
    if billboard:
        result.update({'title': billboard.title, 'body': billboard.body,
            'dur_in': billboard.dur_in, 'dur_out': billboard.dur_out})
        result['status']= 'OK'
    else:
        result['billboard']= e.message
        result['status']= 'ERROR'
    return HttpResponse(json.dumps(
        result, ensure_ascii=False, encoding='utf-8'), 'application/json')

def get_celebrity_list(request):
    """List of confirmed Celebrities
    """
    result= {'celebrity': []}
    result['this_uri']= request.build_absolute_uri()
    for celeb in models.Celebrity.objects.only('name', 'slug').filter(confirmed=True).order_by('name'):
        result['celebrity'].append({'name': celeb.name,
            'slug': celeb.slug, 'uri': request.build_absolute_uri() + celeb.slug})
    if result['celebrity']:
        result['status']= 'OK'
    else:
        result['status']= 'EMPTY_SET'
    return HttpResponse(json.dumps(result, ensure_ascii=False, encoding='utf-8'), 'application/json')


def get_celebrity_lang(request, slug):
    """List of the Languages, in which
    Scripts of the Celebrity exist
    """

    def _fill_lang_dict(lang):
        return {
            'title': lang.title.strip().lower(),
            'title_orig': lang.title_orig.strip().lower(),
            'uri': result['this_uri'] + lang.title.strip().lower() + '/'
            }

    result= {'celebrity': {}}
    result['this_uri']= request.build_absolute_uri()
    try:
        celeb= models.Celebrity.objects.only('name', 'slug',
            'translated').get(confirmed=True, slug=slug)
    except Exception as e:
        celeb= None
    if celeb:                  # If Celebrity record is confirmed, the script
        result['celebrity']= { # exists at least in the default language.
            'name': celeb.name,
            'language': [_fill_lang_dict(lang_default)]
            }
        for lang in celeb.translated:
            result['celebrity']['language'].append(_fill_lang_dict(lang))
        result['status']= 'OK'
    else:
        result['celebrity']= e.message
        result['status']= 'ERROR'
        
    return HttpResponse(json.dumps(result, ensure_ascii=False, encoding='utf-8'), 'application/json')


def get_celebrity_lang_script(request, slug, lang):
    """Scenes of the Script of the Celebrity
    and Language specific names
    """
    result= {'celebrity': {}}
    result['this_uri']= request.build_absolute_uri()
    try:
        celeb= models.Celebrity.objects.only('name', 'name_lang', 'script'
            ).get(confirmed=True, slug=slug)
    except Exception as e:
        celeb= None
    if celeb:
        try:
            language= models.Language.objects.get(title__icontains=lang.strip())
        except Exception as e:
            language= None
        if language:
            lang_title= language.title.strip().lower()
            if request.is_secure():
                prefix= 'https://'
            else:
                prefix= 'http://'
            if (language in celeb.translated) or (language == lang_default):
                result['celebrity'][lang_title]= {
                    'name': '',
                    'name_aka': '',
                    'script': []
                    }
                for name_lang in celeb.name_lang:
                    if name_lang.lang == language:
                        result['celebrity'][lang_title]['name']= name_lang.name
                        result['celebrity'][lang_title]['name_aka']= name_lang.name_aka
                        break
                total_dur= 0
                for scene in celeb.script:
                    for scene_content in scene.scene_content:
                        if scene_content.lang != language:
                            continue
                        else:
                            result['celebrity'][lang_title]['script'].append({
                                'text': scene_content.text,
                                'dur': scene_content.text_dur,
                                'media_url': ''.join([prefix, request.get_host(),
                                    scene.media_url]),
                                'billboard': ''.join([prefix, request.get_host(),
                                    '/api/billboard/', scene.billboard.pk])
                                })
                            total_dur += int(scene_content.text_dur)
                            break
                result['celebrity'][lang_title]['total_dur']= total_dur
                result['status']= 'OK'
            else:
                result['status']= 'EMPTY_SET'
        else:
            result['celebrity']= e.message
            result['status']= 'ERROR'
    else:
        result['celebrity']= e.message
        result['status']= 'ERROR'

    return HttpResponse(json.dumps(result, ensure_ascii=False, encoding='utf-8'), 'application/json')
