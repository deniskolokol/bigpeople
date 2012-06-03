"""Utilities in broswer application.
"""

from models import Language, UserProfile, AppError, Celebrity
from django.contrib.auth.models import User
import settings

def get_error_descr(error, lang):
    """Get error description.
    From the AppError model.
    """
    lang= Language.objects.get(title=lang)
    error_lang= AppError.objects.get(code=error).lang
    error_descr= ''
    for app_error_lang in error_lang:
        if app_error_lang.lang == lang:
            error_descr= app_error_lang.descr
            break
    return error_descr


def get_default_language():
    """Return language as defined in settings
    """
    try:
        default_language= Language.objects.get(title=settings.DEFAULT_LANG)
    except:
        default_language= Language.objects.all()[0]
    return default_language


def get_user_lang(user, default_if_none=False):
    """Determine the current user's language.
    """
    try:
        user_profile= UserProfile.objects.get(user=user)
    except:
        user_profile= None
    lang= None
    if user_profile:
        lang= user_profile.lang
    if (lang is None) and default_if_none:
        lang= get_default_language()
    return lang


def get_session_languages(request, default_if_none=False):
    """Determine the user language.
    If default_if_none is True, return default language.
    Otherwise - all languages.
    """
    language= get_user_lang(request.user)
    if language:
        language= [language] # It should always be a list
    else:
        if default_if_none:
            language= [get_default_language()]
        else:
            language= Language.objects.all()        
    return language


def get_user_profile(user):
    if not isinstance(user, UserProfile):
        try:
            user= UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None
    return user


def get_user_celebrities(user):
    """List of Celebtities created/edited by a user
    """
    full= Celebrity.objects.defer('script','_tags','_keywords').order_by('name')
    user= get_user_profile(user)
    if not user: # Better to return everything than nothing
        return full
    else:
        out= []
        for celebrity in full:
            if user in celebrity.team:
                out.append(celebrity)
        return out
