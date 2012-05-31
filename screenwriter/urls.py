from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('bigpeople.screenwriter.views',
    url(r'^$', 'celebrity_list', {'template': 'celeblist'}, name='celebrity_list'),
    url(r'^add/$', 'celebrity_list', {'template': 'celeblist', 'form':True}, name='celebrity_list_form'),
    url(r'^save/$', 'celebrity_save', name='celebrity_save'),
    url(r'^(?P<slug>[-\w]+)/$', 'scene_list', {'template': 'scriptlist'}, name='scene_list'),
    url(r'^(?P<slug>[-\w]+)/edit/$', 'celebrity_edit', {'template': 'celeblist'}, name='celebrity_edit'),
    url(r'^(?P<slug>[-\w]+)/save/$', 'celebrity_save', name='celebrity_save_new'),
    url(r'^(?P<slug>[-\w]+)/delete/$', 'celebrity_delete', name='celebrity_delete'),
    url(r'^(?P<slug>[-\w]+)/complete/$', 'celebrity_complete', name='celebrity_complete'),
    url(r'^(?P<slug>[-\w]+)/scene/$', 'scene_list', {'template': 'scriptlist'}),
    url(r'^(?P<slug>[-\w]+)/scene/add/$', 'scene_list', {'template': 'scriptlist', 'form':True}),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/up/$', 'scene_move', {'template': 'scriptlist', 'dir':-1}, name='scene_move_up'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/down/$', 'scene_move', {'template': 'scriptlist', 'dir':1}, name='scene_move_down'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/edit/$', 'scene_edit', {'template': 'scriptlist'}, name='scene_edit'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/save/$', 'scene_save', name='scene_save'),
    url(r'^(?P<slug>[-\w]+)/scene/(?P<scene_id>\d+)/delete/$', 'scene_delete', name='scene_delete'),
)
