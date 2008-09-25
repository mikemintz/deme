from cms.models import *
from django.db.models import Q


################################################################################
# Global permissions
################################################################################


def get_global_roles_for_agent(agent):
    """
    Return a triple (user_role_list, group_role_list, default_role_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('pk').query
    role_manager = GlobalRole.objects.filter(trashed=False)
    direct_roles = role_manager.filter(agent_global_role_permissions_as_global_role__agent=agent,
                                       agent_global_role_permissions_as_global_role__trashed=False)
    groupwide_roles = role_manager.filter(group_global_role_permissions_as_global_role__pk__in=my_group_ids,
                                          group_global_role_permissions_as_global_role__trashed=False)
    default_roles = role_manager.filter(default_global_role_permissions_as_global_role__pk__isnull=False,
                                        default_global_role_permissions_as_global_role__trashed=False)
    return (direct_roles, groupwide_roles, default_roles)


def get_global_permissions_for_agent(agent):
    """
    Return a triple (user_permission_list, group_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('pk').query
    direct_roles = AgentGlobalPermission.objects.filter(trashed=False, agent=agent)
    groupwide_roles = GroupGlobalPermission.objects.filter(trashed=False, group__pk__in=my_group_ids)
    default_roles = DefaultGlobalPermission.objects.filter(trashed=False)
    return (direct_roles, groupwide_roles, default_roles)


def get_global_abilities_for_agent(agent):
    """
    Return a set of strings
    """
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
    Return a triple (user_role_list, group_role_list, default_role_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('pk').query
    role_manager = Role.objects.filter(trashed=False)
    direct_roles = role_manager.filter(agent_role_permissions_as_role__item=item,
                                       agent_role_permissions_as_role__agent=agent,
                                       agent_role_permissions_as_role__trashed=False)
    groupwide_roles = role_manager.filter(group_role_permissions_as_role__item=item,
                                          group_role_permissions_as_role__group__pk__in=my_group_ids,
                                          group_role_permissions_as_role__trashed=False)
    default_roles = role_manager.filter(default_role_permissions_as_role__item=item,
                                        default_role_permissions_as_role__trashed=False)
    return (direct_roles, groupwide_roles, default_roles)


def get_permissions_for_agent_and_item(agent, item):
    """
    Return a triple (user_permission_list, group_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('pk').query
    direct_permissions = AgentPermission.objects.filter(item=item, agent=agent, trashed=False)
    groupwide_permissions = GroupPermission.objects.filter(item=item, group__pk__in=my_group_ids, trashed=False)
    default_permissions = DefaultPermission.objects.filter(item=item, trashed=False)
    return (direct_permissions, groupwide_permissions, default_permissions)


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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('pk').query
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=False).values('role_id').query

    direct_yes_q = Q(agent_permissions_as_item__agent=agent,
                     agent_permissions_as_item__ability=ability,
                     agent_permissions_as_item__ability_parameter=ability_parameter,
                     agent_permissions_as_item__is_allowed=True,
                     agent_permissions_as_item__trashed=False)
    direct_no_q = Q(agent_permissions_as_item__agent=agent,
                    agent_permissions_as_item__ability=ability,
                    agent_permissions_as_item__ability_parameter=ability_parameter,
                    agent_permissions_as_item__is_allowed=False,
                    agent_permissions_as_item__trashed=False)
    group_yes_q = Q(group_permissions_as_item__group__pk__in=my_group_ids,
                    group_permissions_as_item__ability=ability,
                    group_permissions_as_item__ability_parameter=ability_parameter,
                    group_permissions_as_item__is_allowed=True,
                    group_permissions_as_item__trashed=False)
    group_no_q = Q(group_permissions_as_item__group__pk__in=my_group_ids,
                   group_permissions_as_item__ability=ability,
                   group_permissions_as_item__ability_parameter=ability_parameter,
                   group_permissions_as_item__is_allowed=False,
                   group_permissions_as_item__trashed=False)
    default_yes_q = Q(default_permissions_as_item__ability=ability,
                      default_permissions_as_item__ability_parameter=ability_parameter,
                      default_permissions_as_item__is_allowed=True,
                      default_permissions_as_item__trashed=False)
    default_no_q = Q(default_permissions_as_item__ability=ability,
                     default_permissions_as_item__ability_parameter=ability_parameter,
                     default_permissions_as_item__is_allowed=False,
                     default_permissions_as_item__trashed=False)

    role_direct_yes_q = Q(agent_role_permissions_as_item__agent=agent,
                          agent_role_permissions_as_item__role__pk__in=relevant_yes_role_ids,
                          agent_role_permissions_as_item__trashed=False)
    role_direct_no_q = Q(agent_role_permissions_as_item__agent=agent,
                         agent_role_permissions_as_item__role__pk__in=relevant_no_role_ids,
                         agent_role_permissions_as_item__trashed=False)
    role_group_yes_q = Q(group_role_permissions_as_item__group__pk__in=my_group_ids,
                         group_role_permissions_as_item__role__pk__in=relevant_yes_role_ids,
                         group_role_permissions_as_item__trashed=False)
    role_group_no_q = Q(group_permissions_as_item__group__pk__in=my_group_ids,
                        group_role_permissions_as_item__role__pk__in=relevant_no_role_ids,
                        group_role_permissions_as_item__trashed=False)
    role_default_yes_q = Q(default_role_permissions_as_item__role__pk__in=relevant_yes_role_ids,
                           default_role_permissions_as_item__trashed=False)
    role_default_no_q = Q(default_role_permissions_as_item__role__pk__in=relevant_no_role_ids,
                          default_role_permissions_as_item__trashed=False)

    return direct_yes_q |\
           role_direct_yes_q |\
           (~direct_no_q & ~role_direct_no_q & group_yes_q) |\
           (~direct_no_q & ~role_direct_no_q & role_group_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & default_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & role_default_yes_q)
