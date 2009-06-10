"""
This module defines wrapper functions around the permission framework.
"""

from cms.models import *
from django.db import models
from django.db.models import Q

###############################################################################
# Helper functions
###############################################################################

def all_possible_global_abilities():
    """Return a set of global abilities that are possible."""
    return set(x[0] for x in POSSIBLE_GLOBAL_ABILITIES)

def all_possible_item_abilities(item_type):
    """Return a set of item abilities that are possible for this item type."""
    if not issubclass(item_type, Item):
        raise Exception("You must call all_possible_item_abilities with a subclass of Item")
    result = set()
    result.update(item_type.introduced_abilities)
    if item_type != Item:
        for parent_item_type in item_type.__bases__:
            result.update(all_possible_item_abilities(parent_item_type))
    return result

def all_possible_item_and_global_abilities():
    """Return a set of item and global abilities that are possible."""
    return set(x[0] for x in POSSIBLE_ITEM_AND_GLOBAL_ABILITIES)

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
        self._global_ability_cache = {}  # agent_id --> set(abilities)
        self._item_ability_cache = {}    # (agent_id, item_id) --> set(abilities)
        self._ability_yes_cache = {}     # (agent_id, ability) --> set(item_ids)
        self._ability_no_cache = {}      # (agent_id, ability) --> set(item_ids)

    def agent_can_global(self, agent, ability):
        """
        Return True if agent has the global ability.
        """
        return ability in self.global_abilities(agent)

    def agent_can(self, agent, ability, item):
        """
        Return True if agent has the ability with respect to the item.
        
        If the `filter_items` method was called for the ability on a QuerySet
        containing the item, no database calls will be made.
        """
        if item.destroyed:
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
            abilities_yes, abilities_no = self.calculate_abilities(agent, None, None)
            self._global_ability_cache[agent.pk] = (abilities_yes, abilities_no)
        else:
            abilities_yes, abilities_no = result
        return abilities_yes

    def item_abilities(self, agent, item):
        """
        Return a set of abilities the agent has with respect to the item.
        """
        if item.destroyed:
            return set()
        result = self._item_ability_cache.get((agent.pk, item.pk))
        if result is None:
            item_type = item.actual_item_type()
            self.global_abilities(agent) # cache the global abilities
            global_abilities_yes, global_abilities_no = self._global_ability_cache[agent.pk]
            if 'do_anything' in global_abilities_yes:
                abilities_yes = all_possible_item_abilities(item_type)
                abilities_no = set()
            elif 'do_anything' in global_abilities_no:
                abilities_yes = set()
                abilities_no = all_possible_item_abilities(item_type)
            else:
                abilities_yes, abilities_no = self.calculate_abilities(agent, item, item_type)
            self._item_ability_cache[(agent.pk, item.pk)] = (abilities_yes, abilities_no)
        else:
            abilities_yes, abilities_no = result
        return abilities_yes

    def filter_items(self, agent, ability, queryset):
        """
        Returns a QuerySet that filters the given QuerySet, into only the items
        that the specified agent has the specified ability to do.
        
        Unlike filter_items_by_permission, this takes into account the fact that
        agents with the global ability "do_anything" virtually have all item
        abilities.
        
        Also, update the cache to learn which items in the queryset the agent
        has the ability for. This makes it possible to call `agent_can` with
        the same agent and ability for all of the items in the queryset,
        without having to do a new database query each time.
        """
        item_type = queryset.model
        self.global_abilities(agent) # cache the global abilities
        global_abilities_yes, global_abilities_no = self._global_ability_cache[agent.pk]
        if ability not in all_possible_item_abilities(item_type):
            raise Exception("Item type %s does not support ability %s" % (item_type.__name__, ability))
        if 'do_anything' in global_abilities_yes:
            # Nothing to update, since no more database calls need to be made
            return queryset.filter(destroyed=False)
        elif 'do_anything' in global_abilities_no:
            # Nothing to update, since no more database calls need to be made
            return queryset.none()
        else:
            authorized_queryset = queryset.filter(self.filter_items_by_permission(agent, ability), destroyed=False)
            yes_ids = set(authorized_queryset.values_list('pk', flat=True))
            no_ids = set(queryset.values_list('pk', flat=True)) - yes_ids
            self._ability_yes_cache.setdefault((agent.pk, ability), set()).update(yes_ids)
            self._ability_no_cache.setdefault((agent.pk, ability), set()).update(no_ids)
            return authorized_queryset

    ###############################################################################
    # Methods to calculate ability sets
    ###############################################################################

    def calculate_abilities(self, agent, item, item_type):
        """
        Return a pair (yes_abilities, no_abilities) where yes_abilities is the set
        of item abilities that the agent is granted and no_abilities is a set of
        item abilities that the agent is denied. The two sets should be disjoint.
        
        If item is None, then we calculate the global abilities for the agent,
        in the same exact way (using only the *ToAllPermission classes).
        
        We calculate yes_abilities and no_abilities iteratively from the highest
        permission level down to the lowest permission level:
            1. OneToOnePermission
            2. OneToSomePermission
            3. OneToAllPermission
            4. SomeToOnePermission
            5. SomeToSomePermission
            6. SomeToAllPermission
            7. AllToOnePermission
            8. AllToSomePermission
            9. AllToAllPermission
        At each level, any permissions that were not granted or denied at a
        higher level are added to the abilities_yes or abilities_no set.
        """
        agent_collection_ids = RecursiveMembership.objects.filter(child=agent).values('parent_id').query
        if item is not None:
            item_collection_ids = RecursiveMembership.objects.filter(child=item, permission_enabled=True).values('parent_id').query

        permission_querysets = []
        for permission_class in [OneToOnePermission, OneToSomePermission, OneToAllPermission,
                                SomeToOnePermission, SomeToSomePermission, SomeToAllPermission,
                                AllToOnePermission, AllToSomePermission, AllToAllPermission]:
            filter = {}
            if hasattr(permission_class, 'source'):
                source_field = permission_class.source.field
                if source_field.rel.to == Agent:
                    filter['source'] = agent
                elif source_field.rel.to == Collection:
                    filter['source__in'] = agent_collection_ids
                else:
                    assert False
            if hasattr(permission_class, 'target'):
                if item is None:
                    continue
                target_field = permission_class.target.field
                if target_field.rel.to == Item:
                    filter['target'] = item
                elif target_field.rel.to == Collection:
                    filter['target__in'] = item_collection_ids
                else:
                    assert False
            permission_querysets.append(permission_class.objects.filter(**filter))

        if item is None:
            possible_abilities = all_possible_global_abilities()
        else:
            possible_abilities = all_possible_item_abilities(item_type)
        abilities_yes = set()
        abilities_no = set()
        # Iterate once for each level: agent, collection, everyone
        for permission_queryset in permission_querysets:
            # Populate cur_abilities_yes and cur_abilities_no with the specified
            # abilities at this level.
            cur_abilities_yes = set()
            cur_abilities_no = set()
            for ability, is_allowed in permission_queryset.values_list('ability', 'is_allowed'):
                if is_allowed:
                    cur_abilities_yes.add(ability)
                else:
                    cur_abilities_no.add(ability)
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
                if x not in abilities_yes and x not in abilities_no and x in possible_abilities:
                    abilities_yes.add(x)
            for x in cur_abilities_no:
                if x not in abilities_yes and x not in abilities_no and x in possible_abilities:
                    abilities_no.add(x)
            if abilities_yes | abilities_no == possible_abilities:
                break
        return (abilities_yes, abilities_no)

    ###############################################################################
    # Methods to calculate QuerySet filters
    ###############################################################################

    def filter_items_by_permission(self, agent, ability):
        """
        Return a Q object that can be used as a QuerySet filter, specifying only
        those items that the agent has the ability for.
        
        This does not take into account the fact that agents with the global
        ability "do_anything" virtually have all item abilities, but it does take
        into account the item ability "do_anything". This also takes into account
        default item type permissions.
        
        This can result in the database query becoming expensive.
        """
        agent_collection_ids = RecursiveMembership.objects.filter(child=agent).values('parent_id').query

        # yes_q_filters and no_q_filters have all Q filters in order of
        # permission level
        yes_q_filters = []
        no_q_filters = []
        for permission_class in [OneToOnePermission, OneToSomePermission, OneToAllPermission,
                                SomeToOnePermission, SomeToSomePermission, SomeToAllPermission,
                                AllToOnePermission, AllToSomePermission, AllToAllPermission]:
            for is_allowed in [True, False]:
                # Generate a Q object for this particular permission and is_allowed
                args = {}
                args['ability__in'] = [ability, 'do_anything']
                args['is_allowed'] = is_allowed
                if hasattr(permission_class, 'source'):
                    source_field = permission_class.source.field
                    if source_field.rel.to == Agent:
                        args['source'] = agent
                    elif source_field.rel.to == Collection:
                        args['source__in'] = agent_collection_ids
                    else:
                        assert False
                permission_queryset = permission_class.objects.filter(**args)
                if hasattr(permission_class, 'target'):
                    target_field = permission_class.target.field
                    if target_field.rel.to == Item:
                        q_filter = Q(pk__in=permission_queryset.values('target_id').query)
                    elif target_field.rel.to == Collection:
                        recursive_memberships = RecursiveMembership.objects.filter(parent__in=permission_queryset.values('target_id').query, permission_enabled=True)
                        q_filter = Q(pk__in=recursive_memberships.values('child_id').query)
                    else:
                        assert False
                else:
                    #TODO come up with a more elegant way to set q_filter, hopefully that doesn't involve doing separate queries
                    if permission_queryset:
                        q_filter = Q(pk__isnull=False)
                    else:
                        q_filter = Q(pk__isnull=True)
                if is_allowed:
                    yes_q_filters.append(q_filter)
                else:
                    no_q_filters.append(q_filter)

        # Combine all of the Q objects by the rules specified in
        # calculate_abilities

        # 9 disjuncts with 1-9 conjunct terms each: y1 | (~n1 & y2) | (~n1 & ~n2 & y3) | ...
        #result = yes_q_filters[0]
        #for i in xrange(1, len(yes_q_filters)):
        #    cur_filter = yes_q_filters[i]
        #    for j in xrange(0, i):
        #        cur_filter = cur_filter & ~no_q_filters[j]
        #    result = result | cur_filter

        # Nested conjuncts: y1 | (~n1 & (y2 | (~n2 & (y3 | ...
        result = yes_q_filters[-1]
        for i in xrange(len(yes_q_filters) - 2, -1, -1):
            result = yes_q_filters[i] | (~no_q_filters[i] & result)

        return result

