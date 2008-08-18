#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cms.models import *

# Necessary items

admin = Agent(description="Admin")
admin.save_versioned(first_agent=True)

anonymous_agent = Agent(description="Anonymous")
anonymous_agent.save_versioned(updater=admin)

anonymous_account = AnonymousAccount(description="Anonymous Account", agent=anonymous_agent)
anonymous_account.save_versioned(updater=admin)

home_page = DjangoTemplateDocument(body="""
{% extends 'base.html' %}
{% block title %}Welcome to Deme!{% endblock %}
{% block content %}
Welcome to Deme!
{% endblock content %}
""", last_author=admin)
home_page.save_versioned(updater=admin)

default_site = Site(name="Default Site", is_default_site=True, viewer='djangotemplatedocument', action='show', aliased_item=home_page, query_string='')
default_site.save_versioned(updater=admin)


# Just testing here:

mike_person = Person(first_name="Mike", last_name="Mintz", email="mike@example.com")
mike_person.save_versioned(updater=admin)
mike_account = Account(agent=mike_person)
mike_account.save_versioned(updater=admin)

todd_person = Person(first_name="Todd", last_name="Davies", email="todd@example.com")
todd_person.save_versioned(updater=admin)
todd_account = Account(agent=todd_person)
todd_account.save_versioned(updater=admin)

reid_person = Person(first_name="Reid", last_name="Chandler", email="reid@example.com")
reid_person.save_versioned(updater=admin)
reid_account = Account(agent=reid_person)
reid_account.save_versioned(updater=admin)

hello_page = DjangoTemplateDocument(name="Front Page", last_author=mike_person, body="""
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

symsys_folio = Folio(name="Symsys Folio")
symsys_folio.save_versioned(updater=admin)
symsys_group = Group(name="Symsys Group", folio=symsys_folio)
symsys_group.save_versioned(updater=admin)
GroupMembership(agent=mike_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(agent=todd_person, group=symsys_group).save_versioned(updater=admin)
GroupMembership(agent=reid_person, group=symsys_group).save_versioned(updater=admin)

role1 = Role(name="Role1")
role1.save_versioned(updater=admin)
RoleAbility(role=role1, ability="this", is_allowed=True).save_versioned(updater=admin)

role2 = Role(name="Role2")
role2.save_versioned(updater=admin)
RoleAbility(role=role2, ability="this", is_allowed=False).save_versioned(updater=admin)
RoleAbility(role=role2, ability="that", is_allowed=True).save_versioned(updater=admin)

mike_role1_item = Item(description="mike_role1_item")
mike_role1_item.save_versioned(updater=admin)
mike_role2_item = Item(description="mike_role2_item")
mike_role2_item.save_versioned(updater=admin)
symsys_role1_item = Item(description="symsys_role1_item")
symsys_role1_item.save_versioned(updater=admin)
symsys_role2_item = Item(description="symsys_role2_item")
symsys_role2_item.save_versioned(updater=admin)
default_role1_item = Item(description="default_role1_item")
default_role1_item.save_versioned(updater=admin)
default_role2_item = Item(description="default_role2_item")
default_role2_item.save_versioned(updater=admin)

AgentPermission(agent=mike_person, item=mike_role1_item, role=role1).save_versioned(updater=admin)
AgentPermission(agent=mike_person, item=mike_role2_item, role=role2).save_versioned(updater=admin)
GroupPermission(group=symsys_group, item=symsys_role1_item, role=role1).save_versioned(updater=admin)
GroupPermission(group=symsys_group, item=symsys_role2_item, role=role2).save_versioned(updater=admin)
AgentPermission(agent=None, item=default_role1_item, role=role1).save_versioned(updater=admin)
AgentPermission(agent=None, item=default_role2_item, role=role2).save_versioned(updater=admin)

AgentPermission(agent=None, item=None, role=role1).save_versioned(updater=admin) # everybody gets role1 w.r.t. whole site

itemset = ItemSet(name="Fun ItemSet")
itemset.save_versioned(updater=admin)
itemset_membership1 = ItemSetMembership(item=symsys_group, itemset=itemset)
itemset_membership1.save_versioned(updater=admin)
itemset_membership2 = ItemSetMembership(item=mike_person, itemset=itemset)
itemset_membership2.save_versioned(updater=admin)

