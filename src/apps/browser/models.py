from django.db import models
from mongoengine import *

class Billboard(Document):
    """Slide templates in Foundry Nuke format
    """
    title= StringField(required=True, help_text="Script title")
    body= StringField(required=True, help_text="Script text")
    dur_in= FloatField(required=True, default=1.0,
		       help_text="Fade-in duration (sec)")
    dur_out= FloatField(required=True, default=1.0,
			help_text="Fade-out duration (sec)")
    sfx_in= FileField(help_text="Scene fade-in sound effect")
    sfx_out= FileField(help_text="Scene fade-out sound effect")
    sfx_loop= FileField(help_text="Scene background sound loop")
    # WARNING! the next fields can be deprecated!
    # sfx_in_url= URLField(help_text="URL to the scene fade-in sound effect")
    # sfx_out_url= URLField(help_text="URL to the scene fade-out sound effect")
    # sfx_loop_url= URLField(help_text="URL to the scene background sound loop")


class Role(Document):
    """Roles of users vs. apps
    """
    title= StringField(required=True, help_text="Role title")
    title_view= StringField(required=True,
			    help_text="Role title as shown on page by default")
    app_name= StringField(required=True, help_text="Application serving the role")
    lang_required= BooleanField(help_text="Language required")

    def __unicode__(self):
        return '%s (%s), app: %s' % (self.title, self.title_view, self.app_name)


class Language(Document):
    """Class for used languages.
    One program will always have at least two narrators
    of two different languages
    """
    title= StringField(required=True, help_text="Languge")

    def __unicode__(self):
        return self.title


class User(Document):
    """MongoEngine user.
    Depends on Roles, specifying a workspace,
    which is realized in corresponding Django app
    """
    name= StringField(required=True, help_text="Name, last name")
    login_name= StringField(required=True, help_text="Login name")
    login_password= StringField(required=True, help_text="Password")
    email= EmailField(help_text="E-mail")
    role= ReferenceField(Role, required=True, help_text="User role")

    def __unicode__(self):
	return '%s aka %s (%s)' % (self.name, self.login_name, self.role.title)


class TeamMember(EmbeddedDocument):
    """Class for team members working on a specific program
    """
    team_member= ReferenceField(User, required=True, help_text="Team member")
    lang= ReferenceField(Language, help_text="Language")

    def __unicode__(self):
	if self.lang:
	    return '%s: %s (%s)' % ( # language specified
		self.team_member.role.title, self.team_member.name,
		self.lang.title)
	else:
	    return '%s: %s' % ( # not depending on language
		self.team_member.role.title, self.team_member.name)

    def check_lang(self):
    	"""Language should be specified only in case a Role requires it
    	"""
	# WARNING! Re-write!
    	if self.team_member.role.lang_required:
    	    if not lang:
    		# raise Error?
    		pass
    	else:
    	    self.lang= None


class Celebrity(DynamicDocument):
    """Class for Celebrities.
    All data classes should inherit from DynamicDocument.
    All data classes should have "_tags" and "_keywords"
    for tagging documents and full-text search
    """
    name= StringField(required=True, help_text="Celebrity full name")
    name_aka= StringField(help_text="Celebrity 'also known as'")
    ready_to_assemble= BooleanField(help_text="Ready to assemble")
    used= BooleanField(help_text="Already used") # read-only, auto-fill
    team= ListField(EmbeddedDocumentField(TeamMember), default=list,
		    help_text="Team")
    _tags= ListField(StringField(), default=list)
    _keywords= ListField(StringField(), default=list)

    def __unicode__(self):
        return self.name


class SceneText(EmbeddedDocument):
    """Class for a Text in a Scene in a specified Language
    """
    text= StringField(required=True, help_text="Text")
    subtitle= StringField(required=True, help_text="Subtitle")
    lang= ReferenceField(Language, required=True, help_text="Text language")
    dur= IntField(required=True, help_text="Text duration") # auto-generated

    def __unicode__(self):
        return 'Text in %s' % self.lang.title

    # WARNING! Isn't subtitle the same that text?
    # If not - is it required?


class SceneVoice(EmbeddedDocument):
    """Class for a Scene Voice file in a specified Language
    """
    voice= FileField(required=True, help_text="Voice content")
    lang= ReferenceField(Language, required=True, help_text="Text language")

    def __unicode__(self):
        return 'Text in %s' % self.lang.title

    # WARNING! Think of merging it with SceneVoice


class CelebrityScene(DynamicDocument):
    """Class for a single Scene on Celebrity
    """
    celebrity= ReferenceField(Celebrity, required=True, help_text="Celebrity")
    media_content= FileField(required=True,
	help_text="Scene content (image or video)")
    media_url= URLField(help_text="URL to the scene content") # can be removed
    media_src= URLField(help_text="Media source")
    media_copyright= StringField(help_text="Media (C)")
    text_content= ListField(EmbeddedDocumentField(SceneText),
	help_text="Scene text content")
    voice_content= ListField(EmbeddedDocumentField(SceneVoice),
	help_text="Scene voice content")
    historical_date= DateTimeField(help_text="Historical date")
    historical_place= StringField(help_text="Historical place")
    billboard= ReferenceField(Billboard, required=True, help_text="Billboard")
    comment= StringField(help_text="Comments")
    # Both taken from text_content plus StringFields
    _tags= ListField(StringField(), default=list)
    _keywords= ListField(StringField(), default=list)

    def __unicode__(self):
        return "Scene on %s" % self.celebrity.name

    # WARNING! No more than one lang in text_content and voice_content!
    # Keep text_content and voice_content lists' indexes according to each other

    # WARNING! At least one historical date and place should be specified!


class CelebrityScript(DynamicDocument):
    """Class for a Script (made of Scenes) on Celebrity
    """
    celebrity= ReferenceField(Celebrity, required=True, help_text="Celebrity")
    scene= ListField(ReferenceField(CelebrityScene), required=True,
		     help_text="Scenes")

    def __unicode__(self):
        return '%s (%s scenes)' % (self.celebrity.name, len(scene))


class Program(Document):
    """Class for assembled program
    """
    celebrity_script= ListField(ReferenceField(CelebrityScript), required=True,
		     help_text="Scripts")
    comment= StringField(help_text="Comments")
    _tags= ListField(StringField(), default=list)
    _keywords= ListField(StringField(), default=list)

    def __unicode__(self):
	result= []
	for script in self.celebrity_script:
	    result.append(script.celebrity.name)
        return ', '.join(result)
