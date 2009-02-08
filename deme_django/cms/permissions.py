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
        if item.blanked:
            return False
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
            abilities_yes, abilities_no = calculate_global_abilities_for_agent(agent)
            self._global_ability_cache[agent.pk] = (abilities_yes, abilities_no)
        else:
            abilities_yes, abilities_no = result
        return abilities_yes

    def item_abilities(self, agent, item):
        """
        Return a set of abilities the agent has with respect to the item.
        """
        if item.blanked:
            return set()
        result = self._item_ability_cache.get((agent.pk, item.pk))
        if result is None:
            item_type = get_item_type_with_name(item.item_type)
            self.global_abilities(agent) # cache the global abilities
            global_abilities_yes, global_abilities_no = self._global_ability_cache[agent.pk]
            if 'do_anything' in global_abilities_yes:
                abilities_yes = all_relevant_abilities(item_type)
                abilities_no = set()
            elif 'do_anything' in global_abilities_no:
                abilities_yes = set()
                abilities_no = all_relevant_abilities(item_type)
            else:
                abilities_yes, abilities_no = calculate_item_abilities_for_agent_and_item(agent, item, item_type)
            self._item_ability_cache[(agent.pk, item.pk)] = (abilities_yes, abilities_no)
        else:
            abilities_yes, abilities_no = result
        return abilities_yes

    def mass_learn(self, agent, ability, queryset):
        """
        Update the cache to learn which items in the queryset the agent has the
        ability for.
        
        Use this method if you are planning on calling `agent_can` with the
        same agent and ability for all of the items in the queryset. This
        method uses filter_items_by_permission and only makes 2 database calls.
        """
        self.global_abilities(agent) # cache the global abilities
        global_abilities_yes, global_abilities_no = self._global_ability_cache[agent.pk]
        if 'do_anything' in global_abilities_yes:
            pass # Nothing to update, since no more database calls need to be made
        elif 'do_anything' in global_abilities_no:
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
        agents with the global ability "do_anything" virtually have all item
        abilities.
        """
        self.global_abilities(agent) # cache the global abilities
        global_abilities_yes, global_abilities_no = self._global_ability_cache[agent.pk]
        if 'do_anything' in global_abilities_yes:
            return queryset.filter(blanked=False)
        elif 'do_anything' in global_abilities_no:
            return queryset.none()
        else:
            item_type = queryset.model
            return queryset.filter(filter_items_by_permission(agent, ability, item_type), blanked=False)


###############################################################################
# Global permissions
###############################################################################

def all_relevant_global_abilities():
    """Return a set of global abilities that are possible."""
    return set(x[0] for x in POSSIBLE_GLOBAL_ABILITIES)


def calculate_global_abilities_for_agent(agent):
    """
    Return a pair (yes_abilities, no_abilities) where yes_abilities is the set
    of global abilities that the agent is granted and no_abilities is a set of
    global abilities that the agent is denied. The two sets should be disjoint.
    
    We calculate yes_abilities and no_abilities iteratively from the highest
    permission level down to the lowest permission level (first we check
    AgentGlobalPermissions, then CollectionGlobalPermissions, and finally
    EveryoneGlobalPermissions). At each level, any permissions that were not
    granted or denied at a higher level are added to the abilities_yes or
    abilities_no set.
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
        # If "do_anything" is in the yes abilities at this level, grant all
        # other global abilities.
        if 'do_anything' in cur_abilities_yes:
            cur_abilities_yes = all_relevant_global_abilities()
        # If "do_anything" is in the no abilities at this level, deny all other
        # global abilities.
        if 'do_anything' in cur_abilities_no:
            cur_abilities_no = all_relevant_global_abilities()
        # For each ability specified at this level, add it to the all-level
        # ability sets if it's not already there. "Yes" takes precedence over
        # "no".
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    abilities_yes &= all_relevant_global_abilities()
    abilities_no &= all_relevant_global_abilities()
    return (abilities_yes, abilities_no)


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
        deme_setting_value = DemeSetting.get(deme_setting_key)
        if deme_setting_value == "true":
            return True
        if deme_setting_value == "false":
            return False
        return None
    if item_type != Item:
        for parent_item_type in item_type.__bases__:
            result = default_ability_is_allowed(ability, parent_item_type)
            if result is not None:
                return result
    return None


def calculate_item_abilities_for_agent_and_item(agent, item, item_type):
    """
    Return a pair (yes_abilities, no_abilities) where yes_abilities is the set
    of item abilities that the agent is granted and no_abilities is a set of
    item abilities that the agent is denied. The two sets should be disjoint.
    
    We calculate yes_abilities and no_abilities iteratively from the highest
    permission level down to the lowest permission level (first we check
    AgentItemPermissions, then CollectionItemPermissions, then 
    EveryoneItemPermissions, and finally default permissions defined in
    DemeSettings). At each level, any permissions that were not granted or
    denied at a higher level are added to the abilities_yes or
    abilities_no set.
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
        # If "do_anything" is in the yes abilities at this level, grant all
        # other item abilities.
        if 'do_anything' in cur_abilities_yes:
            cur_abilities_yes = possible_abilities
        # If "do_anything" is in the no abilities at this level, deny all other
        # item abilities.
        if 'do_anything' in cur_abilities_no:
            cur_abilities_no = possible_abilities
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
        if default_ability_is_allowed(ability, item_type) == True:
            abilities_yes.add(ability)
        elif default_ability_is_allowed(ability, item_type) == False:
            abilities_no.add(ability)
        else:
            pass # unspecified
    abilities_yes &= possible_abilities
    abilities_no &= possible_abilities
    return (abilities_yes, abilities_no)


###############################################################################
# Permission QuerySet filters
###############################################################################

def filter_items_by_permission(agent, ability, item_type):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those items that the agent has the ability for.
    
    This does not take into account the fact that agents with the global
    ability "do_anything" virtually have all item abilities, but it does take
    into account the item ability "do_anything". This also takes into account
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
            args['ability__in'] = [ability, 'do_anything']
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
    result = p['agentyes'] | (~p['agentno'] & p['collectionyes']) | (~p['agentno'] & ~p['collectionno'] & p['everyoneyes'])
    if default_is_allowed:
        result = result | (~p['agentno'] & ~p['collectionno'] & ~p['everyoneno'])
    return result


def filter_agents_by_permission(item, ability):
    """
    Return a Q object that can be used as a QuerySet filter, specifying only
    those agents that have the ability for the item.
    
    This does not take into account the fact that agents with the global
    ability "do_anything" virtually have all item abilities, but it does take
    into account the item ability "do_anything".
    
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
            args['ability__in'] = [ability, 'do_anything']
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
    result = p['agentyes'] | (~p['agentno'] & p['collectionyes']) | (~p['agentno'] & ~p['collectionno'] & p['everyoneyes'])
    if default_is_allowed:
        result = result | (~p['agentno'] & ~p['collectionno'] & ~p['everyoneno'])
    return result


