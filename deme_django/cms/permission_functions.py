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
    role_manager = GlobalRole.objects
    direct_roles = role_manager.filter(agent_global_role_permissions_as_global_role__agent=agent)
    groupwide_roles = role_manager.filter(group_global_role_permissions_as_global_role__group__group_memberships_as_group__agent=agent)
    default_roles = role_manager.filter(default_global_role_permissions_as_global_role__pk__isnull=False)
    return (direct_roles, groupwide_roles, default_roles)


def get_global_permissions_for_agent(agent):
    """
    Return a triple (user_permission_list, group_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    direct_roles = AgentGlobalPermission.objects.filter(agent=agent)
    groupwide_roles = GroupGlobalPermission.objects.filter(group__group_memberships_as_group__agent=agent)
    default_roles = DefaultGlobalPermission.objects.all()
    return (direct_roles, groupwide_roles, default_roles)


def get_global_abilities_for_agent(agent, possible_abilities=None):
    roles_triple = get_global_roles_for_agent(agent)
    permissions_triple = get_global_permissions_for_agent(agent)
    abilities_yes = set()
    abilities_no = set()
    if possible_abilities:
        abilities_unset = set(possible_abilities)
    else:
        abilities_unset = set([x[0] for x in POSSIBLE_GLOBAL_ABILITIES])
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        if possible_abilities != None:
            role_abilities = GlobalRoleAbility.objects.filter(global_role__in=role_list, ability_in=possible_abilities).all()
        else:
            role_abilities = GlobalRoleAbility.objects.filter(global_role__in=role_list).all()
        import itertools
        for role_ability_or_permission in itertools.chain(role_abilities, permission_list):
            ability = role_ability_or_permission.ability
            if ability in abilities_unset:
                # yes takes precedence over no
                if role_ability_or_permission.is_allowed:
                    abilities_yes.add(ability)
                    abilities_no.discard(ability)
                else:
                    if ability not in abilities_yes:
                        abilities_no.add(ability)
                abilities_unset.discard(ability)
    # anything left over in abilities_unset is effectively "no"
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
    role_manager = Role.objects
    direct_roles = role_manager.filter(agent_role_permissions_as_role__item=item,
                                       agent_role_permissions_as_role__agent=agent)
    groupwide_roles = role_manager.filter(group_role_permissions_as_role__item=item,
                                          group_role_permissions_as_role__group__group_memberships_as_group__agent=agent)
    default_roles = role_manager.filter(default_role_permissions_as_role__item=item)
    return (direct_roles, groupwide_roles, default_roles)


def get_permissions_for_agent_and_item(agent, item):
    """
    Return a triple (user_permission_list, group_permission_list, default_permission_list)
    """
    if not agent:
        raise Exception("You must create an anonymous user")
    direct_roles = AgentPermission.objects.filter(item=item, agent=agent)
    groupwide_roles = GroupPermission.objects.filter(item=item, group__group_memberships_as_group__agent=agent)
    default_roles = DefaultPermission.objects.filter(item=item)
    return (direct_roles, groupwide_roles, default_roles)


def get_abilities_for_agent_and_item(agent, item, possible_abilities=None):
    roles_triple = get_roles_for_agent_and_item(agent, item)
    permissions_triple = get_permissions_for_agent_and_item(agent, item)
    abilities_yes = set()
    abilities_no = set()
    if possible_abilities:
        abilities_unset = set(possible_abilities)
    else:
        abilities_unset = set([x[0] for x in POSSIBLE_ABILITIES])
    for role_list, permission_list in zip(roles_triple, permissions_triple):
        if possible_abilities != None:
            role_abilities = RoleAbility.objects.filter(role__in=role_list, ability_in=possible_abilities).all()
        else:
            role_abilities = RoleAbility.objects.filter(role__in=role_list).all()
        import itertools
        for role_ability_or_permission in itertools.chain(role_abilities, permission_list):
            ability = role_ability_or_permission.ability
            if ability in abilities_unset:
                # yes takes precedence over no
                if role_ability_or_permission.is_allowed:
                    abilities_yes.add(ability)
                    abilities_no.discard(ability)
                else:
                    if ability not in abilities_yes:
                        abilities_no.add(ability)
                abilities_unset.discard(ability)
    # anything left over in abilities_unset is effectively "no"
    return abilities_yes


def filter_for_agent_and_ability(agent, ability):
    direct_yes_q = Q(agent_permissions_as_item__agent=agent,
                     agent_permissions_as_item__ability=ability,
                     agent_permissions_as_item__is_allowed=True)
    direct_no_q = Q(agent_permissions_as_item__agent=agent,
                    agent_permissions_as_item__ability=ability,
                    agent_permissions_as_item__is_allowed=False)
    group_yes_q = Q(group_permissions_as_item__group__group_memberships_as_group__agent=agent,
                    group_permissions_as_item__ability=ability,
                    group_permissions_as_item__is_allowed=True)
    group_no_q = Q(group_permissions_as_item__group__group_memberships_as_group__agent=agent,
                   group_permissions_as_item__ability=ability,
                   group_permissions_as_item__is_allowed=False)
    default_yes_q = Q(default_permissions_as_item__ability=ability,
                      default_permissions_as_item__is_allowed=True)
    default_no_q = Q(default_permissions_as_item__ability=ability,
                     default_permissions_as_item__is_allowed=False)

    role_direct_yes_q = Q(agent_role_permissions_as_item__agent=agent,
                          agent_role_permissions_as_item__role__abilities_as_role__ability=ability,
                          agent_role_permissions_as_item__role__abilities_as_role__is_allowed=True)
    role_direct_no_q = Q(agent_role_permissions_as_item__agent=agent,
                         agent_role_permissions_as_item__role__abilities_as_role__ability=ability,
                         agent_role_permissions_as_item__role__abilities_as_role__is_allowed=False)
    role_group_yes_q = Q(group_role_permissions_as_item__group__group_memberships_as_group__agent=agent,
                         group_role_permissions_as_item__role__abilities_as_role__ability=ability,
                         group_role_permissions_as_item__role__abilities_as_role__is_allowed=True)
    role_group_no_q = Q(group_role_permissions_as_item__group__group_memberships_as_group__agent=agent,
                        group_role_permissions_as_item__role__abilities_as_role__ability=ability,
                        group_role_permissions_as_item__role__abilities_as_role__is_allowed=False)
    role_default_yes_q = Q(default_role_permissions_as_item__role__abilities_as_role__ability=ability,
                           default_role_permissions_as_item__role__abilities_as_role__is_allowed=True)
    role_default_no_q = Q(default_role_permissions_as_item__role__abilities_as_role__ability=ability,
                          default_role_permissions_as_item__role__abilities_as_role__is_allowed=False)

    return direct_yes_q |\
           role_direct_yes_q |\
           (~direct_no_q & ~role_direct_no_q & group_yes_q) |\
           (~direct_no_q & ~role_direct_no_q & role_group_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & default_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & role_default_yes_q)


