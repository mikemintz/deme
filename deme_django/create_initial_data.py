#!/usr/bin/env python

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cms.models import *

# Necessary items

default_site = Site(description="Default Site", is_default_site=True, viewer='item', action='list', aliased_item=None, query_string='q=mike')
default_site.save_versioned()

anonymous_agent = Agent(description="Anonymous")
anonymous_agent.save_versioned()

anonymous_account = AnonymousAccount(description="Anonymous Account", agent=anonymous_agent)
anonymous_account.save_versioned()


# Just testing here:

mike_person = Person(description="Mike Mintz", first_name="Mike", last_name="Mintz", email="mike@example.com")
mike_person.save_versioned()
mike_account = Account(description="Mike Mintz's Account", agent=mike_person)
mike_account.save_versioned()

todd_person = Person(description="Todd Davies", first_name="Todd", last_name="Davies", email="todd@example.com")
todd_person.save_versioned()
todd_account = Account(description="Todd Davies's Account", agent=todd_person)
todd_account.save_versioned()

reid_person = Person(description="Reid Chandler", first_name="Reid", last_name="Chandler", email="reid@example.com")
reid_person.save_versioned()
reid_account = Account(description="Reid Chandler's Account", agent=reid_person)
reid_account.save_versioned()

hello_page = DynamicPage(description="Front Page", code="""
{% extends layout %}
{% load resource_extras %}
{% block title %}Sample Home Page{% endblock %}
{% block content %}
Hello World!
{% endblock content %}
""")
hello_page.save_versioned()
hello_url = AliasUrl(description="Hello Page Alias", parent_url=default_site, path="hello", viewer='dynamicpage', action='run', aliased_item=hello_page)
hello_url.save_versioned()

symsys_folio = Folio(description="Symsys Folio")
symsys_folio.save_versioned()
symsys_group = Group(description="Symsys Group", folio=symsys_folio)
symsys_group.save_versioned()
AgentToGroupRelationship(item1=mike_person, item2=symsys_group).save_versioned()
AgentToGroupRelationship(item1=todd_person, item2=symsys_group).save_versioned()
AgentToGroupRelationship(item1=reid_person, item2=symsys_group).save_versioned()

role1 = Role(description="Role1")
role1.save_versioned()
RolePermission(role=role1, ability="this", is_allowed=True).save_versioned()

role2 = Role(description="Role2")
role2.save_versioned()
RolePermission(role=role2, ability="this", is_allowed=False).save_versioned()
RolePermission(role=role2, ability="that", is_allowed=True).save_versioned()

mike_role1_item = Item(description="mike_role1_item")
mike_role1_item.save_versioned()
mike_role2_item = Item(description="mike_role2_item")
mike_role2_item.save_versioned()
symsys_role1_item = Item(description="symsys_role1_item")
symsys_role1_item.save_versioned()
symsys_role2_item = Item(description="symsys_role2_item")
symsys_role2_item.save_versioned()
default_role1_item = Item(description="default_role1_item")
default_role1_item.save_versioned()
default_role2_item = Item(description="default_role2_item")
default_role2_item.save_versioned()

AgentItemRoleRelationship(item1=mike_person, item2=mike_role1_item, role=role1).save_versioned()
AgentItemRoleRelationship(item1=mike_person, item2=mike_role2_item, role=role2).save_versioned()
GroupItemRoleRelationship(item1=symsys_group, item2=symsys_role1_item, role=role1).save_versioned()
GroupItemRoleRelationship(item1=symsys_group, item2=symsys_role2_item, role=role2).save_versioned()
AgentItemRoleRelationship(item1=None, item2=default_role1_item, role=role1).save_versioned()
AgentItemRoleRelationship(item1=None, item2=default_role2_item, role=role2).save_versioned()

AgentItemRoleRelationship(item1=None, item2=None, role=role1).save_versioned() # everybody gets role1 w.r.t. whole site

