from django.db.models import *
from django.contrib.auth.models import User
from djangotoolbox.fields import ListField, EmbeddedModelField
from django.template.defaultfilters import slugify
from gridfsuploads import gridfs_storage
from bigpeople.settings import MEDIA_URL
from bigpeople.browser.downcode import downcode

class Billboard(Model):
    """Slide templates in Foundry Nuke format
    """
    title= CharField(max_length=400, help_text="Script title")
    body= TextField(help_text="Script text")
    dur_in= PositiveIntegerField(default=1, help_text="Fade-in duration (s)")
    dur_out= PositiveIntegerField(default=1, help_text="Fade-out duration (s)")
    sfx_in= FileField(storage=gridfs_storage, upload_to=MEDIA_URL,
		      help_text="Scene fade-in sound effect")
    sfx_out= FileField(storage=gridfs_storage, upload_to=MEDIA_URL,
		       help_text="Scene fade-out sound effect")
    sfx_loop= FileField(storage=gridfs_storage, upload_to=MEDIA_URL,
			help_text="Scene background sound loop")
    # WARNING! the following fields can be deprecated!
    sfx_in_url= URLField(max_length=400,
        help_text="URL to the scene fade-in sound effect")
    sfx_out_url= URLField(max_length=400,
        help_text="URL to the scene fade-out sound effect")
    sfx_loop_url= URLField(max_length=400,
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


class Role(Model):
    """Roles of users vs. apps
    """
    title= CharField(max_length=400, help_text="Role title")
    title_view= CharField(max_length=400,
	help_text="Role title as shown on page by default")
    app_name= CharField(max_length=50, help_text="Application serving the role")
    lang= ForeignKey(Language, null=True, help_text="Operator language")
    lang_required= BooleanField(help_text="Language required")

    def __unicode__(self):
        return '%s (%s), app: %s' % (self.title, self.title_view, self.app_name)


class TeamMember(Model):
    """Class for team members working on a specific program
    """
    usr= ForeignKey(User, help_text="Team member")
    lang= ForeignKey(Language, null=True, help_text="Language")

    def __unicode__(self):
	if self.lang:
	    return '%s (%s)' % ( # language specified
	    	self.usr.username, self.lang.title)
	    # return '%s: %s (%s)' % ( # language specified
	    # 	self.usr.role.title, self.usr.name,
	    # 	self.lang.title)
	else:
	    return '%s' % ( # not depending on language
	    	self.usr.role.title, self.usr.username)
	    # return '%s: %s' % ( # not depending on language
	    # 	self.usr.role.title, self.usr.username)


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
    voice= FileField(storage=gridfs_storage,
	upload_to=MEDIA_URL, help_text="Voice content")
    voice_dur= PositiveIntegerField(
	help_text="Actual duration (s) after voice recording")

    def __unicode__(self):
        return 'Scene data in %s' % self.lang.title


class Scene(Model):
    """Class for a single Scene on Celebrity
    """
    media_content= FileField(storage=gridfs_storage, upload_to=MEDIA_URL,
	help_text="Scene content (image or video)")
    media_content_thumb= FileField(storage=gridfs_storage, upload_to=MEDIA_URL,
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
    historical_date_input= DateField(null=True,
        help_text="Input historical date")
    historical_date= CharField(null=True, max_length=50,
        help_text="Historical date")
    historical_date_bc= BooleanField(default=False, help_text="Date B.C.")
    historical_place= CharField(max_length=400, help_text="Historical place")
    billboard= ForeignKey(Billboard, null=True, help_text="Billboard")
    comment= TextField(help_text="Comments")
    # Both taken from text_content plus Char- & TextFields
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    # WARNING! No more than one lang in text_content and voice_content!
    # Keep text_content and voice_content lists' indexes according to each other

    # WARNING! Create a rule:
    # either media_content or historical_date or historical_place
    # or title_content should be given for a record


class Celebrity(Model):
    """Class for Celebrities.
    All data classes should have "_tags" and "_keywords"
    for tagging documents and full-text search
    """
    last_edited_on= DateTimeField(null=True, auto_now_add=True)
    name= CharField(max_length=400, unique=True, help_text="Celebrity base name")
    name_lang= ListField(EmbeddedModelField(CelebrityName),
	help_text="Language dependent Celebrity names")
    slug= SlugField(max_length=100, unique=True, help_text="Slug")
    ready_to_assemble= BooleanField(default=False, help_text="Ready to assemble")
    used= BooleanField(help_text="Already used") # read-only, auto-fill
    script= ListField(EmbeddedModelField(Scene), help_text="Scenes")
    # team= ListField(ForeignKey(TeamMember), help_text="Team") #  doesn't work this way!!!
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    def __unicode__(self):
        return self.name

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
