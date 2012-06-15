from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('bigpeople.api.views',
    url(r'^$', 'get_description'),
    url(r'^celebrity/$', 'get_celebrity_list'),
    url(r'^celebrity/(?P<slug>[-\w]+)/$', 'get_celebrity_lang'),
    url(r'^celebrity/(?P<slug>[-\w]+)/(?P<lang>[a-z]+)/$', 'get_celebrity_lang_script'),

)
