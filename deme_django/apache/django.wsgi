import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'deme_django.settings'

project_dir = os.path.dirname(os.path.dirname(__file__))
django_dir = os.path.join(os.path.dirname(project_dir), 'django_src')
sys.path.append(django_dir)
sys.path.append(project_dir)
sys.path.append(os.path.dirname(project_dir))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

