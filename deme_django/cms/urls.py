from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^resource/(?P<viewer>[a-z]+)(?:/(?P<collection_action>[a-z]+))?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.resource', name='resource_collection'),
    url(r'^resource/(?P<viewer>[a-z]+)(?:/(?P<noun>[0-9]+)(?:/(?P<entry_action>[a-z]+))?)?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.resource', name='resource_entry'),
    url(r'^resource($|/)', 'deme_django.cms.dispatcher.invalidresource'),
    url(r'^meta/login($|/)', 'deme_django.cms.dispatcher.login'),
    url(r'^meta/logout($|/)', 'deme_django.cms.dispatcher.logout'),
    url(r'^meta/codegraph($|/)', 'deme_django.cms.dispatcher.codegraph'),
    url(r'', 'deme_django.cms.dispatcher.alias'),
)

