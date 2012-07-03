#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.utils import simplejson as json

from bigpeople.browser import models
from bigpeople.browser.utils import get_default_language

lang_default= get_default_language()

def is_include_all(rq):
    """Catch ?all=true flag
    """
    all_flag= rq.GET.get('all', False)
    if str(all_flag).strip().upper() in ['1', 'YES', 'Y', 'TRUE', 'T']:
        return True
    else:
        return False
        

def get_description(request):
    """General description and next URL
    """
    result= {'description': 'Big People API',
        'this_uri': request.build_absolute_uri(),
        'language': [], 'status': 'OK'}
    result.update({'uri': {'celebrity': result['this_uri']+'celebrity/',
        'billboard': result['this_uri']+'billboard/'}})

    for lang in models.Language.objects.all():
        result['language'].append({'title': lang.title.strip(),
            'title_orig': lang.title_orig.strip()})
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
    if is_include_all(request): # All records.
        dataset= models.Celebrity.objects.only('name', 'slug').all().order_by('name')
    else: # Only confirmed records.
        dataset= models.Celebrity.objects.only('name', 'slug').filter(confirmed=True).order_by('name')
    for celeb in dataset:
        clean_celeb_uri= request.build_absolute_uri().split('?')[0]
        result['celebrity'].append({'name': celeb.name,
            'slug': celeb.slug, 'uri': clean_celeb_uri + celeb.slug,
            'confirmed': str(celeb.confirmed).lower()})
    if result['celebrity']:
        result['status']= 'OK'
    else:
        result['status']= 'EMPTY_SET'
    return HttpResponse(json.dumps(result, ensure_ascii=False, encoding='utf-8'), 'application/json')


def get_celebrity_lang_user(celeb, lang):
    """Get the full name of the User,
    who created/interpreted Celebrity
    in a certain Language.
    """
    print type(celeb), type(lang)
    for team_member in celeb.team:
        if team_member.lang == lang:
            return team_member.user.get_full_name()
    return ''
            

def get_celebrity_lang(request, slug):
    """List of the Languages, in which
    Scripts of the Celebrity exist
    """

    def _fill_lang_dict(lang):
        return {
            'title': lang.title.strip().lower(),
            'title_orig': lang.title_orig.strip().lower(),
            'uri': result['this_uri'].split('?')[0] + lang.title.strip().lower() + '/'
            }

    result= {'celebrity': {}}
    result['this_uri']= request.build_absolute_uri()
    try:
        celeb= models.Celebrity.objects.get(slug=slug)
    except Exception as e:
        celeb= None
    if celeb:
        result['celebrity']['language']= []
        if is_include_all(request): # All records.
            dataset= models.Language.objects.all()
        else: # Only confirmed records.
            dataset= celeb.translated
            if celeb.confirmed:
                dataset.append(lang_default) # Default language doesn't show up in .translated
        for lang in dataset:
            lang_dict= _fill_lang_dict(lang)
            lang_dict.update({'user': get_celebrity_lang_user(celeb, lang),
                'completed': 'false'})
            if lang == lang_default:
                lang_dict.update({'completed': str(celeb.confirmed).lower()})
            else:
                if lang in celeb.translated:
                    lang_dict.update({'completed': 'true'})
            result['celebrity']['language'].append(lang_dict)
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
        celeb= models.Celebrity.objects.get(slug=slug)
    except Exception as e:
        celeb= None
    if celeb:
        result['celebrity'].update({'name': celeb.name, 'slug': celeb.slug})
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
            if is_include_all(request):
                check= True
            else:
                check= (language in celeb.translated) or (language == lang_default)
            if check:
                result['celebrity'][lang_title]= {
                    'name': '',
                    'name_aka': '',
                    'script': []
                    }
                result['celebrity'][lang_title]['user']= get_celebrity_lang_user(
                    celeb, language)
                for name_lang in celeb.name_lang:
                    if name_lang.lang == language:
                        result['celebrity'][lang_title].update({'name': name_lang.name,
                            'name_aka': name_lang.name_aka})
                        break
                total_dur= 0
                total_scenes= 0
                for scene in celeb.script:

                    # Fill general Scene data.
                    scene_dict= {'media_src': scene.media_src,
                        'media_copyright': scene.media_copyright,
                        'historical_date': scene.historical_date,
                        'historical_place': scene.historical_place
                        }
                    
                    try: # Getting the billboard
                        scene_dict.update({
                            'billboard': ''.join([prefix, request.get_host(),
                                '/api/billboard/', scene.billboard.pk])})
                    except:
                        scene_dict.update({'billboard': '<EMPTY>'})

                    try: # Getting the image
                        scene_dict.update({
                            'media_url': ''.join([prefix, request.get_host(),
                                scene.media_url])})
                    except:
                        scene_dict.update({'media_url': '<EMPTY>'})

                    # Fill language specific Scene data.
                    for scene_content in scene.scene_content:
                        if scene_content.lang != language:
                            continue
                        else:
                            total_scenes += 1
                            scene_dict.update({'text': scene_content.text,
                                'dur': scene_content.text_dur})
                            result['celebrity'][lang_title]['script'].append(scene_dict)
                            total_dur += int(scene_content.text_dur)
                            break
                result['celebrity'][lang_title].update({'total_dur': total_dur,
                    'total_scenes': total_scenes})
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
