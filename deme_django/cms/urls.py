from django.conf.urls.defaults import *

urlpatterns = patterns('',

    # The `resource_collection` URLs are restful URLs without nouns:
    #   - /resource/<viewer>/<action>.<format>
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    url(r'^resource/(?P<viewer>[a-z]+)(?:/(?P<action>[a-z]+))?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.resource', name='resource_collection'),

    # The `resource_entry` URLs are restful URLs with nouns:
    #   - /resource/<viewer>/<noun>/<action>.<format>
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    # The <noun> parameter is a number.
    url(r'^resource/(?P<viewer>[a-z]+)(?:/(?P<noun>[0-9]+)(?:/(?P<action>[a-z]+))?)?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.resource', name='resource_entry'),

    # Other URLs that begin with /resource are invalid.
    url(r'^resource($|/)', 'deme_django.cms.dispatcher.invalidurl'),

    # All other URLs are interpreted as alises using ViewerRequests
    url(r'', 'deme_django.cms.dispatcher.alias'),

)

