from cms.models import *
from django.db.models import Q
from itertools import chain


class PermissionCache(object):

    def __init__(self):
        self._global_ability_cache = {}
        self._item_ability_cache = {}
        self._ability_yes_cache = {}
        self._ability_no_cache = {}

    def agent_can_global(self, agent, ability):
        return ability in self.cached_global_abilities_for_agent(agent)

    def agent_can(self, agent, ability, item):
        if item.pk in self._ability_yes_cache.get((agent.pk, ability), set()):
            return True
        if item.pk in self._ability_no_cache.get((agent.pk, ability), set()):
            return False
        return ability in self.cached_abilities_for_agent_and_item(agent, item)

    def cached_global_abilities_for_agent(self, agent):
        result = self._global_ability_cache.get(agent.pk)
        if result is None:
            result = set(calculate_global_abilities_for_agent(agent))
            if 'do_everything' in result:
                result = set([x[0] for x in POSSIBLE_GLOBAL_ABILITIES])
            else:
                result = result & set([x[0] for x in POSSIBLE_GLOBAL_ABILITIES])
            self._global_ability_cache[agent.pk] = result
        return result

    def cached_abilities_for_agent_and_item(self, agent, item):
        result = self._item_ability_cache.get((agent.pk, item.pk))
        if result is None:
            result = type(item).relevant_abilities
            if 'do_everything' not in self.cached_global_abilities_for_agent(agent):
                result = result & set(calculate_abilities_for_agent_and_item(agent, item))
            self._item_ability_cache[(agent.pk, item.pk)] = result
        return result

    def learn_ability_for_queryset(self, agent, ability, queryset):
        yes_pks = set(queryset.filter(filter_for_agent_and_ability(agent, ability)).values_list('pk', flat=True))
        no_pks = set(queryset.values_list('pk', flat=True)) - yes_pks
        self._ability_yes_cache.setdefault((agent.pk, ability), set()).update(yes_pks)
        self._ability_no_cache.setdefault((agent.pk, ability), set()).update(no_pks)


################################################################################
# Global permissions
################################################################################


def get_global_roles_for_agent(agent):
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    role_manager = GlobalRole.objects.filter(trashed=False)
    agent_roles = role_manager.filter(pk__in=AgentGlobalRolePermission.objects.filter(agent=agent).values('global_role_id').query)
    itemset_roles = role_manager.filter(pk__in=ItemSetGlobalRolePermission.objects.filter(itemset__pk__in=my_itemset_ids).values('global_role_id').query)
    default_roles = role_manager.filter(pk__in=DefaultGlobalRolePermission.objects.values('global_role_id').query)
    return (agent_roles, itemset_roles, default_roles)


def get_global_permissions_for_agent(agent):
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    agent_perms = AgentGlobalPermission.objects.filter(agent=agent)
    itemset_perms = ItemSetGlobalPermission.objects.filter(itemset__pk__in=my_itemset_ids)
    default_perms = DefaultGlobalPermission.objects.all()
    return (agent_perms, itemset_perms, default_perms)


def calculate_global_abilities_for_agent(agent):
    roles_triple = get_global_roles_for_agent(agent)
    permissions_triple = get_global_permissions_for_agent(agent)
    abilities_yes = set()
    abilities_no = set()
    abilities_unset = set([x[0] for x in POSSIBLE_GLOBAL_ABILITIES])
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = GlobalRoleAbility.objects.filter(trashed=False, global_role__pk__in=role_list.values('pk').query)
        for role_ability_or_permission in chain(role_abilities.values('ability', 'is_allowed'), permission_list.values('ability', 'is_allowed')):
            ability = role_ability_or_permission['ability']
            is_allowed = role_ability_or_permission['is_allowed']
            if is_allowed:
                cur_abilities_yes.add(ability)
            else:
                cur_abilities_no.add(ability)
        # yes takes precedence over no
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no - cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    # anything left over is effectively "no"
    return abilities_yes


################################################################################
# Item permissions
################################################################################


def get_roles_for_agent_and_item(agent, item):
    """
    Return a triple (user_role_list, itemset_role_list, default_role_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    role_manager = Role.objects.filter(trashed=False)
    agent_roles = role_manager.filter(pk__in=AgentRolePermission.objects.filter(item=item, agent=agent).values('role_id').query)
    itemset_roles = role_manager.filter(pk__in=ItemSetRolePermission.objects.filter(item=item, itemset__pk__in=my_itemset_ids).values('role_id').query)
    default_roles = role_manager.filter(pk__in=DefaultRolePermission.objects.filter(item=item).values('role_id').query)
    return (agent_roles, itemset_roles, default_roles)


def get_permissions_for_agent_and_item(agent, item):
    """
    Return a triple (user_permission_list, itemset_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    agent_perms = AgentPermission.objects.filter(item=item, agent=agent)
    itemset_perms = ItemSetPermission.objects.filter(item=item, itemset__pk__in=my_itemset_ids)
    default_perms = DefaultPermission.objects.filter(item=item)
    return (agent_perms, itemset_perms, default_perms)


def calculate_abilities_for_agent_and_item(agent, item):
    """
    Return a set of ability strings
    """
    roles_triple = get_roles_for_agent_and_item(agent, item)
    permissions_triple = get_permissions_for_agent_and_item(agent, item)
    abilities_yes = set()
    abilities_no = set()
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = RoleAbility.objects.filter(trashed=False, role__pk__in=role_list.values('pk').query)
        for role_ability_or_permission in chain(role_abilities.values('ability', 'is_allowed'), permission_list.values('ability', 'is_allowed')):
            ability = role_ability_or_permission['ability']
            is_allowed = role_ability_or_permission['is_allowed']
            if is_allowed:
                cur_abilities_yes.add(ability)
            else:
                cur_abilities_no.add(ability)
        # yes takes precedence over no
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no - cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    # anything left over is effectively "no"
    return abilities_yes


def filter_for_agent_and_ability(agent, ability):
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=False).values('role_id').query

    perm_q = {}
    for agentitemsetdefault in ['agent', 'itemset', 'default']:
        for role in ['role', '']:
            for is_allowed in ['yes', 'no']:
                permission_class = eval("%s%sPermission" % ({'agent':'Agent','itemset':'ItemSet','default':'Default'}[agentitemsetdefault], role.capitalize()))
                args = {}
                if role == 'role':
                    args['role__pk__in'] = (relevant_yes_role_ids if is_allowed == 'yes' else relevant_no_role_ids)
                else:
                    args['ability'] = ability
                    args['is_allowed'] = (is_allowed == 'yes')
                if agentitemsetdefault == 'agent':
                    args['agent'] = agent
                elif agentitemsetdefault == 'itemset':
                    args['itemset__pk__in'] = my_itemset_ids
                query = permission_class.objects.filter(**args).values('item_id').query
                perm_q["%s%s%s" % (agentitemsetdefault, role, is_allowed)] = Q(pk__in=query)

    return perm_q['agentyes'] |\
           perm_q['agentroleyes'] |\
           (~perm_q['agentno'] & ~perm_q['agentroleno'] & perm_q['itemsetyes']) |\
           (~perm_q['agentno'] & ~perm_q['agentroleno'] & perm_q['itemsetroleyes']) |\
           (~perm_q['agentno'] & ~perm_q['itemsetno'] & ~perm_q['agentroleno'] & ~perm_q['itemsetroleno'] & perm_q['defaultyes']) |\
           (~perm_q['agentno'] & ~perm_q['itemsetno'] & ~perm_q['agentroleno'] & ~perm_q['itemsetroleno'] & perm_q['defaultroleyes'])

def filter_agents_for_item_and_ability(item, ability):
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, is_allowed=False).values('role_id').query

    perm_q = {}
    for agentitemsetdefault in ['agent', 'itemset', 'default']:
        for role in ['role', '']:
            for is_allowed in ['yes', 'no']:
                permission_class = eval("%s%sPermission" % ({'agent':'Agent','itemset':'ItemSet','default':'Default'}[agentitemsetdefault], role.capitalize()))
                args = {'item': item}
                if role == 'role':
                    args['role__pk__in'] = (relevant_yes_role_ids if is_allowed == 'yes' else relevant_no_role_ids)
                else:
                    args['ability'] = ability
                    args['is_allowed'] = (is_allowed == 'yes')
                if agentitemsetdefault == 'agent':
                    query = permission_class.objects.filter(**args).values('agent_id').query
                    perm_q["%s%s%s" % (agentitemsetdefault, role, is_allowed)] = Q(pk__in=query)
                elif agentitemsetdefault == 'itemset':
                    itemset_query = permission_class.objects.filter(**args).values('itemset_id').query
                    query = RecursiveMembership.objects.filter(parent__pk__in=itemset_query).values('child_id').query
                    perm_q["%s%s%s" % (agentitemsetdefault, role, is_allowed)] = Q(pk__in=query)
                else:
                    default_perm_exists = (len(permission_class.objects.filter(**args)[:1]) > 0)
                    perm_q["%s%s%s" % (agentitemsetdefault, role, is_allowed)] = Q(pk__isnull=not default_perm_exists)

    return perm_q['agentyes'] |\
           perm_q['agentroleyes'] |\
           (~perm_q['agentno'] & ~perm_q['agentroleno'] & perm_q['itemsetyes']) |\
           (~perm_q['agentno'] & ~perm_q['agentroleno'] & perm_q['itemsetroleyes']) |\
           (~perm_q['agentno'] & ~perm_q['itemsetno'] & ~perm_q['agentroleno'] & ~perm_q['itemsetroleno'] & perm_q['defaultyes']) |\
           (~perm_q['agentno'] & ~perm_q['itemsetno'] & ~perm_q['agentroleno'] & ~perm_q['itemsetroleno'] & perm_q['defaultroleyes'])

