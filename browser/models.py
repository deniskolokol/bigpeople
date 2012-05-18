from django.db.models import *
from django.contrib.auth.models import User
from djangotoolbox.fields import ListField, EmbeddedModelField
from django.template.defaultfilters import slugify
from gridfsuploads import gridfs_storage


class Billboard(Model):
    """Slide templates in Foundry Nuke format
    """
    title= CharField(max_length=400, help_text="Script title")
    body= TextField(help_text="Script text")
    dur_in= PositiveIntegerField(default=1, help_text="Fade-in duration (s)")
    dur_out= PositiveIntegerField(default=1, help_text="Fade-out duration (s)")
    sfx_in= FileField(storage=gridfs_storage, upload_to='/',
		      help_text="Scene fade-in sound effect")
    sfx_out= FileField(storage=gridfs_storage, upload_to='/',
		       help_text="Scene fade-out sound effect")
    sfx_loop= FileField(storage=gridfs_storage, upload_to='/',
			help_text="Scene background sound loop")
    # WARNING! the following fields can be deprecated!
    sfx_in_url= URLField(help_text="URL to the scene fade-in sound effect")
    sfx_out_url= URLField(help_text="URL to the scene fade-out sound effect")
    sfx_loop_url= URLField(help_text="URL to the scene background sound loop")

    def __unicode__(self):
        return self.title


class Role(Model):
    """Roles of users vs. apps
    """
    title= CharField(max_length=400, help_text="Role title")
    title_view= CharField(max_length=400, help_text="Role title as shown on page by default")
    app_name= CharField(max_length=50, help_text="Application serving the role")
    lang_required= BooleanField(help_text="Language required")

    def __unicode__(self):
        return '%s (%s), app: %s' % (self.title, self.title_view, self.app_name)


class Language(Model):
    """Class for Languages.
    A program will always have at least two narrators
    of two different languages
    """
    title= CharField(max_length=400, help_text="Languge title")
    title_orig= CharField(max_length=400, help_text="Original language title")

    def __unicode__(self):
        return self.title


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


class Celebrity(Model):
    """Class for Celebrities.
    All data classes should have "_tags" and "_keywords"
    for tagging documents and full-text search
    """
    name= CharField(max_length=400, help_text="Celebrity full name")
    name_aka= CharField(max_length=400, blank=True, help_text="Celebrity 'also known as'")
    slug= SlugField(max_length=100, help_text="Celebrity slug")
    ready_to_assemble= BooleanField(help_text="Ready to assemble")
    used= BooleanField(help_text="Already used") # read-only, auto-fill
    team= ListField(ForeignKey(TeamMember), help_text="Team")
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
	"""Override save
	"""
        self.slug= slugify(self.name)
        super(Celebrity, self).save(*args, **kwargs)

    def get_scene(self, scene_no=None):
	"""Get selected scene (or all) from the CelebrityScript
	"""
	try:
	    scene= CelebrityScene.objects.filter(celebrity=self)
	except CelebrityScene.DoesNotExist:
	    scene= []
	if scene and scene_no:
	    try:
		scene= scene[scene_no]
	    except IndexError:
		pass # leave as is
	if not isinstance(scene, list):
	    scene= list(scene) # should be list even if one
	# # media_content should contain a file
 	# if scene:
	#     for sc in scene:
	# 	sc.media_content= gridfs_storage.open(basename(sc.media_content.file.name))
	return scene


class SceneText(Model):
    """Class for a Text in a Scene in a specified Language
    """
    text= TextField(help_text="Text")
    lang= ForeignKey(Language, help_text="Text language")
    dur= PositiveIntegerField(help_text="Text duration (s)") # calc automatically

    def __unicode__(self):
        return 'Text in %s' % self.lang.title


class SceneTitle(Model):
    """Class for a Title in a Scene in a specified Language
    """
    text= TextField(help_text="Scene title")
    lang= ForeignKey(Language, help_text="Title language")

    def __unicode__(self):
        return 'Title in %s' % self.lang.title


class SceneVoice(Model):
    """Class for a Scene Voice file in a specified Language
    """
    voice= FileField(storage=gridfs_storage,
		     upload_to='/', help_text="Voice content")
    lang= ForeignKey(Language, help_text="Text language")
    dur= PositiveIntegerField(help_text="Actual duration (s)") # calc automatically

    def __unicode__(self):
        return 'Speech in %s' % self.lang.title


class CelebrityScene(Model):
    """Class for a single Scene on Celebrity
    """
    celebrity= ForeignKey(Celebrity, help_text="Celebrity")
    media_content= FileField(storage=gridfs_storage, upload_to='/',
	help_text="Scene content (image or video)")
    media_content_created_on= DateTimeField(auto_now_add=True)
    media_url= URLField(blank=True, help_text="URL to the scene content") # can be removed
    media_src= URLField(blank=True, help_text="Media source")
    media_copyright= CharField(max_length=400, blank=True, help_text="Media (C)")
    text_content= ListField(EmbeddedModelField(SceneText),
	help_text="Scene text content")
    title_content= ListField(EmbeddedModelField(SceneTitle),
	help_text="Scene title content")
    voice_content= ListField(EmbeddedModelField(SceneVoice),
	help_text="Scene voice content")
    historical_date_input= DateField( # for input only
	help_text="Input historical date") # (can be used with calendar)
    date_bc= BooleanField(default=False, help_text="Before Christ")
    historical_date= CharField(max_length=50,  # formatted string (including BC)
	help_text="Historical date") # filled automatically
    historical_place= CharField(max_length=400, help_text="Historical place")
    billboard= ForeignKey(Billboard, null=True, help_text="Billboard")
    
    comment= TextField(help_text="Comments")
    # Both taken from text_content plus Char- & TextFields
    _tags= ListField(CharField(max_length=50))
    _keywords= ListField(CharField(max_length=50))

    def __unicode__(self):
        return "Scene on %s" % self.celebrity.name

    # WARNING! No more than one lang in text_content and voice_content!
    # Keep text_content and voice_content lists' indexes according to each other

    # WARNING! Create a rule:
    # either media_content or historical_date or historical_place
    # or title_content should be given for a record


class CelebrityScript(Model):
    """Class for a Script (made of Scenes) on Celebrity.
    Used for numbering scenes in a script.
    """
    celebrity= ForeignKey(Celebrity, help_text="Celebrity") # control field!
    scene= ListField(ForeignKey(CelebrityScene), help_text="Scenes")

    def __unicode__(self):
        return '%s (%s scenes)' % (self.celebrity.name, len(scene))


class Program(Model):
    """Class for assembled program
    """
    celebrity_script= ListField(ForeignKey(CelebrityScript), help_text="Script")
    comment= TextField(help_text="Comment")

    def __unicode__(self):
	result= []
	for script in self.celebrity_script:
	    result.append(script.celebrity.name)
        return ', '.join(result)
