from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('bigpeople.interpreter.views',
    url(r'^$', 'celebrity_translate', {'template': 'celeb_interpreter'}, name='celebrity_translate'),
    url(r'^(?P<slug>[-\w]+)/$', 'script_translate', {'template': 'script_interpreter'}, name='script_translate'),
    url(r'^(?P<slug>[-\w]+)/complete/$', 'script_complete_translation', {'template': 'script_interpreter'}, name='script_complete_translation'),
    url(r'^(?P<slug>[-\w]+)/revert/$', 'script_revert_translation', {'template': 'script_interpreter'}, name='script_revert_translation'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/translate/$', 'scene_translate', {'template': 'script_interpreter'}, name='scene_translate'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/save/$', 'save_translation', {'template': 'script_interpreter'}, name='save_translation'),
)
