#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cms.models import *
from django import db
import subprocess
import re
import time
import sys

if Item.objects.count() != 0:
    raise AssertionError, 'You cannot run ./create_initial_data.py on a non-empty database'

################################################################################
# Necessary items
################################################################################

admin = Agent(name="Admin")
admin.save_versioned(first_agent=True, create_permissions=False)

role_abilities = []
for model in all_models():
    #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
    if issubclass(model, Permission):
        continue
    print 'Creating roles for %s' % model.__name__
    default_role = Role(name="%s Default" % model.__name__)
    creator_role = Role(name="%s Creator" % model.__name__)
    default_role.save_versioned(updater=admin, create_permissions=False)
    creator_role.save_versioned(updater=admin, create_permissions=False)
    for name in model._meta.get_all_field_names():
        field, defined_model, direct, m2m = model._meta.get_field_by_name(name)
        if not direct:
            continue
        if isinstance(field, db.models.fields.related.OneToOneField):
            continue
        if isinstance(field, db.models.fields.AutoField):
            continue
        if name in ['item_type', 'trashed']:
            continue
        role_abilities.append(RoleAbility(name="Default ability to view %s.%s" % (model.__name__, name), role=default_role, ability="view", ability_parameter=name, is_allowed=True))
        role_abilities.append(RoleAbility(name="Creator ability to view %s.%s" % (model.__name__, name), role=creator_role, ability="view", ability_parameter=name, is_allowed=True))
        if field.editable and name not in model.immutable_fields:
            role_abilities.append(RoleAbility(name="Creator ability to edit %s.%s" % (model.__name__, name), role=creator_role, ability="edit", ability_parameter=name, is_allowed=True))
    role_abilities.append(RoleAbility(name="Creator ability to modify permissions of %s" % (model.__name__,), role=creator_role, ability="modify_permissions", ability_parameter="id", is_allowed=True))
    role_abilities.append(RoleAbility(name="Creator ability to trash %s" % (model.__name__,), role=creator_role, ability="trash", ability_parameter="id", is_allowed=True))

print 'Saving roles...'
for item in role_abilities:
    item.save_versioned(updater=admin, create_permissions=False)

print 'Creating permissions for roles'
for model in all_models():
    #TODO don't create these permissions on other funny things like Relationships or SiteDomain or RoleAbility, etc.?
    if issubclass(model, Permission):
        continue
    default_role = Role.objects.get(name="%s Default" % model.__name__)
    creator_role = Role.objects.get(name="%s Creator" % model.__name__)
    for role in [default_role, creator_role]:
        DefaultRolePermission(name="Default permission for %s" % role.name, item=role, role=Role.objects.get(name="Role Default")).save_versioned(updater=admin)
        AgentRolePermission(name="Creator permission for %s" % role.name, agent=admin, item=role, role=Role.objects.get(name="Role Creator")).save_versioned(updater=admin)

print 'Creating permissions for admin'
DefaultRolePermission(name="Default permission for Admin", item=admin, role=Role.objects.get(name="Agent Default")).save_versioned(updater=admin)
AgentRolePermission(name="Creator permission for Admin", agent=admin, item=admin, role=Role.objects.get(name="Agent Creator")).save_versioned(updater=admin)

AgentGlobalPermission(name='Admin can do everything', ability='do_everything', ability_parameter="Item", is_allowed=True, agent=admin).save_versioned(updater=admin)

anonymous_agent = AnonymousAgent(name='Anonymous')
anonymous_agent.save_versioned(updater=admin)

default_site = Site(name="Default Site", is_default_site=True, viewer='item', action='list', aliased_item=None, query_string='')
default_site.save_versioned(updater=admin)

if len(sys.argv) < 2 or sys.argv[1] != 'test':
    sys.exit(0)

################################################################################
# Just testing here:
################################################################################

git_log = subprocess.Popen(["git", "log"], stdout=subprocess.PIPE).communicate()[0]
git_commit = re.search(r'commit (.+)', git_log).group(1)
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
default_site.save_versioned(updater=admin)

mike_person = Person(first_name="Mike", last_name="Mintz", name="Mike Mintz")
mike_person.save_versioned(updater=admin)
mike_authentication_method = PasswordAuthenticationMethod(name="Mike's Password Authentication Method", username="mike", agent=mike_person)
mike_authentication_method.set_password('')
mike_authentication_method.save_versioned(updater=admin)
mike_email_contact_method = EmailContactMethod(name="Mike's Email Contact Method", email="mike@example.com", agent=mike_person)
mike_email_contact_method.save_versioned(updater=admin)

todd_person = Person(first_name="Todd", last_name="Davies", name="Todd Davies")
todd_person.save_versioned(updater=admin)
todd_authentication_method = PasswordAuthenticationMethod(name="Todd's Password Authentication Method", username="todd", agent=todd_person)
todd_authentication_method.set_password('')
todd_authentication_method.save_versioned(updater=admin)
todd_email_contact_method = EmailContactMethod(name="Todd's Email Contact Method", email="todd@example.com", agent=todd_person)
todd_email_contact_method.save_versioned(updater=admin)

reid_person = Person(first_name="Reid", last_name="Chandler", name="Reid Chandler")
reid_person.save_versioned(updater=admin)
reid_authentication_method = PasswordAuthenticationMethod(name="Reid's Password Authentication Method", username="reid", agent=reid_person)
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
hello_url = CustomUrl(name="/hello URL", parent_url=default_site, path="hello", viewer='djangotemplatedocument', action='render', aliased_item=hello_page)
hello_url.save_versioned(updater=admin)

symsys_group = Group(name="Symsys Group")
symsys_group.save_versioned(updater=admin)
symsys_folio = Folio(name="Symsys Folio", group=symsys_group)
symsys_folio.save_versioned(updater=admin)
GroupMembership(name="Mike's membership in Symsys group", agent=mike_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(name="Todd's membership in Symsys group", agent=todd_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(name="Reid's membership in Symsys group", agent=reid_person, group=symsys_group).save_versioned(updater=admin)

discuss_group = Group(name="Deme Dev Discussion")
discuss_group.save_versioned(updater=admin)
discuss_folio = Folio(name="Deme Dev Discussion Folio", group=discuss_group)
discuss_folio.save_versioned(updater=admin)
GroupMembership(name="Mike's membership in discuss group", agent=mike_person, group=discuss_group).save_versioned(updater=admin)
GroupMembership(name="Todd's membership in discuss group", agent=todd_person, group=discuss_group).save_versioned(updater=admin)

DefaultGlobalPermission(name="Default permission to do_something", ability='do_something', ability_parameter='Item', is_allowed=True).save_versioned(updater=admin)
#AgentGlobalPermission(name="Permission for Anonymous not to do_something", agent=anonymous_agent, ability='do_something', ability_parameter='Item', is_allowed=False).save_versioned(updater=admin)
DefaultGlobalPermission(name="Default permission to create TextComments", ability='create', ability_parameter='TextComment', is_allowed=True).save_versioned(updater=admin)
DefaultGlobalPermission(name="Default permission to create HtmlDocuments", ability='create', ability_parameter='HtmlDocument', is_allowed=True).save_versioned(updater=admin)

DefaultPermission(name="Default permission to login_as Admin", item=admin, ability='login_as', ability_parameter="id", is_allowed=True).save_versioned(updater=admin)
