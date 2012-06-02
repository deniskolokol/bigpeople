from django.contrib.admin import site
from browser.models import Language, UserProfile, Billboard, Celebrity

site.register(Billboard)
site.register(UserProfile)
site.register(Language)
