from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',

    # The `item_type_url` URLs are restful URLs without nouns:
    #   - /<PREFIX>/<viewer>/<action>.<format>
    # The <PREFIX> component is defined as settings.VIEWER_URL_PREFIX
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    url(r'^%s(?P<viewer>[a-z]+)(?:/(?P<action>[a-z]+))?(?:\.(?P<format>[a-z]+))?/?$' % settings.VIEWER_URL_PREFIX, 'deme_django.cms.dispatcher.item_view', name='item_type_url'),

    # The `item_url` URLs are restful URLs with nouns:
    #   - /<PREFIX>/<viewer>/<noun>/<action>.<format>
    # The <PREFIX> component is defined as settings.VIEWER_URL_PREFIX
    # The <action> and <format> parameters are optional.
    # The <viewer>, <action>, and <format> parameters are all lowercase letters.
    # The <noun> parameter is a number.
    url(r'^%s(?P<viewer>[a-z]+)(?:/(?P<noun>[0-9]+)(?:/(?P<action>[a-z]+))?)?(?:\.(?P<format>[a-z]+))?/?$' % settings.VIEWER_URL_PREFIX, 'deme_django.cms.dispatcher.item_view', name='item_url'),

    # All other URLs are interpreted as alises using ViewerRequests
    url(r'', 'deme_django.cms.dispatcher.alias_view'),

)

