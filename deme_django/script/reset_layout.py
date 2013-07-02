#!/usr/bin/env python

from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

from cms.models import *

admin = Agent.objects.get(pk=1)
site = Site.objects.get(pk=DemeSetting.objects.get(name="cms.default_site").value)
site.default_layout = None
site.save_versioned(admin)
