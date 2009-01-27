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
admin.save_versioned(updater=None, first_agent=True, create_permissions=False)

print 'Creating permissions for admin...'
AgentPermission(agent=admin, item=admin, ability='do_everything', is_allowed=True).save()

print 'Other stuff...'

AgentGlobalPermission(ability='do_everything', is_allowed=True, agent=admin).save()

anonymous_agent = AnonymousAgent(name='Anonymous')
anonymous_agent.save_versioned(updater=admin)

default_site = Site(name="Default Site", viewer='item', action='list', aliased_item=None, query_string='')
default_site.save_versioned(updater=admin)
DemeSetting.set('cms.default_site', default_site.pk, agent=admin)

if len(sys.argv) < 2 or sys.argv[1] != 'test':
    sys.exit(0)

###############################################################################
# Just testing here:
###############################################################################

# Set the default layout
default_layout_code = open(os.path.join(os.path.dirname(__file__), '..', 'cms', 'templates', 'default_layout.html')).read()
default_layout = DjangoTemplateDocument(override_default_layout=True, name='Deme Layout', body=default_layout_code)
default_layout.save_versioned(updater=admin)

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
home_page.save_versioned(updater=admin)
default_site.viewer = 'djangotemplatedocument'
default_site.action = 'render'
default_site.aliased_item = home_page
default_site.query_string = ''
default_site.default_layout = default_layout
default_site.save_versioned(updater=admin)

mike_person = Person(first_name="Mike", last_name="Mintz", name="Mike Mintz")
mike_person.save_versioned(updater=admin)
mike_authentication_method = PasswordAuthenticationMethod(username="mike", agent=mike_person)
mike_authentication_method.set_password('')
mike_authentication_method.save_versioned(updater=admin)
mike_email_contact_method = EmailContactMethod(name="Mike's Email Contact Method", email="mike@example.com", agent=mike_person)
mike_email_contact_method.save_versioned(updater=admin)

todd_person = Person(first_name="Todd", last_name="Davies", name="Todd Davies")
todd_person.save_versioned(updater=admin)
todd_authentication_method = PasswordAuthenticationMethod(username="todd", agent=todd_person)
todd_authentication_method.set_password('')
todd_authentication_method.save_versioned(updater=admin)
todd_email_contact_method = EmailContactMethod(name="Todd's Email Contact Method", email="todd@example.com", agent=todd_person)
todd_email_contact_method.save_versioned(updater=admin)

reid_person = Person(first_name="Reid", last_name="Chandler", name="Reid Chandler")
reid_person.save_versioned(updater=admin)
reid_authentication_method = PasswordAuthenticationMethod(username="reid", agent=reid_person)
reid_authentication_method.set_password('')
reid_authentication_method.save_versioned(updater=admin)
reid_email_contact_method = EmailContactMethod(name="Reid's Email Contact Method", email="reid@example.com", agent=reid_person)
reid_email_contact_method.save_versioned(updater=admin)

hello_page = DjangoTemplateDocument(name="Hello Page", body="""
{% block title %}Sample Home Page{% endblock %}
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned(updater=admin)
hello_url = CustomUrl(parent_url=default_site, path="hello", viewer='djangotemplatedocument', action='render', aliased_item=hello_page)
hello_url.save_versioned(updater=admin)

symsys_group = Group(name="Symsys Group")
symsys_group.save_versioned(updater=admin)
Membership(item=mike_person, collection=symsys_group).save_versioned(updater=admin)
Membership(item=todd_person, collection=symsys_group).save_versioned(updater=admin)
Membership(item=reid_person, collection=symsys_group).save_versioned(updater=admin)

discuss_group = Group(name="Deme Dev Discussion")
discuss_group.save_versioned(updater=admin)
Membership(item=mike_person, collection=discuss_group).save_versioned(updater=admin)
Membership(item=todd_person, collection=discuss_group).save_versioned(updater=admin)

DefaultGlobalPermission(ability='do_something', is_allowed=True).save()
#AgentGlobalPermission(agent=anonymous_agent, ability='do_something', is_allowed=False).save()
DefaultGlobalPermission(ability='create HtmlDocument', is_allowed=True).save()
DefaultGlobalPermission(ability='create TextDocumentExcerpt', is_allowed=True).save()
DefaultGlobalPermission(ability='create Collection', is_allowed=True).save()

DefaultPermission(item=admin, ability='login_as', is_allowed=True).save()
