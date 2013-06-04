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
from cms.permissions import all_possible_global_abilities
from modules.webauth.models import *
from modules.demeaccount.models import *
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
admin.save_versioned(action_agent=None, first_agent=True)

anonymous_agent = AnonymousAgent(name='Anonymous')
anonymous_agent.save_versioned(action_agent=admin)

default_site = Site(name="Default Site", viewer='item', action='list', aliased_item=None, query_string='', hostname="localhost")
default_site.save_versioned(action_agent=admin)
DemeSetting.set('cms.default_site', default_site.pk, admin)

print 'Creating defaults for the permission framework'
for item_type in all_item_types():
    for ability in item_type.introduced_abilities:
        if ability.endswith('_anything'):
            continue # We don't want any default permission here
        elif issubclass(item_type, (DemeSetting, AuthenticationMethod)):
            is_allowed = False
        elif ability.startswith('view '):
            is_allowed = True
        elif ability in ['comment_on', 'advanced_layout']:
            is_allowed = True
        else:
            is_allowed = False
        AllToAllPermission(ability=ability, is_allowed=is_allowed).save()

# Give everyone permission to create any item type, except DemeSetting, Site, and DjangoTemplateDocument
for item_type in all_item_types():
    if item_type in [DemeSetting, Site, DjangoTemplateDocument]:
        continue
    ability = 'create %s' % item_type.__name__
    if ability in all_possible_global_abilities():
        AllToAllPermission(ability=ability, is_allowed=True).save()

print 'Other stuff...'

OneToAllPermission(ability='do_anything', is_allowed=True, source=admin).save()

if len(sys.argv) < 2 or sys.argv[1] != 'test':
    sys.exit(0)

###############################################################################
# Just testing here:
###############################################################################

print 'Test stuff...'

DemeSetting.set("cms.default_create_item_types", "HtmlDocument,Project,AgreeDisagreePoll,Person,Group,DiscussionBoard,ImageDocument,FileDocument", admin)
DemeSetting.set("cms.comment_max_nesting_level", "99999", admin)

# Set the default layout
default_layout_code = open(os.path.join(os.path.dirname(__file__), '..', 'cms', 'templates', 'default_layout.html')).read()
default_layout = DjangoTemplateDocument(override_default_layout=True, name='Deme Layout', body=default_layout_code)
default_layout.save_versioned(action_agent=admin)

# Set the sample layout
sample_layout_code = open(os.path.join(os.path.dirname(__file__), '..', 'cms', 'templates', 'sample_layout.html')).read()
sample_layout = DjangoTemplateDocument(override_default_layout=True, name='Sample Layout', body=sample_layout_code)
sample_layout.save_versioned(action_agent=admin)

# Set the forum sample layout
forum_sample_layout_code = open(os.path.join(os.path.dirname(__file__), '..', 'cms', 'templates', 'forum_layout.html')).read()
forum_sample_layout = DjangoTemplateDocument(override_default_layout=True, name='Sample Forum Layout', body=forum_sample_layout_code)
forum_sample_layout.save_versioned(action_agent=admin)

git_log = subprocess.Popen(["git", "log"], stdout=subprocess.PIPE).communicate()[0]
git_commit = re.search(r'commit (.+)\nAuthor:', git_log).group(1)
git_date = re.search(r'Date:\s*(.*) (-|\+)\d+', git_log).group(1)
formatted_git_date = time.strftime("%Y-%m-%d", time.strptime(git_date, "%a %b %d %H:%M:%S %Y"))
home_page = DjangoTemplateDocument(name='Deme Home Page', body="""
{%% block content %%}
Welcome to Deme!
<br /><br />
Visit our GitHub page for the latest source code: <a href="http://github.com/mikemintz/deme">http://github.com/mikemintz/deme</a>.
<br /><br />
This site is running a working copy of Deme <a href="http://github.com/mikemintz/deme/commit/%s">commit %s</a> from %s.
<br /><br />
View the slides from our presentation at Silicon Valley Code Camp 2008 at <a href="http://www.stanford.edu/~davies/tdavies-presentations.html">http://www.stanford.edu/~davies/tdavies-presentations.html</a> (scroll down).
<br /><br />
Read our paper on Deme's architecture for IWWOST 2009 at <a href="http://www.stanford.edu/~davies/IWWOST09-Davies-Mintz-websiteversion.pdf">http://www.stanford.edu/~davies/IWWOST09-Davies-Mintz-websiteversion.pdf</a>
{%% endblock content %%}
""" % (git_commit, git_commit, formatted_git_date) )
home_page.save_versioned(action_agent=admin)
default_site.viewer = 'djangotemplatedocument'
default_site.action = 'render'
default_site.aliased_item = home_page
default_site.query_string = ''
#default_site.default_layout = default_layout #TODO uncomment this line
default_site.save_versioned(action_agent=admin)

mike = Person(first_name="Mike", last_name="Mintz", name="Mike Mintz")
mike.save_versioned(action_agent=admin)
OneToOnePermission(source=mike, target=mike, ability='do_anything', is_allowed=True).save()
mike_authentication_method = DemeAccount(username="mike", agent=mike)
mike_authentication_method.set_password('')
mike_authentication_method.save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])
WebauthAccount(username="mintz", agent=mike).save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])
mike_email_contact_method = EmailContactMethod(name="Mike's Email Contact Method", email="mintz@stanford.edu", agent=mike)
mike_email_contact_method.save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])

todd = Person(first_name="Todd", last_name="Davies", name="Todd Davies")
todd.save_versioned(action_agent=admin)
OneToOnePermission(source=todd, target=todd, ability='do_anything', is_allowed=True).save()
todd_authentication_method = DemeAccount(username="todd", agent=todd)
todd_authentication_method.set_password('')
todd_authentication_method.save_versioned(action_agent=todd, initial_permissions=[OneToOnePermission(source=todd, ability='do_anything', is_allowed=True)])
WebauthAccount(username="davies", agent=todd).save_versioned(action_agent=todd, initial_permissions=[OneToOnePermission(source=todd, ability='do_anything', is_allowed=True)])
todd_email_contact_method = EmailContactMethod(name="Todd's Email Contact Method", email="todd@example.com", agent=todd)
todd_email_contact_method.save_versioned(action_agent=todd, initial_permissions=[OneToOnePermission(source=todd, ability='do_anything', is_allowed=True)])

joe = Person(first_name="Joe", last_name="Marrama", name="Joe Marrama")
joe.save_versioned(action_agent=admin)
OneToOnePermission(source=joe, target=joe, ability='do_anything', is_allowed=True).save()
joe_authentication_method = DemeAccount(username="joe", agent=joe)
joe_authentication_method.set_password('')
joe_authentication_method.save_versioned(action_agent=joe, initial_permissions=[OneToOnePermission(source=joe, ability='do_anything', is_allowed=True)])
WebauthAccount(username="jmarrama", agent=joe).save_versioned(action_agent=joe, initial_permissions=[OneToOnePermission(source=joe, ability='do_anything', is_allowed=True)])
joe_email_contact_method = EmailContactMethod(name="Joe's Email Contact Method", email="joe@example.com", agent=joe)
joe_email_contact_method.save_versioned(action_agent=joe, initial_permissions=[OneToOnePermission(source=joe, ability='do_anything', is_allowed=True)])

github_agent = Agent(name="Github")
github_agent.save_versioned(action_agent=admin)
github_email_contact_method = EmailContactMethod(email="noreply@github.com", agent=github_agent)
github_email_contact_method.save_versioned(action_agent=admin)

hello_page = DjangoTemplateDocument(name="Hello Page", body="""
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned(action_agent=admin)
hello_url = CustomUrl(parent_url=default_site, path="hello", viewer='djangotemplatedocument', action='render', aliased_item=hello_page)
hello_url.save_versioned(action_agent=admin)

discuss_group = Group(name="Deme Dev Discussion")
discuss_group.save_versioned(action_agent=admin)
Membership(item=mike, collection=discuss_group).save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])
Membership(item=todd, collection=discuss_group).save_versioned(action_agent=todd, initial_permissions=[OneToOnePermission(source=todd, ability='do_anything', is_allowed=True)])
Membership(item=joe, collection=discuss_group).save_versioned(action_agent=joe, initial_permissions=[OneToOnePermission(source=joe, ability='do_anything', is_allowed=True)])
Subscription(contact_method=mike_email_contact_method, item=discuss_group.folios.get(), deep=True).save_versioned(action_agent=mike, initial_permissions=[OneToOnePermission(source=mike, ability='do_anything', is_allowed=True)])
Subscription(contact_method=todd_email_contact_method, item=discuss_group.folios.get(), deep=True).save_versioned(action_agent=todd, initial_permissions=[OneToOnePermission(source=todd, ability='do_anything', is_allowed=True)])
Subscription(contact_method=joe_email_contact_method, item=discuss_group.folios.get(), deep=True).save_versioned(action_agent=joe, initial_permissions=[OneToOnePermission(source=joe, ability='do_anything', is_allowed=True)])

#OneToAllPermission(source=anonymous_agent, ability='do_anything', is_allowed=False).save()

AllToOnePermission(target=admin, ability='login_as', is_allowed=True).save()

print 'Done'
