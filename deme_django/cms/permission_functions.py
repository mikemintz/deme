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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
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
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
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

    #return group_yes_q | default_yes_q # this is the majority of the bottleneck, so easier to debug SQL
    return direct_yes_q |\
           role_direct_yes_q |\
           (~direct_no_q & ~role_direct_no_q & group_yes_q) |\
           (~direct_no_q & ~role_direct_no_q & role_group_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & default_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & role_default_yes_q)


class filter_for_agent_and_ability2(Q):

    def __init__(self, agent, ability, ability_parameter):
        self.agent = agent
        self.ability = ability
        self.ability_parameter = ability_parameter

    def add_to_query(self, query, used_aliases):

        my_group_ids = self.agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
        relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=self.ability, ability_parameter=self.ability_parameter, is_allowed=True).values('role_id').query
        relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=self.ability, ability_parameter=self.ability_parameter, is_allowed=False).values('role_id').query

        from django.db.models.sql.query import AND, OR
        qn = query.quote_name_unless_alias
        qn2 = query.connection.ops.quote_name

        def add_joins_to_access_parts(alias, parts, can_reuse, opts):
            setup_result = query.setup_joins(parts, opts, alias, dupe_multis=True, allow_many=True, can_reuse=can_reuse, negate=False, process_extras=False)
            field, target, opts, join_list, last, extra_filters = setup_result
            #query.promote_alias_chain(join_list, False) # if we get too many inner joins, set the False to True
            query.promote_alias_chain(join_list, True) # we were getting too many
            return {'field':field, 'target':target, 'opts':opts, 'join_list':join_list}

        opts = query.get_meta()
        initial_alias = query.get_initial_alias()
        
        def add_permission_type(agent_group_or_default, role, is_allowed):
            permissions_related_name = '%s%s_permissions_as_item' % (agent_group_or_default, '_role' if role else '')
            reuse_set = set()

            join_info_trashed = add_joins_to_access_parts(initial_alias, [permissions_related_name, 'trashed'], reuse_set, opts)
            reuse_set.update(join_info_trashed['join_list'])
            def custom_join(default_join, default_params):
                return ("%s AND %s.%s = %%s" % (default_join, qn(join_info_trashed['join_list'][-1]), qn2('trashed')), default_params + [False])
            query.custom_join_map[join_info_trashed['join_list'][-1]] = custom_join

            join_info_details = add_joins_to_access_parts(initial_alias, [permissions_related_name, 'role' if role else 'ability'], reuse_set, opts)
            reuse_set.update(join_info_details['join_list'])
            def custom_join(default_join, default_params):
                alias = join_info_details['join_list'][-2 if role else -1]
                conditions = []
                params = []
                conditions.append(default_join)
                params.extend(default_params)

                if agent_group_or_default == 'agent':
                    conditions.append('%s.%s = %%s' % (qn(alias), qn2('agent_id')))
                    params.append(self.agent.pk)
                elif agent_group_or_default == 'group':
                    #TODO the alias names can clash in the group subquery with the outer query, will this be a problem?
                    my_group_ids_sql, my_group_ids_params = my_group_ids.as_sql()
                    conditions.append('%s.%s IN (%s)' % (qn(alias), qn2('group_id'), my_group_ids_sql))
                    params.extend(my_group_ids_params)
                elif agent_group_or_default == 'default':
                    pass # no extra conditions

                if role:
                    relevant_role_ids = relevant_yes_role_ids if is_allowed else relevant_no_role_ids
                    relevant_role_ids_sql, relevant_role_ids_params = relevant_role_ids.as_sql()
                    conditions.append('%s.%s IN (%s)' % (qn(alias), qn2('role_id'), relevant_role_ids_sql))
                    params.extend(relevant_role_ids_params)
                else:
                    conditions.append('%s.%s = %%s' % (qn(alias), qn2('ability')))
                    params.append(self.ability)
                    conditions.append('%s.%s = %%s' % (qn(alias), qn2('ability_parameter')))
                    params.append(self.ability_parameter)
                    conditions.append('%s.%s = %%s' % (qn(alias), qn2('is_allowed')))
                    params.append(is_allowed)

                return (' AND '.join(conditions), params)
            query.custom_join_map[join_info_details['join_list'][-2 if role else -1]] = custom_join

            join_info_id = add_joins_to_access_parts(initial_alias, [permissions_related_name, 'id'], reuse_set, opts)
            reuse_set.update(join_info_id['join_list'])
            return join_info_id


        def require_join_in_where_clause(join_info, negate=False):
            query.where.add((join_info['join_list'][-1], join_info['target'].column, join_info['field'], 'isnull', negate), AND)

        agent_direct_yes = add_permission_type('agent', role=False, is_allowed=True)
        group_direct_yes = add_permission_type('group', role=False, is_allowed=True)
        default_direct_yes = add_permission_type('default', role=False, is_allowed=True)
        agent_role_yes = add_permission_type('agent', role=True, is_allowed=True)
        group_role_yes = add_permission_type('group', role=True, is_allowed=True)
        default_role_yes = add_permission_type('default', role=True, is_allowed=True)
        
        agent_direct_no = add_permission_type('agent', role=False, is_allowed=False)
        group_direct_no = add_permission_type('group', role=False, is_allowed=False)
        agent_role_no = add_permission_type('agent', role=True, is_allowed=False)
        group_role_no = add_permission_type('group', role=True, is_allowed=False)

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_direct_yes)
        query.where.end_subtree()

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_role_yes)
        query.where.end_subtree()

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_direct_no, negate=True)
        require_join_in_where_clause(agent_role_no, negate=True)
        require_join_in_where_clause(group_direct_yes)
        query.where.end_subtree()

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_direct_no, negate=True)
        require_join_in_where_clause(agent_role_no, negate=True)
        require_join_in_where_clause(group_role_yes)
        query.where.end_subtree()

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_direct_no, negate=True)
        require_join_in_where_clause(agent_role_no, negate=True)
        require_join_in_where_clause(group_direct_no, negate=True)
        require_join_in_where_clause(group_role_no, negate=True)
        require_join_in_where_clause(default_direct_yes)
        query.where.end_subtree()

        query.where.start_subtree(OR)
        require_join_in_where_clause(agent_direct_no, negate=True)
        require_join_in_where_clause(agent_role_no, negate=True)
        require_join_in_where_clause(group_direct_no, negate=True)
        require_join_in_where_clause(group_role_no, negate=True)
        require_join_in_where_clause(default_role_yes)
        query.where.end_subtree()


def filter_for_agent_and_ability3(agent, ability, ability_parameter):
    my_group_ids = agent.group_memberships_as_agent.filter(trashed=False, group__trashed=False).values('group_id').query
    relevant_yes_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=True).values('role_id').query
    relevant_no_role_ids = RoleAbility.objects.filter(trashed=False, ability=ability, ability_parameter=ability_parameter, is_allowed=False).values('role_id').query

    direct_yes_q = Q(pk__in=AgentPermission.objects.filter(agent=agent, ability=ability, ability_parameter=ability_parameter, is_allowed=True, trashed=False).values('item_id').query)
    direct_no_q = Q(pk__in=AgentPermission.objects.filter(agent=agent, ability=ability, ability_parameter=ability_parameter, is_allowed=False, trashed=False).values('item_id').query)
    group_yes_q = Q(pk__in=GroupPermission.objects.filter(group__pk__in=my_group_ids, ability=ability, ability_parameter=ability_parameter, is_allowed=True, trashed=False).values('item_id').query)
    group_no_q = Q(pk__in=GroupPermission.objects.filter(group__pk__in=my_group_ids, ability=ability, ability_parameter=ability_parameter, is_allowed=False, trashed=False).values('item_id').query)
    default_yes_q = Q(pk__in=DefaultPermission.objects.filter(ability=ability, ability_parameter=ability_parameter, is_allowed=True, trashed=False).values('item_id').query)
    default_no_q = Q(pk__in=DefaultPermission.objects.filter(ability=ability, ability_parameter=ability_parameter, is_allowed=False, trashed=False).values('item_id').query)

    role_direct_yes_q = Q(pk__in=AgentRolePermission.objects.filter(agent=agent, role__pk__in=relevant_yes_role_ids, trashed=False).values('item_id').query)
    role_direct_no_q = Q(pk__in=AgentRolePermission.objects.filter(agent=agent, role__pk__in=relevant_no_role_ids, trashed=False).values('item_id').query)
    role_group_yes_q = Q(pk__in=GroupRolePermission.objects.filter(group__pk__in=my_group_ids, role__pk__in=relevant_yes_role_ids, trashed=False).values('item_id').query)
    role_group_no_q = Q(pk__in=GroupRolePermission.objects.filter(group__pk__in=my_group_ids, role__pk__in=relevant_no_role_ids, trashed=False).values('item_id').query)
    role_default_yes_q = Q(pk__in=DefaultRolePermission.objects.filter(role__pk__in=relevant_yes_role_ids, trashed=False).values('item_id').query)
    role_default_no_q = Q(pk__in=DefaultRolePermission.objects.filter(role__pk__in=relevant_no_role_ids, trashed=False).values('item_id').query)

    #return group_yes_q | default_yes_q # this is the majority of the bottleneck, so easier to debug SQL
    return direct_yes_q |\
           role_direct_yes_q |\
           (~direct_no_q & ~role_direct_no_q & group_yes_q) |\
           (~direct_no_q & ~role_direct_no_q & role_group_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & default_yes_q) |\
           (~direct_no_q & ~group_no_q & ~role_direct_no_q & ~role_group_no_q & role_default_yes_q)

filter_for_agent_and_ability = filter_for_agent_and_ability3
