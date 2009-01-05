from django.conf.urls.defaults import *
from django.conf import settings
import os

urlpatterns = patterns('')

# Set up /static/modules/<module>/* to point to ./modules/<module>/static/*
# Set up /static/* to point to ./static/*
if settings.DJANGO_SERVES_STATIC_FILES:
    for module_name in settings.MODULE_NAMES:
        url = r'^static/modules/%s/(?P<path>.*)$' % module_name
        filesys_path = os.path.join(settings.MODULES_DIR, module_name, 'static')
        urlpatterns += patterns('', (url, 'django.views.static.serve', {'document_root': filesys_path}))
    url = r'^static/(?P<path>.*)$'
    filesys_path = os.path.join(os.path.dirname(__file__), 'static')
    urlpatterns += patterns('', (url, 'django.views.static.serve', {'document_root': filesys_path}))

# Let modules define special URLs before everything goes to cms/urls.py
for module_name in settings.MODULE_NAMES:
    urlpatterns += patterns('', (r'', include('deme_django.modules.%s.urls' % module_name)))

# Everything else goes to cms/urls.py, which includes a catch-all for aliases
urlpatterns += patterns('', (r'', include('deme_django.cms.urls')))

