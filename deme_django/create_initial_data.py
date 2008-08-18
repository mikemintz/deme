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

mike_person = Person(description="Mike Mintz", first_name="Mike", last_name="Mintz", email="mike@example.com")
mike_person.save_versioned(updater=admin)
mike_account = Account(description="Mike Mintz's Account", agent=mike_person)
mike_account.save_versioned(updater=admin)

todd_person = Person(description="Todd Davies", first_name="Todd", last_name="Davies", email="todd@example.com")
todd_person.save_versioned(updater=admin)
todd_account = Account(description="Todd Davies's Account", agent=todd_person)
todd_account.save_versioned(updater=admin)

reid_person = Person(description="Reid Chandler", first_name="Reid", last_name="Chandler", email="reid@example.com")
reid_person.save_versioned(updater=admin)
reid_account = Account(description="Reid Chandler's Account", agent=reid_person)
reid_account.save_versioned(updater=admin)

hello_page = DjangoTemplateDocument(description="Front Page", last_author=mike_person, body="""
{% extends layout %}
{% load resource_extras %}
{% block title %}Sample Home Page{% endblock %}
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned(updater=admin)
hello_url = CustomUrl(description="Hello Page Alias", parent_url=default_site, path="hello", viewer='dynamicpage', action='run', aliased_item=hello_page)
hello_url.save_versioned(updater=admin)

symsys_folio = Folio(description="Symsys Folio")
symsys_folio.save_versioned(updater=admin)
symsys_group = Group(description="Symsys Group", folio=symsys_folio)
symsys_group.save_versioned(updater=admin)
GroupMembership(item1=mike_person, item2=symsys_group).save_versioned(updater=admin)
GroupMembership(item1=todd_person, item2=symsys_group).save_versioned(updater=admin)
GroupMembership(item1=reid_person, item2=symsys_group).save_versioned(updater=admin)

role1 = Role(description="Role1")
role1.save_versioned(updater=admin)
RoleAbility(role=role1, ability="this", is_allowed=True).save_versioned(updater=admin)

role2 = Role(description="Role2")
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

AgentPermission(item1=mike_person, item2=mike_role1_item, role=role1).save_versioned(updater=admin)
AgentPermission(item1=mike_person, item2=mike_role2_item, role=role2).save_versioned(updater=admin)
GroupPermission(item1=symsys_group, item2=symsys_role1_item, role=role1).save_versioned(updater=admin)
GroupPermission(item1=symsys_group, item2=symsys_role2_item, role=role2).save_versioned(updater=admin)
AgentPermission(item1=None, item2=default_role1_item, role=role1).save_versioned(updater=admin)
AgentPermission(item1=None, item2=default_role2_item, role=role2).save_versioned(updater=admin)

AgentPermission(item1=None, item2=None, role=role1).save_versioned(updater=admin) # everybody gets role1 w.r.t. whole site

itemset = ItemSet(description="Fun ItemSet")
itemset.save_versioned(updater=admin)
itemset_membership1 = ItemSetMembership(item1=symsys_group, item2=itemset)
itemset_membership1.save_versioned(updater=admin)
itemset_membership2 = ItemSetMembership(item1=mike_person, item2=itemset)
itemset_membership2.save_versioned(updater=admin)

