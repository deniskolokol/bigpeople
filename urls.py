from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.contrib import admin
from browser.models import *

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'bigpeople.browser.views.usr_login', name='usr_login'),
    url(r'^logout/$', 'bigpeople.browser.views.usr_logout', name='usr_logout'),
    url(r'^accounts/profile/', 'bigpeople.browser.views.usr_redirect', name='usr_redirect'),
    url(r'^celebrity/', include('screenwriter.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT})
    )
