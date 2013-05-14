import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'deme_django.settings'

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
venv_lib_dir = os.path.join(project_dir, 'venv/lib')
for python_version_dir in os.listdir(venv_lib_dir):
    venv_site_package_dir = os.path.join(venv_lib_dir, python_version_dir, 'site-packages')
    sys.path.insert(0, venv_site_package_dir)
sys.path.insert(0, project_dir)
sys.path.insert(0, os.path.dirname(project_dir))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

