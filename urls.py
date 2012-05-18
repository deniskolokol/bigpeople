from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.contrib import admin
from browser.models import *

admin.autodiscover()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^role/$', list_detail.object_list, {'queryset': Role.objects.all(),
					      'template_name': 'ref_list.html'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/$', 'bigpeople.screenwriter.views.view_scenes', {'template': 'scriptlist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/$', 'bigpeople.screenwriter.views.view_scenes', {'template': 'scriptlist'}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/add/$', 'bigpeople.screenwriter.views.view_scenes', {'template': 'scriptlist', 'form':True}),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/$', 'bigpeople.screenwriter.views.scene_details'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/save/$', 'bigpeople.screenwriter.views.save_scene'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/remove/$', 'bigpeople.screenwriter.views.remove_scene'),
    url(r'^celebrity/(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/edit/$', 'bigpeople.screenwriter.views.edit_scene'),

    # Examples:
    # url(r'^$', 'bigpeople.views.home', name='home'),
    # url(r'^bigpeople/', include('bigpeople.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('', (
    r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}
))
