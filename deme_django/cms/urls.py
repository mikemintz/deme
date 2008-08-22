from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^resource/(?P<viewer>[a-z]+)(?:(?:/(?P<collection_action>[a-z]+))|(?:/(?P<noun>[0-9]+)(?:/(?P<entry_action>[a-z]+))?))?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.resource'),
    (r'^resource($|/)', 'deme_django.cms.dispatcher.invalidresource'),
    (r'^meta/login($|/)', 'deme_django.cms.dispatcher.login'),
    (r'^meta/logout($|/)', 'deme_django.cms.dispatcher.logout'),
    (r'^meta/codegraph($|/)', 'deme_django.cms.dispatcher.codegraph'),
    (r'', 'deme_django.cms.dispatcher.alias'),
)

