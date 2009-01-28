from django.conf.urls.defaults import *

urlpatterns = patterns('',

    # The `item_type_url` URLs are restful URLs without nouns:
    #   - /item/<viewer>/<action>.<format>
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    url(r'^item/(?P<viewer>[a-z]+)(?:/(?P<action>[a-z]+))?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.item_view', name='item_type_url'),

    # The `item_url` URLs are restful URLs with nouns:
    #   - /item/<viewer>/<noun>/<action>.<format>
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    # The <noun> parameter is a number.
    url(r'^item/(?P<viewer>[a-z]+)(?:/(?P<noun>[0-9]+)(?:/(?P<action>[a-z]+))?)?(?:\.(?P<format>[a-z]+))?/?$', 'deme_django.cms.dispatcher.item_view', name='item_url'),

    # Other URLs that begin with /item are invalid.
    url(r'^item($|/)', 'deme_django.cms.dispatcher.invalid_url_view'),

    # All other URLs are interpreted as alises using ViewerRequests
    url(r'', 'deme_django.cms.dispatcher.alias_view'),

)

