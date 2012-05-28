from django.contrib.admin import site
from browser.models import Billboard, Role, Language, Celebrity

site.register(Billboard)
site.register(Role)
site.register(Language)
site.register(Celebrity)
