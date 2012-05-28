from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.contrib import admin
from browser.models import *

admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('bigpeople.screenwriter.views',
    url(r'^celebrity/$', 'celebrity_list', {'template': 'celeblist'}),
    url(r'^celebrity/add/$', 'celebrity_list', {'template': 'celeblist', 'form':True}),
    url(r'^celebrity/save/$', 'celebrity_save'),
    url(r'^celebrity/(?P<slug>[-\w]+)/delete/$', 'celebrity_delete'),
    url(r'^celebrity/(?P<slug>[-\w]+)/edit/$', 'celebrity_edit', {'template': 'celeblist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/save/$', 'celebrity_save'),
    url(r'^celebrity/(?P<slug>[-\w]+)/$', 'scene_list', {'template': 'scriptlist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/$', 'scene_list', {'template': 'scriptlist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/add/$', 'scene_list', {'template': 'scriptlist', 'form':True}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/$', 'scene_details'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/delete/$', 'scene_delete'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/edit/$', 'scene_edit', {'template': 'scriptlist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/save/$', 'scene_save'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/up/$', 'scene_move', {'template': 'scriptlist', 'dir':-1}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/down/$', 'scene_move', {'template': 'scriptlist', 'dir':1}),

    # Examples:
    # url(r'^$', 'bigpeople.views.home', name='home'),
    # url(r'^bigpeople/', include('bigpeople.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('', (
    r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT})
    )
