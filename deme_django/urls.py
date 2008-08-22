from django.conf.urls.defaults import *
from django.conf import settings
import os

urlpatterns = patterns('')

if settings.DJANGO_SERVES_STATIC_FILES:
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    for module_name in os.listdir(modules_dir):
        if module_name.startswith('.'):
            continue
        urlpatterns += patterns('',
            (r'^static/modules/%s/(?P<path>.*)$' % module_name, 'django.views.static.serve', {'document_root': os.path.join(modules_dir, module_name, 'static')}),
        )
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    )

urlpatterns += patterns('',
    # Uncomment this for admin:
    # (r'^admin/', include('django.contrib.admin.urls')),
    (r'', include('deme_django.cms.urls')),
)

