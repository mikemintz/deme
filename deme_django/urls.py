from django.conf.urls.defaults import *
import os.path

urlpatterns = patterns('',
    # Comment this out for production:
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    # Uncomment this for admin:
    # (r'^admin/', include('django.contrib.admin.urls')),
    (r'', include('deme_django.cms.urls')),
)
