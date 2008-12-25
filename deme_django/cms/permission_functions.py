from cms.models import *
from django.db.models import Q


################################################################################
# Global permissions
################################################################################


def get_global_roles_for_agent(agent):
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    role_manager = GlobalRole.objects.filter(trashed=False)
    agent_roles = role_manager.filter(agent_global_role_permissions_as_global_role__agent=agent,
                                      agent_global_role_permissions_as_global_role__trashed=False)
    itemset_roles = role_manager.filter(itemset_global_role_permissions_as_global_role__pk__in=my_itemset_ids,
                                      itemset_global_role_permissions_as_global_role__trashed=False)
    default_roles = role_manager.filter(default_global_role_permissions_as_global_role__pk__isnull=False,
                                        default_global_role_permissions_as_global_role__trashed=False)
    return (agent_roles, itemset_roles, default_roles)


def get_global_permissions_for_agent(agent):
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    agent_perms = AgentGlobalPermission.objects.filter(trashed=False, agent=agent)
    itemset_perms = ItemSetGlobalPermission.objects.filter(trashed=False, itemset__pk__in=my_itemset_ids)
    default_perms = DefaultGlobalPermission.objects.filter(trashed=False)
    return (agent_perms, itemset_perms, default_perms)


def get_global_abilities_for_agent(agent):
    roles_triple = get_global_roles_for_agent(agent)
    permissions_triple = get_global_permissions_for_agent(agent)
    abilities_yes = set()
    abilities_no = set()
    abilities_unset = set([x[0] for x in POSSIBLE_GLOBAL_ABILITIES])
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = GlobalRoleAbility.objects.filter(trashed=False, global_role__in=role_list).all()
        import itertools
        for role_ability_or_permission in itertools.chain(role_abilities, permission_list):
            ability = role_ability_or_permission.ability
            ability_parameter = role_ability_or_permission.ability_parameter
            is_allowed = role_ability_or_permission.is_allowed
            if is_allowed:
                cur_abilities_yes.add((ability, ability_parameter))
            else:
                cur_abilities_no.add((ability, ability_parameter))
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
    agent_roles = role_manager.filter(agent_role_permissions_as_role__item=item,
                                      agent_role_permissions_as_role__agent=agent,
                                      agent_role_permissions_as_role__trashed=False)
    itemset_roles = role_manager.filter(itemset_role_permissions_as_role__item=item,
                                      itemset_role_permissions_as_role__itemset__pk__in=my_itemset_ids,
                                      itemset_role_permissions_as_role__trashed=False)
    default_roles = role_manager.filter(default_role_permissions_as_role__item=item,
                                        default_role_permissions_as_role__trashed=False)
    return (agent_roles, itemset_roles, default_roles)


def get_permissions_for_agent_and_item(agent, item):
    """
    Return a triple (user_permission_list, itemset_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    agent_perms = AgentPermission.objects.filter(item=item, agent=agent, trashed=False)
    itemset_perms = ItemSetPermission.objects.filter(item=item, itemset__pk__in=my_itemset_ids, trashed=False)
    default_perms = DefaultPermission.objects.filter(item=item, trashed=False)
    return (agent_perms, itemset_perms, default_perms)


def get_abilities_for_agent_and_item(agent, item):
    """
    Return a set of string-pairs (ability, ability_parameter)
    """
    roles_triple = get_roles_for_agent_and_item(agent, item)
    permissions_triple = get_permissions_for_agent_and_item(agent, item)
    abilities_yes = set()
    abilities_no = set()
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        cur_abilities_yes = set()
        cur_abilities_no = set()
        role_abilities = RoleAbility.objects.filter(trashed=False, role__in=role_list).all()
        import itertools
        for role_ability_or_permission in itertools.chain(role_abilities, permission_list):
            ability = role_ability_or_permission.ability
            ability_parameter = role_ability_or_permission.ability_parameter
            is_allowed = role_ability_or_permission.is_allowed
            if is_allowed:
                cur_abilities_yes.add((ability, ability_parameter))
            else:
                cur_abilities_no.add((ability, ability_parameter))
        # yes takes precedence over no
        for x in cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_yes.add(x)
        for x in cur_abilities_no - cur_abilities_yes:
            if x not in abilities_yes and x not in abilities_no:
                abilities_no.add(x)
    # anything left over is effectively "no"
    return abilities_yes


def filter_for_agent_and_ability(agent, ability, ability_parameter):
    my_itemset_ids = agent.all_containing_itemsets().values('pk').query
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=False).values('role_id').query

    perm_q = {}
    for agentitemsetdefault in ['agent', 'itemset', 'default']:
        for role in ['role', '']:
            for is_allowed in ['yes', 'no']:
                permission_class = eval("%s%sPermission" % ({'agent':'Agent','itemset':'ItemSet','default':'Default'}[agentitemsetdefault], role.capitalize()))
                args = {'trashed': False}
                if role == 'role':
                    args['role__pk__in'] = (relevant_yes_role_ids if is_allowed == 'yes' else relevant_no_role_ids)
                else:
                    args['ability'] = ability
                    args['ability_parameter'] = ability_parameter
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

def filter_agents_for_item_and_ability(item, ability, ability_parameter):
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=False).values('role_id').query

    perm_q = {}
    for agentitemsetdefault in ['agent', 'itemset', 'default']:
        for role in ['role', '']:
            for is_allowed in ['yes', 'no']:
                permission_class = eval("%s%sPermission" % ({'agent':'Agent','itemset':'ItemSet','default':'Default'}[agentitemsetdefault], role.capitalize()))
                args = {'trashed': False, 'item': item}
                if role == 'role':
                    args['role__pk__in'] = (relevant_yes_role_ids if is_allowed == 'yes' else relevant_no_role_ids)
                else:
                    args['ability'] = ability
                    args['ability_parameter'] = ability_parameter
                    args['is_allowed'] = (is_allowed == 'yes')
                if agentitemsetdefault == 'agent':
                    query = permission_class.objects.filter(**args).values('agent_id').query
                    perm_q["%s%s%s" % (agentitemsetdefault, role, is_allowed)] = Q(pk__in=query)
                elif agentitemsetdefault == 'itemset':
                    itemset_query = permission_class.objects.filter(**args).values('itemset_id').query
                    query = RecursiveItemSetMembership.objects.filter(parent__pk__in=itemset_query).values('child_id').query
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

