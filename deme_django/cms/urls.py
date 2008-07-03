from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'deme_django.cms.views.index'),
    (r'^resource/(?P<item_type>[a-z]+)(?:(?:/(?P<collection_action>[a-z]+))|(?:/(?P<noun>[0-9]+)(?:/(?P<entry_action>[a-z]+))?))?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.views.resource'),
    (r'^resource($|/)', 'deme_django.cms.views.invalidresource'),
    (r'^meta/login($|/)', 'deme_django.cms.views.login'),
    (r'^meta/logout($|/)', 'deme_django.cms.views.logout'),
    (r'', 'deme_django.cms.views.alias'),
)

