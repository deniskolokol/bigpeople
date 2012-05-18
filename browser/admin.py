from django.contrib.admin import site
from browser.models import Role, Language, Celebrity, CelebrityScene, CelebrityScript

site.register(Role)
site.register(Language)
site.register(Celebrity)
site.register(CelebrityScene)
site.register(CelebrityScript)
