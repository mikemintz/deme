#!/usr/bin/env python

# Set up the Django Enviroment
from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from deme_django import settings
setup_environ(settings)

from cms.models import *
from django import db
import subprocess
import re
import time

if Item.objects.count() != 0:
    raise AssertionError, 'You cannot run ./create_initial_data.py on a non-empty database'

###############################################################################
# Necessary items
###############################################################################

admin = Agent(name="Admin")
admin.save_versioned(action_agent=None, first_agent=True, create_permissions=False)
AgentItemPermission(agent=admin, item=admin, ability='do_anything', is_allowed=True).save()

print 'Creating defaults for the permission framework'
for item_type in all_item_types():
    for ability in item_type.introduced_abilities:
        setting_name = 'cms.default_permission.%s.%s' % (item_type.__name__, ability)
        if issubclass(item_type, (DemeSetting, AuthenticationMethod)):
            is_allowed = False
        elif ability.startswith('view '):
            is_allowed = True
        elif ability in ['comment_on']:
            is_allowed = True
        else:
            is_allowed = False
        setting_value = 'true' if is_allowed else 'false'
        if ability == 'do_anything':
            setting_value = 'none'
        DemeSetting.set(setting_name, setting_value, admin)
        EveryoneItemPermission(item=DemeSetting.objects.get(key=setting_name), ability='view name', is_allowed=False).save()

print 'Other stuff...'

AgentGlobalPermission(ability='do_anything', is_allowed=True, agent=admin).save()

anonymous_agent = AnonymousAgent(name='Anonymous')
anonymous_agent.save_versioned(action_agent=admin)

default_site = Site(name="Default Site", viewer='item', action='list', aliased_item=None, query_string='', hostname="localhost")
default_site.save_versioned(action_agent=admin)
DemeSetting.set('cms.default_site', default_site.pk, admin)

if len(sys.argv) < 2 or sys.argv[1] != 'test':
    sys.exit(0)

###############################################################################
# Just testing here:
###############################################################################

print 'Test stuff...'

# Set the default layout
default_layout_code = open(os.path.join(os.path.dirname(__file__), '..', 'cms', 'templates', 'default_layout.html')).read()
default_layout = DjangoTemplateDocument(override_default_layout=True, name='Deme Layout', body=default_layout_code)
default_layout.save_versioned(action_agent=admin)

git_log = subprocess.Popen(["git", "log"], stdout=subprocess.PIPE).communicate()[0]
git_commit = re.search(r'commit (.+)\nAuthor:', git_log).group(1)
git_date = re.search(r'Date:\s*(.*) (-|\+)\d+', git_log).group(1)
formatted_git_date = time.strftime("%Y-%m-%d", time.strptime(git_date, "%a %b %d %H:%M:%S %Y"))
home_page = DjangoTemplateDocument(name='Deme Home Page', body="""
{%% block title %%}Welcome to Deme!{%% endblock %%}
{%% block content %%}
Welcome to Deme!
<br><br>
Visit our GitHub page for the latest source code: <a href="http://github.com/mikemintz/deme">http://github.com/mikemintz/deme</a>.
<br><br>

This site is running a working copy of Deme <a href="http://github.com/mikemintz/deme/commit/%s">commit %s</a> from %s.
<br><br>
View the slides from our presentation at Code Camp at <a href="http://www.stanford.edu/~davies/tdavies-presentations.html">http://www.stanford.edu/~davies/tdavies-presentations.html</a>.
{%% endblock content %%} 
""" % (git_commit, git_commit, formatted_git_date) )
home_page.save_versioned(action_agent=admin)
default_site.viewer = 'djangotemplatedocument'
default_site.action = 'render'
default_site.aliased_item = home_page
default_site.query_string = ''
default_site.default_layout = default_layout
default_site.save_versioned(action_agent=admin)

mike_person = Person(first_name="Mike", last_name="Mintz", name="Mike Mintz")
mike_person.save_versioned(action_agent=admin)
AgentItemPermission(agent=mike_person, item=mike_person, ability='do_anything', is_allowed=True).save()
mike_authentication_method = PasswordAuthenticationMethod(username="mike", agent=mike_person)
mike_authentication_method.set_password('')
mike_authentication_method.save_versioned(action_agent=mike_person)
WebauthAuthenticationMethod(username="mintz", agent=mike_person).save_versioned(action_agent=mike_person)
mike_email_contact_method = EmailContactMethod(name="Mike's Email Contact Method", email="mintz@stanford.edu", agent=mike_person)
mike_email_contact_method.save_versioned(action_agent=mike_person)

todd_person = Person(first_name="Todd", last_name="Davies", name="Todd Davies")
todd_person.save_versioned(action_agent=admin)
AgentItemPermission(agent=todd_person, item=todd_person, ability='do_anything', is_allowed=True).save()
todd_authentication_method = PasswordAuthenticationMethod(username="todd", agent=todd_person)
todd_authentication_method.set_password('')
todd_authentication_method.save_versioned(action_agent=todd_person)
todd_email_contact_method = EmailContactMethod(name="Todd's Email Contact Method", email="todd@example.com", agent=todd_person)
todd_email_contact_method.save_versioned(action_agent=todd_person)

reid_person = Person(first_name="Reid", last_name="Chandler", name="Reid Chandler")
reid_person.save_versioned(action_agent=admin)
AgentItemPermission(agent=reid_person, item=reid_person, ability='do_anything', is_allowed=True).save()
reid_authentication_method = PasswordAuthenticationMethod(username="reid", agent=reid_person)
reid_authentication_method.set_password('')
reid_authentication_method.save_versioned(action_agent=reid_person)
reid_email_contact_method = EmailContactMethod(name="Reid's Email Contact Method", email="reid@example.com", agent=reid_person)
reid_email_contact_method.save_versioned(action_agent=reid_person)

hello_page = DjangoTemplateDocument(name="Hello Page", body="""
{% block title %}Sample Home Page{% endblock %}
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned(action_agent=admin)
hello_url = CustomUrl(parent_url=default_site, path="hello", viewer='djangotemplatedocument', action='render', aliased_item=hello_page)
hello_url.save_versioned(action_agent=admin)

symsys_group = Group(name="Symsys Group")
symsys_group.save_versioned(action_agent=admin)
Membership(item=mike_person, collection=symsys_group).save_versioned(action_agent=admin)
Membership(item=todd_person, collection=symsys_group).save_versioned(action_agent=admin)
Membership(item=reid_person, collection=symsys_group).save_versioned(action_agent=admin)

discuss_group = Group(name="Deme Dev Discussion")
discuss_group.save_versioned(action_agent=admin)
Membership(item=mike_person, collection=discuss_group).save_versioned(action_agent=admin)
Membership(item=todd_person, collection=discuss_group).save_versioned(action_agent=admin)
Subscription(contact_method=mike_email_contact_method, item=discuss_group.folios.get(), deep=True).save_versioned(action_agent=mike_person)
#Subscription(contact_method=todd_email_contact_method, item=discuss_group.folios.get(), deep=True).save_versioned(action_agent=todd_person)

#AgentGlobalPermission(agent=anonymous_agent, ability='do_anything', is_allowed=False).save()
EveryoneGlobalPermission(ability='create HtmlDocument', is_allowed=True).save()
EveryoneGlobalPermission(ability='create TextDocumentExcerpt', is_allowed=True).save()
EveryoneGlobalPermission(ability='create Collection', is_allowed=True).save()

EveryoneItemPermission(item=admin, ability='login_as', is_allowed=True).save()
