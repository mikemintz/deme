from cms.models import *
from django.db import models
from django.db.models import Q
from itertools import chain

###############################################################################
# PermissionCache class
###############################################################################

class PermissionCache(object):
    """
    In-memory cache of global and item abilities.
    
    All methods are lazy, so if you ask about an ability, it will fetch it from
    the database only if it's not already cached.
    """

    def __init__(self):
        """
        Initialize an empty PermissionCache.
        """
        self._global_ability_cache = {} # agent_id --> set(abilities)
        self._item_ability_cache = {}   # (agent_id, item_id) --> set(abilities)
        self._ability_yes_cache = {}    # (agent_id, ability) --> set(item_ids)
        self._ability_no_cache = {}     # (agent_id, ability) --> set(item_ids)

    def agent_can_global(self, agent, ability):
        """
        Return True if agent has the global ability.
        """
        return ability in self.global_abilities(agent)

    def agent_can(self, agent, ability, item):
        """
        Return True if agent has the ability with respect to the item.
        
        If the `mass_learn` method was called for the ability on a QuerySet
        containing the item, no database calls will be made.
        """
        if item.pk in self._ability_yes_cache.get((agent.pk, ability), set()):
            return True
        if item.pk in self._ability_no_cache.get((agent.pk, ability), set()):
            return False
        return ability in self.item_abilities(agent, item)

    def global_abilities(self, agent):
        """
        Return a set of global abilities the agent has.
        """
        result = self._global_ability_cache.get(agent.pk)
        if result is None:
            result = calculate_global_abilities_for_agent(agent)
            possible_abilities = set(x[0] for x in POSSIBLE_GLOBAL_ABILITIES)
            if 'do_everything' in result:
                result = possible_abilities
            else:
                result &= possible_abilities
            self._global_ability_cache[agent.pk] = result
        return result

    def item_abilities(self, agent, item):
        """
        Return a set of abilities the agent has with respect to the item.
        """
        result = self._item_ability_cache.get((agent.pk, item.pk))
        if result is None:
            item_type = get_model_with_name(item.item_type)
            result = item_type.relevant_abilities
            if 'do_everything' not in self.global_abilities(agent):
                result &= calculate_abilities_for_agent_and_item(agent, item)
            self._item_ability_cache[(agent.pk, item.pk)] = result
        return result

    def mass_learn(self, agent, ability, queryset):
        """
        Update the cache to learn which items in the queryset the agent has the
        ability for.
        
        Use this method if you are planning on calling `agent_can` with the
        same agent and ability for all of the items in the queryset. This
        method uses filter_items_by_permission and only makes 2 database calls.
        """
        if self.agent_can_global(agent, 'do_everything'):
            pass # Nothing to update, since no more database calls need to be made
        else:
            authorized_queryset = queryset.filter(filter_items_by_permission(agent, ability))
            yes_ids = set(authorized_queryset.values_list('pk', flat=True))
            no_ids = set(queryset.values_list('pk', flat=True)) - yes_ids
            self._ability_yes_cache.setdefault((agent.pk, ability), set()).update(yes_ids)
            self._ability_no_cache.setdefault((agent.pk, ability), set()).update(no_ids)

    def filter_items(self, agent, ability):
        """
        Return a Q object that can be used as a QuerySet filter, specifying only
        those items that the agent has the ability for.
        
        Unlike filter_items_by_permission, this takes into account the fact that
        agents with the global ability "do_everything" virtually have all item
        abilities.
        """
        if self.agent_can_global(agent, 'do_everything'):
            return Q()
        else:
            return filter_items_by_permission(agent, ability)


###############################################################################
# Global permissions
###############################################################################

def calculate_global_roles_for_agent(agent):
    """
    Return tuple (agent_roles, collection_roles, default_roles).
    
    Each role list is a QuerySet for untrashed GlobalRoles. The agent_roles
    queryset contains roles that were assigned directly to agent, collection_roles
    contains roles that were assigned to Collections that agent is in (directly or
    indirectly), and default_roles contains all roles that were assigned to
    everyone by default.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query
    agent_role_permissions = AgentGlobalRolePermission.objects.filter(agent=agent)
    collection_role_permissions = CollectionGlobalRolePermission.objects.filter(collection__in=my_collection_ids)
    default_role_permissions = DefaultGlobalRolePermission.objects
    role_manager = GlobalRole.objects.filter(trashed=False)
    agent_roles = role_manager.filter(pk__in=agent_role_permissions.values('global_role_id').query)
    collection_roles = role_manager.filter(pk__in=collection_role_permissions.values('global_role_id').query)
    default_roles = role_manager.filter(pk__in=default_role_permissions.values('global_role_id').query)
    return (agent_roles, collection_roles, default_roles)


def calculate_global_permissions_for_agent(agent):
    """
    Return tuple (agent_permissions, collection_permissions, default_permissions).
    
    Each permission list is a QuerySet for untrashed GlobalPermissions. The
    agent_permissions queryset contains permissions that were assigned directly
    to agent, collection_permissions contains permissions that were assigned to
    Collections that agent is in (directly or indirectly), and default_permissions
    contains all permissions that were assigned to everyone by default.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query
    agent_perms = AgentGlobalPermission.objects.filter(agent=agent)
    collection_perms = CollectionGlobalPermission.objects.filter(collection__in=my_collection_ids)
    default_perms = DefaultGlobalPermission.objects.all()
    return (agent_perms, collection_perms, default_perms)


def calculate_global_abilities_for_agent(agent):
    """
    Return a set of global abilities the agent has.
    
    The agent has an ability if one of the following holds:
      1. The agent was directly assigned a role or permission that contains
         this ability with is_allowed=True.
      2. All of the following holds:
         a. An Collection that the agent is in (directly or indirectly) was
            assigned a role or permission that contains this ability with
            is_allowed=True.
         b. The agent was NOT directly assigned a role or permission that
            contains this ability with is_allowed=False.
      3. All of the following holds:
         a. There is a default role or permission that contains this ability
            with is_allowed=True.
         b. NO Collection that the agent is in (directly or indirectly) was
            assigned a role or permission that contains this ability with
            is_allowed=False.
         c. The agent was NOT directly assigned a role or permission that
            contains this ability with is_allowed=False.
    """
    roles_triple = calculate_global_roles_for_agent(agent)
    permissions_triple = calculate_global_permissions_for_agent(agent)
    abilities_yes = set()
    abilities_no = set()
    # Iterate once for each level: agent, collection, default
    for roles, permissions in zip(roles_triple, permissions_triple):
        # Populate cur_abilities_yes and cur_abilities_no with the specified
        # abilities at this level.
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = GlobalRoleAbility.objects.filter(trashed=False, global_role__in=roles.values('pk').query)
        role_ability_records = role_abilities.values('ability', 'is_allowed')
        permission_ability_records = permissions.values('ability', 'is_allowed')
        for ability_record in chain(role_ability_records, permission_ability_records):
            if ability_record['is_allowed']:
                cur_abilities_yes.add(ability_record['ability'])
            else:
                cur_abilities_no.add(ability_record['ability'])
        # For each ability specified at this level, add it to the all-level
        # ability sets if it's not already there. "Yes" takes precedence over
        # "no".
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    # All unspecified abilities are "no".
    return abilities_yes


###############################################################################
# Item permissions
###############################################################################

def calculate_roles_for_agent_and_item(agent, item):
    """
    Return tuple (agent_roles, collection_roles, default_roles).
    
    Each role list is a QuerySet for untrashed Roles. The agent_roles queryset
    contains roles that were assigned directly to agent/item, collection_roles
    contains roles that were assigned to Collections that agent is in (directly or
    indirectly), and default_roles contains all roles that were assigned to
    everyone by default.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query
    agent_role_permissions = AgentRolePermission.objects.filter(item=item, agent=agent)
    collection_role_permissions = CollectionRolePermission.objects.filter(item=item, collection__in=my_collection_ids)
    default_role_permissions = DefaultRolePermission.objects
    role_manager = Role.objects.filter(trashed=False)
    agent_roles = role_manager.filter(pk__in=agent_role_permissions.values('role_id').query)
    collection_roles = role_manager.filter(pk__in=collection_role_permissions.values('role_id').query)
    default_roles = role_manager.filter(pk__in=default_role_permissions.filter(item=item).values('role_id').query)
    return (agent_roles, collection_roles, default_roles)


def calculate_permissions_for_agent_and_item(agent, item):
    """
    Return tuple (agent_permissions, collection_permissions, default_permissions).
    
    Each permission list is a QuerySet for untrashed Permissions. The
    agent_permissions queryset contains permissions that were assigned directly
    to agent/item, collection_permissions contains permissions that were assigned
    to Collections that agent is in (directly or indirectly), and
    default_permissions contains all permissions that were assigned to everyone by
    default.
    """

    my_collection_ids = agent.ancestor_collections().values('pk').query
    agent_perms = AgentPermission.objects.filter(item=item, agent=agent)
    collection_perms = CollectionPermission.objects.filter(item=item, collection__in=my_collection_ids)
    default_perms = DefaultPermission.objects.filter(item=item)
    return (agent_perms, collection_perms, default_perms)


def calculate_abilities_for_agent_and_item(agent, item):
    """
    Return a set of abilities the agent has with respect to the item.
    
    The agent has an ability if one of the following holds:
      1. The agent was directly assigned a role or permission that contains
         this ability with is_allowed=True.
      2. All of the following holds:
         a. An Collection that the agent is in (directly or indirectly) was
            assigned a role or permission that contains this ability with
            is_allowed=True.
         b. The agent was NOT directly assigned a role or permission that
            contains this ability with is_allowed=False.
      3. All of the following holds:
         a. There is a default role or permission that contains this ability
            with is_allowed=True.
         b. NO Collection that the agent is in (directly or indirectly) was
            assigned a role or permission that contains this ability with
            is_allowed=False.
         c. The agent was NOT directly assigned a role or permission that
            contains this ability with is_allowed=False.
    """
    roles_triple = calculate_roles_for_agent_and_item(agent, item)
    permissions_triple = calculate_permissions_for_agent_and_item(agent, item)
    abilities_yes = set()
    abilities_no = set()
    # Iterate once for each level: agent, collection, default
    for roles, permissions in zip(roles_triple, permissions_triple):
        # Populate cur_abilities_yes and cur_abilities_no with the specified
        # abilities at this level.
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = RoleAbility.objects.filter(trashed=False, role__in=roles.values('pk').query)
        role_ability_records = role_abilities.values('ability', 'is_allowed')
        permission_ability_records = permissions.values('ability', 'is_allowed')
        for ability_record in chain(role_ability_records, permission_ability_records):
            if ability_record['is_allowed']:
                cur_abilities_yes.add(ability_record['ability'])
            else:
                cur_abilities_no.add(ability_record['ability'])
        # For each ability specified at this level, add it to the all-level
        # ability sets if it's not already there. "Yes" takes precedence over
        # "no".
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    # All unspecified abilities are "no".
    return abilities_yes


###############################################################################
# Permission QuerySet filters
###############################################################################

def filter_items_by_permission(agent, ability):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those items that the agent has the ability for.
    
    This does not take into account the fact that agents with the global
    ability "do_everything" virtually have all item abilities.
    
    This can result in the database query becoming expensive.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query
    yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=True).values('role_id').query
    no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=False).values('role_id').query

    # p contains all Q objects for all 12 combinations of level, role, is_allowed
    p = {}
    for permission_class in [AgentPermission, CollectionPermission, DefaultPermission,
                             AgentRolePermission, CollectionRolePermission, DefaultRolePermission]:
        for is_allowed in [True, False]:
            # Figure out what kind of permission this is
            is_role = 'role' in permission_class._meta.get_all_field_names()
            if 'agent' in permission_class._meta.get_all_field_names():
                level = 'agent'
            elif 'collection' in permission_class._meta.get_all_field_names():
                level = 'collection'
            else:
                level = 'default'
            # Generate a Q object for this particular permission and is_allowed
            args = {}
            if is_role:
                args['role__in'] = (yes_role_ids if is_allowed else no_role_ids)
            else:
                args['ability'] = ability
                args['is_allowed'] = is_allowed
            if level == 'agent':
                args['agent'] = agent
            elif level == 'collection':
                args['collection__in'] = my_collection_ids
            query = permission_class.objects.filter(**args).values('item_id').query
            q_name = "%s%s%s" % (level, 'role' if is_role else '', 'yes' if is_allowed else 'no')
            p[q_name] = Q(pk__in=query)

    # Combine all of the Q objects by the rules specified in
    # calculate_abilities_for_agent_and_item
    return p['agentyes'] |\
           p['agentroleyes'] |\
           (~p['agentno'] & ~p['agentroleno'] & p['collectionyes']) |\
           (~p['agentno'] & ~p['agentroleno'] & p['collectionroleyes']) |\
           (~p['agentno'] & ~p['collectionno'] & ~p['agentroleno'] & ~p['collectionroleno'] & p['defaultyes']) |\
           (~p['agentno'] & ~p['collectionno'] & ~p['agentroleno'] & ~p['collectionroleno'] & p['defaultroleyes'])

def filter_agents_by_permission(item, ability):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those agents that have the ability for the item.
    
    This does not take into account the fact that agents with the global
    ability "do_everything" virtually have all item abilities.
    
    This can result in the database query becoming expensive.
    """
    yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=True).values('role_id').query
    no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=False).values('role_id').query

    # p contains all Q objects for all 12 combinations of level, role, is_allowed
    p = {}
    for permission_class in [AgentPermission, CollectionPermission, DefaultPermission,
                             AgentRolePermission, CollectionRolePermission, DefaultRolePermission]:
        for is_allowed in [True, False]:
            # Figure out what kind of permission this is
            is_role = 'role' in permission_class._meta.get_all_field_names()
            if 'agent' in permission_class._meta.get_all_field_names():
                level = 'agent'
            elif 'collection' in permission_class._meta.get_all_field_names():
                level = 'collection'
            else:
                level = 'default'
            # Generate a Q object for this particular permission and is_allowed
            args = {'item': item}
            if is_role:
                args['role__in'] = (yes_role_ids if is_allowed else no_role_ids)
            else:
                args['ability'] = ability
                args['is_allowed'] = is_allowed
            if level == 'agent':
                query = permission_class.objects.filter(**args).values('agent_id').query
            elif level == 'collection':
                collection_query = permission_class.objects.filter(**args).values('collection_id').query
                query = RecursiveMembership.objects.filter(parent__in=collection_query).values('child_id').query
            else:
                default_perm_exists = (len(permission_class.objects.filter(**args)[:1]) > 0)
                query = (Agent.objects if default_perm_exists else Agent.objects.filter(pk__isnull=True)).values('pk').query
            q_name = "%s%s%s" % (level, 'role' if is_role else '', 'yes' if is_allowed else 'no')
            p[q_name] = Q(pk__in=query)

    # Combine all of the Q objects by the rules specified in
    # calculate_abilities_for_agent_and_item
    return p['agentyes'] |\
           p['agentroleyes'] |\
           (~p['agentno'] & ~p['agentroleno'] & p['collectionyes']) |\
           (~p['agentno'] & ~p['agentroleno'] & p['collectionroleyes']) |\
           (~p['agentno'] & ~p['collectionno'] & ~p['agentroleno'] & ~p['collectionroleno'] & p['defaultyes']) |\
           (~p['agentno'] & ~p['collectionno'] & ~p['agentroleno'] & ~p['collectionroleno'] & p['defaultroleyes'])

