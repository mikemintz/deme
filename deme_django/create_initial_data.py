#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cms.models import *

if Item.objects.count() != 0:
    raise AssertionError, 'You cannot run ./create_initial_data.py on a non-empty database'

################################################################################
# Necessary items
################################################################################

admin = Agent(name="Admin")
admin.save_versioned(first_agent=True, create_permissions=False)

for model in all_models():
    #TODO don't create these permissions on other funny things like SiteDomain or RoleAbility, etc.?
    if issubclass(model, Relationship):
        continue
    print 'Creating roles for %s' % model.__name__
    default_role = Role(name="%s Default" % model.__name__)
    default_role.save_versioned(updater=admin, create_permissions=False)
    creator_role = Role(name="%s Creator" % model.__name__)
    creator_role.save_versioned(updater=admin, create_permissions=False)
    for name in model._meta.get_all_field_names():
        field, defined_model, direct, m2m = model._meta.get_field_by_name(name)
        if name in ['item_type', 'trashed']:
            continue
        if direct and type(field).__name__ != 'OneToOneField':
            RoleAbility(role=default_role, ability="view", ability_parameter=name, is_allowed=True).save_versioned(updater=admin, create_permissions=False)
            RoleAbility(role=creator_role, ability="view", ability_parameter=name, is_allowed=True).save_versioned(updater=admin, create_permissions=False)
            RoleAbility(role=creator_role, ability="edit", ability_parameter=name, is_allowed=True).save_versioned(updater=admin, create_permissions=False)
    RoleAbility(role=creator_role, ability="modify_permissions", ability_parameter="id", is_allowed=True).save_versioned(updater=admin, create_permissions=False)
    RoleAbility(role=creator_role, ability="trash", ability_parameter="id", is_allowed=True).save_versioned(updater=admin, create_permissions=False)

print 'Creating permissions for roles'
for model in all_models():
    #TODO don't create these permissions on other funny things like SiteDomain or RoleAbility, etc.?
    if issubclass(model, Relationship):
        continue
    default_role = Role.objects.get(name="%s Default" % model.__name__)
    creator_role = Role.objects.get(name="%s Creator" % model.__name__)
    for role in [default_role, creator_role]:
        DefaultRolePermission(item=role, role=Role.objects.get(name="Role Default")).save_versioned(updater=admin)
        AgentRolePermission(agent=admin, item=role, role=Role.objects.get(name="Role Creator")).save_versioned(updater=admin)

AgentGlobalPermission(ability='do_everything', ability_parameter="Item", is_allowed=True, agent=admin).save_versioned(updater=admin)

anonymous_agent = AnonymousAgent()
anonymous_agent.save_versioned(updater=admin)

default_site = Site(name="Default Site", is_default_site=True, viewer='item', action='list', aliased_item=None, query_string='')
default_site.save_versioned(updater=admin)

import sys; sys.exit(0)

################################################################################
# Just testing here:
################################################################################

home_page = DjangoTemplateDocument(body="""
{% extends layout %}
{% block title %}Welcome to Deme!{% endblock %}
{% block content %}
Welcome to Deme!
{% endblock content %}
""")
home_page.save_versioned(updater=admin)
default_site.viewer = 'djangotemplatedocument'
default_site.action = 'render'
default_site.aliased_item = home_page
default_site.query_string = ''
default_site.save_versioned(updater=admin)

mike_person = Person(first_name="Mike", last_name="Mintz", email="mike@example.com", name="Mike Mintz")
mike_person.save_versioned(updater=admin)
mike_account = PasswordAccount(agent=mike_person)
mike_account.set_password('')
mike_account.save_versioned(updater=admin)

todd_person = Person(first_name="Todd", last_name="Davies", email="todd@example.com", name="Todd Davies")
todd_person.save_versioned(updater=admin)
todd_account = PasswordAccount(agent=todd_person)
todd_account.set_password('')
todd_account.save_versioned(updater=admin)

reid_person = Person(first_name="Reid", last_name="Chandler", email="reid@example.com", name="Reid Chandler")
reid_person.save_versioned(updater=admin)
reid_account = PasswordAccount(agent=reid_person)
reid_account.set_password('')
reid_account.save_versioned(updater=admin)

hello_page = DjangoTemplateDocument(name="Front Page", body="""
{% extends layout %}
{% load resource_extras %}
{% block title %}Sample Home Page{% endblock %}
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned(updater=admin)
hello_url = CustomUrl(parent_url=default_site, path="hello", viewer='dynamicpage', action='run', aliased_item=hello_page)
hello_url.save_versioned(updater=admin)

symsys_group = Group(name="Symsys Group")
symsys_group.save_versioned(updater=admin)
symsys_folio = Folio(name="Symsys Folio", group=symsys_group)
symsys_folio.save_versioned(updater=admin)
GroupMembership(agent=mike_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(agent=todd_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(agent=reid_person, group=symsys_group).save_versioned(updater=admin)

discuss_group = Group(name="Deme Dev Discussion")
discuss_group.save_versioned(updater=admin)
discuss_folio = Folio(name="Deme Dev Discussion Folio", group=discuss_group)
discuss_folio.save_versioned(updater=admin)
GroupMembership(agent=mike_person, group=discuss_group).save_versioned(updater=admin)
GroupMembership(agent=todd_person, group=discuss_group).save_versioned(updater=admin)

role1 = Role(name="Role1")
role1.save_versioned(updater=admin)
RoleAbility(role=role1, ability="this", ability_parameter="id", is_allowed=True).save_versioned(updater=admin)

role2 = Role(name="Role2")
role2.save_versioned(updater=admin)
RoleAbility(role=role2, ability="this", ability_parameter="id", is_allowed=False).save_versioned(updater=admin)
RoleAbility(role=role2, ability="that", ability_parameter="id", is_allowed=True).save_versioned(updater=admin)

mike_role1_item = Item(name="mike_role1_item")
mike_role1_item.save_versioned(updater=admin)
mike_role2_item = Item(name="mike_role2_item")
mike_role2_item.save_versioned(updater=admin)
symsys_role1_item = Item(name="symsys_role1_item")
symsys_role1_item.save_versioned(updater=admin)
symsys_role2_item = Item(name="symsys_role2_item")
symsys_role2_item.save_versioned(updater=admin)
default_role1_item = Item(name="default_role1_item")
default_role1_item.save_versioned(updater=admin)
default_role2_item = Item(name="default_role2_item")
default_role2_item.save_versioned(updater=admin)

AgentRolePermission(agent=mike_person, item=mike_role1_item, role=role1).save_versioned(updater=admin)
AgentRolePermission(agent=mike_person, item=mike_role2_item, role=role2).save_versioned(updater=admin)
GroupRolePermission(group=symsys_group, item=symsys_role1_item, role=role1).save_versioned(updater=admin)
GroupRolePermission(group=symsys_group, item=symsys_role2_item, role=role2).save_versioned(updater=admin)
DefaultRolePermission(item=default_role1_item, role=role1).save_versioned(updater=admin)
DefaultRolePermission(item=default_role2_item, role=role2).save_versioned(updater=admin)

DefaultGlobalPermission(ability='do_something', ability_parameter='Item', is_allowed=True).save_versioned(updater=admin)
AgentGlobalPermission(agent=anonymous_agent, ability='do_something', ability_parameter='Item', is_allowed=False).save_versioned(updater=admin)

DefaultPermission(item=default_role1_item, ability='view', ability_parameter="id", is_allowed=True).save_versioned(updater=admin)
AgentPermission(item=mike_role1_item, ability='view', ability_parameter="id", is_allowed=True, agent=mike_person).save_versioned(updater=admin)

AgentPermission(item=symsys_group, ability='login_as', ability_parameter="id", is_allowed=True, agent=mike_person).save_versioned(updater=admin)
AgentPermission(item=admin, ability='login_as', ability_parameter="id", is_allowed=True, agent=mike_person).save_versioned(updater=admin)
AgentPermission(item=mike_person, ability='login_as', ability_parameter="id", is_allowed=True, agent=anonymous_agent).save_versioned(updater=admin)

itemset = ItemSet(name="Fun ItemSet")
itemset.save_versioned(updater=admin)
itemset_membership1 = ItemSetMembership(item=symsys_group, itemset=itemset)
itemset_membership1.save_versioned(updater=admin)
itemset_membership2 = ItemSetMembership(item=mike_person, itemset=itemset)
itemset_membership2.save_versioned(updater=admin)

