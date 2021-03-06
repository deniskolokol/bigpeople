# -*- coding: utf-8 -*-

from django.db.models import *
from django.contrib.auth.models import User
from djangotoolbox.fields import ListField, EmbeddedModelField
from django.template.defaultfilters import slugify
from bigpeople.settings import MEDIA_URL
from bigpeople.browser.downcode import downcode

ALERT_TYPE= (
    ('block', 'block'),
    ('error', 'error'),
    ('success', 'success'),
    ('info', 'info')
    )

class Billboard(Model):
    """Slide templates in Foundry Nuke format
    """
    title= CharField(max_length=400, help_text="Script title")
    body= TextField(help_text="Script text")
    dur_in= PositiveIntegerField(default=1, help_text="Fade-in duration (s)")
    dur_out= PositiveIntegerField(default=1, help_text="Fade-out duration (s)")
    sfx_in= FileField(null=True, blank=True, upload_to=MEDIA_URL,
	help_text="Scene fade-in sound effect")
    sfx_out= FileField(null=True, blank=True, upload_to=MEDIA_URL,
	help_text="Scene fade-out sound effect")
    sfx_loop= FileField(null=True, blank=True, upload_to=MEDIA_URL,
	help_text="Scene background sound loop")
    # WARNING! the following fields can be deprecated!
    sfx_in_url= URLField(null=True, blank=True, max_length=400,
        help_text="URL to the scene fade-in sound effect")
    sfx_out_url= URLField(null=True, blank=True, max_length=400,
        help_text="URL to the scene fade-out sound effect")
    sfx_loop_url= URLField(null=True, blank=True, max_length=400,
        help_text="URL to the scene background sound loop")

    def __unicode__(self):
        return self.title


class Language(Model):
    """Class for Languages.
    A program will always have at least two narrators
    of two different languages
    """
    title= CharField(max_length=400, help_text="Languge title")
    title_orig= CharField(max_length=400, help_text="Original language title")

    def __unicode__(self):
        return self.title


class UserProfile(Model):
    """Custom user profile
    """
    user= ForeignKey(User, unique=True, help_text="User profile")
    lang= ForeignKey(Language, null=True, help_text="User language")
    
    def __unicode__(self):
        return '%s (%s)' % (self.user.username, self.lang.title)        
        

class TeamMember(Model):
    """Class for team members working on a specific program
    """
    usr= ForeignKey(User, help_text="Team member")
    lang= ForeignKey(Language, null=True, help_text="Language")

    def __unicode__(self):
        return '%s (%s)' % (self.usr.username, self.lang.title)


class CelebrityName(Model):
    """Celebrity name in different Languages
    """
    name= CharField(max_length=400, help_text="Celebrity full name")
    name_aka= CharField(max_length=400, blank=True,
        help_text="Celebrity 'also known as'")
    lang= ForeignKey(Language, help_text="Language")

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.lang.title_orig)


class SceneLang(Model):
    """Class for a Language-dependent Scene data
    """
    lang= ForeignKey(Language, help_text="Language")
    title= TextField(help_text="Scene title")
    text= TextField(help_text="Text")
    text_dur= PositiveIntegerField(
	help_text="Text duration (s), calculated based on the number of words in text")
    voice= FileField(null=True, blank=True, upload_to=MEDIA_URL,
        help_text="Voice content")
    voice_dur= PositiveIntegerField(
	help_text="Actual duration (s) after voice recording")

    def __unicode__(self):
        return 'Scene data in %s' % self.lang.title


class Scene(Model):
    """Class for a single Scene on Celebrity
    """
    media_content= FileField(null=True, blank=True, upload_to=MEDIA_URL,
	help_text="Scene content (image or video)")
    media_content_thumb= FileField(null=True, blank=True, upload_to=MEDIA_URL,
	help_text="Scene content thumbnail")
    media_content_created_on= DateTimeField(null=True, auto_now_add=True)
    media_url= URLField(max_length=400, blank=True,
        help_text="URL to the scene content")
    media_thumb_url= URLField(max_length=400, blank=True,
        help_text="URL to the scene thumbnail")
    media_src= URLField(max_length=400, blank=True, help_text="Media source")
    media_copyright= CharField(max_length=400, blank=True, help_text="Media (C)")
    scene_content= ListField(EmbeddedModelField(SceneLang),
	help_text="Scene text content")
    historical_date_input= DateField(null=True, blank=True, 
        help_text="Input historical date")
    historical_date= CharField(null=True, blank=True, max_length=50,
        help_text="Historical date")
    historical_date_bc= BooleanField(default=False, help_text="Date B.C.")
    historical_place= CharField(max_length=400, help_text="Historical place")
    billboard= ForeignKey(Billboard, null=True, help_text="Billboard")
    comment= TextField(help_text="Comments")
    # Both taken from text_content plus Char- & TextFields
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    def get_scene_content(self, lang):
        out= None
        for scene_cont in self.scene_content:
            if scene_cont.lang == lang:
                out= scene_cont
                break
        return out

    def set_lang_text(self, text, dur, lang):
        success= False
        scene_cont_index= 0
        for scene_cont in self.scene_content:
            if scene_cont.lang == lang:
                scene_cont.text= text
                scene_cont.text_dur= dur
                success= True
                break
            scene_cont_index += 1
        if not success: # No record in this lang yet.
            scene_content= SceneLang(lang=lang, text=text, text_dur=dur)
            if len(self.scene_content) == 0:
                self.scene_content= []
            self.scene_content.append(scene_content)
            scene_cont_index += 1
        return scene_cont_index


class Celebrity(Model):
    """Class for Celebrities.
    All data classes should have "_tags" and "_keywords"
    for tagging documents and full-text search
    NB: The indication if the Celebrity script was translated is via appending
        the specific Language to 'translated', not by a BooleanField
    """
    last_edited_on= DateTimeField(null=True, auto_now_add=True)
    name= CharField(max_length=400, unique=True, help_text="Celebrity base name")
    name_lang= ListField(EmbeddedModelField(CelebrityName),
	help_text="Language dependent Celebrity names")
    slug= SlugField(max_length=100, unique=True, help_text="Slug")
    # Flags
    completed= BooleanField(default=False, help_text="Script completed")
    declined= BooleanField(default=False,
        help_text="Script declined by main editor")
    confirmed= BooleanField(default=False,
        help_text="Script declined by main editor")
    translated= ListField(EmbeddedModelField(Language),
        help_text="Translated to the chosen language")
    ready_to_assemble= BooleanField(default=False, help_text="Ready to assemble")
    used= BooleanField(help_text="Already used") # read-only, auto-fill
    script= ListField(EmbeddedModelField(Scene), help_text="Scenes")
    team= ListField(EmbeddedModelField(UserProfile), help_text="Team")
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    def __unicode__(self):
        return self.name

    def _get_user_profile(self, user):
        """If there is a UserProfile, return it.
        Otherwise return False.
        """
        if not isinstance(user, UserProfile):
            try:
                user= UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return False # User cannot be part of the team without profile
        return user

    def is_team_member(self, user):
        """Check if the user is a team member.
        If User doesn't have a UserProfile, he/she can't be a part of a team.
        """
        if isinstance(user, User):
            if user.is_staff:
                return True # Staff members have full access to everything
        user= self._get_user_profile(user)
        if user:
            if user in self.team:
                return True
            else:
                return False
        else:
            return False

    def ensure_team_member(self, user):
        """Check if the User is in the team editing the Celebrity,
        and add him/her to the team if not
        """
        user= self._get_user_profile(user)
        if user:
            if not self.is_team_member(user):
                self.team.append(user)
            return True
        else:
            return False # Cannot add User without Profile

    def save(self, *args, **kwargs):
	"""Override save
	"""
        self.slug= slugify(downcode(self.name))
        super(Celebrity, self).save(*args, **kwargs)


class Program(Model):
    """Class for assembled program
    """
    celebrity= ListField(ForeignKey(Celebrity), help_text="Celebrities")
    comment= TextField(help_text="Comment")

    def __unicode__(self):
        return ', '.join(celebrity.name)


class AppErrorLang(Model):
    """Error codes in different languages
    """
    lang= ForeignKey(Language, help_text="Language")
    descr= CharField(max_length=400, help_text="Error description")
    
class AppError(Model):
    """Error codes in different languages
    """
    code= CharField(max_length=50, help_text="Error code")
    http_status_code= PositiveIntegerField(help_text="HTTP status code")
    lang= ListField(EmbeddedModelField(AppErrorLang), help_text="Error description")

    def __unicode__(self):
        lang_list= []
        for language in self.lang:
            lang_list.append(': '.join([language.lang.title, language.descr]))
        return '%s: %s' % (self.code, '; '.join(lang_list))

    
class AlertLang(Model):
    """Error codes in different languages
    """
    lang= ForeignKey(Language, help_text="Language")
    descr= CharField(max_length=400, help_text="Error description")
    alert= CharField(max_length=50, blank=True, help_text="Alert")
    
class Alert(Model):
    """Error codes in different languages
    """
    code= CharField(max_length=50, help_text="Error code")
    type= CharField(max_length=50, choices=ALERT_TYPE, help_text="Alert type")
    http_status_code= PositiveIntegerField(help_text="HTTP status code")
    lang= ListField(EmbeddedModelField(AlertLang), help_text="Error description")

    def __unicode__(self):
        lang_list= []
        for language in self.lang:
            lang_list.append(': '.join([language.lang.title, language.descr]))
        return '%s: %s' % (self.code, '; '.join(lang_list))

# Switch from AppError to Alert:
# for app_err in AppError.objects.all():
#     lang= []
#     for app_err_lang in app_err.lang:
#         lang.append(app_err_lang)
#     alert= Alert(type=ALERT_TYPE[1], code= app_err.code,
#         http_status_code= app_err.http_status_code,
#         lang=lang)
#     try:
#         alert.save()
#     except Exception as e:
#         print e

# plus:
# al= Alert(code="no_text_lang", type=ALERT_TYPE[0], http_status_code=200, lang=[AlertLang(lang=ru,descr=u"Cannot find text for given language")])

# fulfill lang alert (for russian only!)
# for alert in Alert.objects.all():
#     for lang in alert.lang:
#         if 'block' in alert.type:
#             lang.alert= u"Внимание!"
#         elif 'error' in alert.type:
#             lang.alert= u"Ошибка!"
#         elif 'info' in alert.type:
#             lang.alert= u"Информация!"
#         else:
#             lang.alert= u""
#     try:
#         alert.save()
#     except Exception as e:
#         print e
