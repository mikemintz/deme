from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('')

if settings.DJANGO_SERVES_STATIC_FILES:
    import os.path
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    )

urlpatterns += patterns('',
    # Uncomment this for admin:
    # (r'^admin/', include('django.contrib.admin.urls')),
    (r'', include('deme_django.cms.urls')),
)

