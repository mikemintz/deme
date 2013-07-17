#!/usr/bin/env python

from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

from cms.models import *
from modules.demeaccount.models import *
filename = sys.argv[1]
data = [x.strip().split(',') for x in open(filename)][1:]
admin = Agent.objects.get(pk=1)
for name, password, group_name in data:
    try:
        agent = Agent(name=name)
        agent.save_versioned(admin)
        deme_account = DemeAccount(username=name, agent=agent)
        deme_account.set_password(password)
        deme_account.save_versioned(admin)
        try:
            group = Group.objects.get(name=group_name)
            Membership(item=agent, collection=group).save_versioned(admin)
        except:
            print sys.exc_info()[0]
    except:
        print sys.exc_info()[0]