"""
This module defines wrapper functions around the permission framework.
"""

from cms.models import *
from django.db import models
from django.db.models import Q

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
            item_type = get_item_type_with_name(item.item_type)
            if 'do_everything' in self.global_abilities(agent):
                result = all_relevant_abilities(item_type)
            else:
                result = calculate_item_abilities_for_agent_and_item(agent, item, item_type)
                if 'do_everything' in result:
                    result = all_relevant_abilities(item_type)
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
            item_type = queryset.model
            authorized_queryset = queryset.filter(filter_items_by_permission(agent, ability, item_type))
            yes_ids = set(authorized_queryset.values_list('pk', flat=True))
            no_ids = set(queryset.values_list('pk', flat=True)) - yes_ids
            self._ability_yes_cache.setdefault((agent.pk, ability), set()).update(yes_ids)
            self._ability_no_cache.setdefault((agent.pk, ability), set()).update(no_ids)

    def filter_items(self, agent, ability, queryset):
        """
        Return a Q object that can be used as a QuerySet filter, specifying only
        those items that the agent has the ability for.
        
        Unlike filter_items_by_permission, this takes into account the fact that
        agents with the global ability "do_everything" virtually have all item
        abilities.
        """
        if self.agent_can_global(agent, 'do_everything'):
            return queryset
        else:
            item_type = queryset.model
            return queryset.filter(filter_items_by_permission(agent, ability, item_type))


###############################################################################
# Global permissions
###############################################################################

def calculate_global_abilities_for_agent(agent):
    """
    Return a set of global abilities the agent has.
    
    The agent has an ability if one of the following holds:
      1. The agent was directly assigned a permission that contains
         this ability with is_allowed=True.
      2. All of the following holds:
         a. A Collection that the agent is in (directly or indirectly) was
            assigned a permission that contains this ability with
            is_allowed=True.
         b. The agent was NOT directly assigned a permission that
            contains this ability with is_allowed=False.
      3. All of the following holds:
         a. There is an everyone permission that contains this ability
            with is_allowed=True.
         b. NO Collection that the agent is in (directly or indirectly) was
            assigned a permission that contains this ability with
            is_allowed=False.
         c. The agent was NOT directly assigned a permission that
            contains this ability with is_allowed=False.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query

    agent_perms = AgentGlobalPermission.objects.filter(agent=agent)
    collection_perms = CollectionGlobalPermission.objects.filter(collection__in=my_collection_ids)
    everyone_perms = EveryoneGlobalPermission.objects.all()

    abilities_yes = set()
    abilities_no = set()
    # Iterate once for each level: agent, collection, everyone
    for permissions in (agent_perms, collection_perms, everyone_perms):
        # Populate cur_abilities_yes and cur_abilities_no with the specified
        # abilities at this level.
        cur_abilities_yes = set()
        cur_abilities_no = set()
        permission_ability_records = permissions.values('ability', 'is_allowed')
        for ability_record in permission_ability_records:
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

def all_relevant_abilities(item_type):
    """Return a set of item abilities that are relevant to this item type."""
    if not issubclass(item_type, Item):
        raise Exception("You must call all_relevant_abilities with a subclass of Item")
    result = set()
    result.update(item_type.introduced_abilities)
    if item_type != Item:
        for parent_item_type in item_type.__bases__:
            result.update(all_relevant_abilities(parent_item_type))
    return result


def default_ability_is_allowed(ability, item_type):
    """
    Return true if this item type's ability is allowed by default (from
    DemeSettings).
    """
    if not issubclass(item_type, Item):
        raise Exception("You must call all_relevant_abilities with a subclass of Item")
    if ability in item_type.introduced_abilities:
        deme_setting_key = "cms.default_permission.%s.%s" % (item_type.__name__, ability)
        return (DemeSetting.get(deme_setting_key) == "true")
    if item_type != Item:
        for parent_item_type in item_type.__bases__:
            result = default_ability_is_allowed(ability, parent_item_type)
            if result is not None:
                return result
    return None


def calculate_item_abilities_for_agent_and_item(agent, item, item_type):
    """
    Return a set of abilities the agent has with respect to the item, using the
    item_type to determine relevant abilities and defaults.
    
    The agent has an ability if one of the following holds:
      1. The agent was directly assigned a permission that contains
         this ability with is_allowed=True.
      2. All of the following holds:
         a. A Collection that the agent is in (directly or indirectly) was
            assigned a permission that contains this ability with
            is_allowed=True.
         b. The agent was NOT directly assigned a permission that
            contains this ability with is_allowed=False.
      3. All of the following holds:
         a. There is an everyone permission that contains this ability
            with is_allowed=True.
         b. NO Collection that the agent is in (directly or indirectly) was
            assigned a permission that contains this ability with
            is_allowed=False.
         c. The agent was NOT directly assigned a permission that
            contains this ability with is_allowed=False.
      4. All of the following holds:
         a. There is a DemeSetting set to "true" with the key
            "cms.default_permission.<ITEM_TYPE_NAME>.<ABILITY>" (without angle
            brackets around the item type name and ability).
         b. There is NO everyone permission that contains this ability
            with is_allowed=False.
         c. NO Collection that the agent is in (directly or indirectly) was
            assigned a permission that contains this ability with
            is_allowed=False.
         d. The agent was NOT directly assigned a permission that
            contains this ability with is_allowed=False.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query

    agent_perms = AgentItemPermission.objects.filter(item=item, agent=agent)
    collection_perms = CollectionItemPermission.objects.filter(item=item, collection__in=my_collection_ids)
    everyone_perms = EveryoneItemPermission.objects.filter(item=item)

    possible_abilities = all_relevant_abilities(item_type)
    abilities_yes = set()
    abilities_no = set()
    # Iterate once for each level: agent, collection, everyone
    for permissions in (agent_perms, collection_perms, everyone_perms):
        # Populate cur_abilities_yes and cur_abilities_no with the specified
        # abilities at this level.
        cur_abilities_yes = set()
        cur_abilities_no = set()
        permission_ability_records = permissions.values('ability', 'is_allowed')
        for ability_record in permission_ability_records:
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
    unspecified_abilities = possible_abilities - abilities_yes - abilities_no
    for ability in unspecified_abilities:
        if default_ability_is_allowed(ability, item_type):
            abilities_yes.add(ability)
    return abilities_yes & possible_abilities


###############################################################################
# Permission QuerySet filters
###############################################################################

def filter_items_by_permission(agent, ability, item_type):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those items that the agent has the ability for.
    
    This does not take into account the fact that agents with the global
    ability "do_everything" virtually have all item abilities, but it does take
    into account the item ability "do_everything". This also takes into account
    default item type permissions.
    
    This can result in the database query becoming expensive.
    """
    my_collection_ids = agent.ancestor_collections().values('pk').query

    default_is_allowed = default_ability_is_allowed(ability, item_type)

    # p contains all Q objects for all 6 combinations of level, is_allowed
    p = {}
    for permission_class in [AgentItemPermission, CollectionItemPermission, EveryoneItemPermission]:
        for is_allowed in [True, False]:
            # Figure out what kind of permission this is
            if 'agent' in permission_class._meta.get_all_field_names():
                level = 'agent'
            elif 'collection' in permission_class._meta.get_all_field_names():
                level = 'collection'
            else:
                level = 'everyone'
            # Generate a Q object for this particular permission and is_allowed
            args = {}
            args['ability__in'] = [ability, 'do_everything']
            args['is_allowed'] = is_allowed
            if level == 'agent':
                args['agent'] = agent
            elif level == 'collection':
                args['collection__in'] = my_collection_ids
            query = permission_class.objects.filter(**args).values('item_id').query
            q_name = "%s%s" % (level, 'yes' if is_allowed else 'no')
            p[q_name] = Q(pk__in=query)

    # Combine all of the Q objects by the rules specified in
    # calculate_item_abilities_for_agent_and_item
    if default_is_allowed:
        return ~p['agentno'] & ~p['collectionno'] & ~p['everyoneno']
    else:
        return p['agentyes'] | (~p['agentno'] & p['collectionyes']) | (~p['agentno'] & ~p['collectionno'] & p['everyoneyes'])


def filter_agents_by_permission(item, ability):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those agents that have the ability for the item.
    
    This does not take into account the fact that agents with the global
    ability "do_everything" virtually have all item abilities, but it does take
    into account the item ability "do_everything".
    
    This can result in the database query becoming expensive.
    """

    default_is_allowed = default_ability_is_allowed(ability, type(item))

    # p contains all Q objects for all 6 combinations of level, is_allowed
    p = {}
    for permission_class in [AgentItemPermission, CollectionItemPermission, EveryoneItemPermission]:
        for is_allowed in [True, False]:
            # Figure out what kind of permission this is
            if 'agent' in permission_class._meta.get_all_field_names():
                level = 'agent'
            elif 'collection' in permission_class._meta.get_all_field_names():
                level = 'collection'
            else:
                level = 'everyone'
            # Generate a Q object for this particular permission and is_allowed
            args = {'item': item}
            args['ability__in'] = [ability, 'do_everything']
            args['is_allowed'] = is_allowed
            if level == 'agent':
                query = permission_class.objects.filter(**args).values('agent_id').query
            elif level == 'collection':
                collection_query = permission_class.objects.filter(**args).values('collection_id').query
                query = RecursiveMembership.objects.filter(parent__in=collection_query).values('child_id').query
            else:
                everyone_perm_exists = (len(permission_class.objects.filter(**args)[:1]) > 0)
                query = (Agent.objects if everyone_perm_exists else Agent.objects.filter(pk__isnull=True)).values('pk').query
            q_name = "%s%s" % (level, 'yes' if is_allowed else 'no')
            p[q_name] = Q(pk__in=query)

    # Combine all of the Q objects by the rules specified in
    # calculate_item_abilities_for_agent_and_item
    if default_is_allowed:
        return ~p['agentno'] & ~p['collectionno'] & ~p['everyoneno']
    else:
        return p['agentyes'] | (~p['agentno'] & p['collectionyes']) | (~p['agentno'] & ~p['collectionno'] & p['everyoneyes'])

