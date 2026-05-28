from collections import deque
from typing import get_origin, get_args, Any, Optional
import logging
from typeguard import typechecked

from sexpr.base import ClockedProperty, PropertyIrNode, PlaceholderNode, IrContainer, RawSExpr, NodeId, RawSExprList, Signal, LiteralType, Property, Sequence, Bool, Range, BoundedRange
from sexpr.primitives import And, ClkPropAlwaysRanged, ClkPropEventually, ClkPropStrongEventuallyRanged, Constant, FutureGclk, Not, Or, Initial, PropAcceptOn, PropNexttime, PropAnd, PropNot, PropOr, PropStrong, PropWeak, PropSeq, PropBool, PropWeakBool, PropStrongBool
from sexpr.primitives import PropOverlappedFollowedBy, PropOverlappedImplication, PropRejectOn, PropStrongNexttime, PropUntil, PropStrongUntilWith, PropRefuted
from sexpr.parsing import get_op_symbols, parse_expression



logger = logging.getLogger(__name__)



type RewriteRule = tuple[RawSExprList, RawSExprList]



# Boolean primitives

xor_rule: RewriteRule = (['xor', '<bool1>', '<bool2>'],
    ['or', ['and', '<bool1>', ['not', '<bool2>']], ['and', ['not', '<bool1>'], '<bool2>']])

eq_rule: RewriteRule = (['eq', '<bool1>', '<bool2>'],
    ['or', ['and', '<bool1>', '<bool2>'], ['and', ['not', '<bool1>'], ['not', '<bool2>']]])


rising_gclk_rule: RewriteRule = (['rising-gclk', 'clock_value', 'clock_defined'],
    ['and', ['not', ['and', 'clock_value', 'clock_defined']],
        ['future-gclk', ['and', 'clock_value', 'clock_defined']]])

falling_gclk_rule: RewriteRule = (['falling-gclk', 'clock_value', 'clock_defined'],
    ['and', ['not', ['and', ['not', 'clock_value'], 'clock_defined']],
        ['future-gclk', ['and', ['not', 'clock_value'], 'clock_defined']]])

changing_gclk: RewriteRule = (['changing-gclk', 'clock_value', 'clock_defined'],
    ['or', ['xor', ['clock_value', ['future-gclk', 'clock_value']]],
        ['xor', ['clock_defined', ['future-gclk', 'clock_defined']]]])


# Sequence primitives

delay_rule: RewriteRule = (['clk-seq-repeat', '<range>', '<clk_seq>'],
    ['clk-seq-concat', ['clk-seq-repeat', '<range>', ['clk-seq-bool', ['true']]], '<clk_seq>'])

goto_repeat_rule: RewriteRule = (['clk-seq-goto-repeat', '<range>', '<bool>'],
    ['clk-seq-repeat', '<range>', ['clk-seq-concat', ['clk-seq-repeat', ['range', '0', '$'], ['clk-seq-bool', ['not', '<bool>']]], ['clk-seq-bool', '<bool>']]])

nonconsecutive_repeat_rule: RewriteRule = (['clk-seq-nonconsecutive-repeat', '<range>', '<bool>'],
    ['clk-seq-concat', ['clk-seq-goto-repeat', '<range>', '<bool>'], ['clk-seq-repeat', ['range', '0', '$'], ['not', '<bool>']]])

# clk-seq-and might be more efficient to implement directly instead of rewriting (would be rewritten as intersect + delay)
# and the use of any number of arguments makes this rule more complex than a normal rewrite rule
# seq_and_rule: RewriteRule

throughout_rule: RewriteRule = (['clk-seq-throughout', '<bool>', '<clk_seq>'],
    ['clk-seq-intersect', ['clk-seq-repeat', ['range', '0', '$'], '<bool>'], '<clk_seq>'])

within_rule: RewriteRule = (['clk-seq-within', '<clk_seq1>', '<clk_seq2>'],
    ['clk-seq-intersect',
        ['clk-seq-concat',
            ['clk-seq-repeat', ['range', '0', '$'], ['clk-seq-bool', ['true']]],
            '<clk_seq2>',
            ['clk-seq-repeat', ['range', '0', '$'], ['clk-seq-bool', ['true']]]],
        '<clk_seq2>'])


# Property primitives

if_rule: RewriteRule = (['clk-prop-if', '<bool>', '<clk_prop>'],
    ['clk-prop-overlapped-implication', ['clk-seq-bool', '<bool>'], '<clk_prop>'])

if_else_rule: RewriteRule = (['clk-prop-if', '<bool>', '<clk_prop1>', '<clk_prop2>'],
    ['clk-prop-and',
        ['clk-prop-overlapped-implication', ['clk-seq-bool', '<bool>'], '<clk_prop1>'],
        ['clk-prop-or', ['clk-prop-weak', ['seq-bool', '<bool>']], '<clk_prop2>']])

# this rule is different for clocked and unclocked properties
# the rewriting rules are mostly defined for unclocked properties
# rewrite clock first?
# the following is for unclocked properties
non_overlapped_implication_rule: RewriteRule = (['clk-prop-non-overlapped-implication', '<seq>', '<prop>'],
    ['clk-prop-overlapped-implication', ['seq-concat', '<seq>', ['clk-seq-bool', ['true']]], '<prop>'])

implies_rule: RewriteRule = (['clk-prop-implies', '<clk_prop1>', '<clk_prop2>'], [])

iff_rule: RewriteRule = (['clk-prop-iff', '<clk_prop1>', '<clk_prop2>'], [])

# overlapped-followed-by is defined via negation of overlapped implication
# but we cannot use that here
non_overlapped_followed_by_rule: RewriteRule = (['clk-prop-non-overlapped-followed-by', '<clk_seq>', '<clk_prop>'],
    ['clk-prop-overlapped-followed-by', ['seq-concat', '<clk_seq>', ['clk-seq-bool', ['true']]], '<clk_prop>'])


strong_until_rule: RewriteRule = (['clk-prop-strong-until', '<clk_prop1>', '<clk_prop2>'], ['clk-prop-and', ['clk-prop-until', '<clk_prop1>', '<clk_prop2>'], ['clk-prop-strong-eventually', '<clk_prop2>']])

until_with_rule: RewriteRule = (['clk-prop-until-with', '<clk_prop1>', '<clk_prop2>'], ['clk-prop-until', '<clk_prop1>', ['clk-prop-and', '<clk_prop1>', '<clk_prop2>']])

# here already specific weak/strong of prop-bool? Does probably not matter which one is used? TODO
always_rule: RewriteRule = (['clk-prop-always', '<clk_prop>'], ['clk-prop-until', '<clk_prop>', ['prop-bool', ['false']]])

strong_eventually_rule: RewriteRule = (['clk-prop-strong-eventually', '<clk_prop>'], ['not', ['clk-prop-always', ['not', '<clk_prop>']]])

# -------------

# the following creates clk-prop-eventually, which can only be removed with a special rule below
strong_always_rule: RewriteRule = (['clk-prop-strong-always', '<bounded_range>', '<clk_prop>'], ['not', ['clk-prop-eventually', '<bounded_range>', ['not', '<clk_prop>']]])

# -------------

# this is rewritten to a conjunction of the form (nexttime m p and ... and nexttime n p) [bounded range]
# or to (nexttime m always p) [unbounded range]
# must be handled separately (get_ranged_rewrite_rule)
#always_ranged_rule: RewriteRule = (['clk-prop-always-ranged', '<range>', '<clk_prop>'], [])

# this is rewritten to a disjunction of the form (nexttime m p or ... or nexttime n p) [bounded range]
# must be handled separately (get_ranged_rewrite_rule)
#eventually_rule: RewriteRule

# this is rewritten to a disjunction of the form (s_nexttime m p or ... or s_nexttime n p) [bounded range]
# or to (s_nexttime m s_eventually p) [unbounded range]
# must be handled separately (get_ranged_rewrite_rule)
#strong_eventually_ranged_rule: RewriteRule

# -------------

# the following should probably be handled in clock rewriting TODO
#sync_accept_on_rule: RewriteRule
#sync_reject_on_rule: RewriteRule


def get_ranged_rewrite_rule(container: IrContainer, node_id: NodeId, rule) -> RewriteRule:
    """There are three ranged eventually/always primitives that cannot be rewritten with a simple primitive replacement
    as defined by a RewriteRule, but the rewrite rule looks differently depending on the range.
    Given a node with one of these primitives as node type, the applicable rewrite rule is returned.
    """

    rule = ([], [])

    node: PropertyIrNode = container[node_id]
    node_cls: type[PropertyIrNode] = type(node)

    if not (isinstance(node, ClkPropAlwaysRanged) or isinstance(node, ClkPropStrongEventuallyRanged) or isinstance(node, ClkPropEventually)):
        raise TypeError(f'Cannot generate ranged rewrite rule for node {node} with wrong node type')

    clk_prop: NodeId[ClockedProperty] = getattr(node, 'child2')

    # (nexttime m p and ... and nexttime n p) [bounded range] or (nexttime m always p) [unbounded range]
    if isinstance(node, ClkPropAlwaysRanged):
        range1: Range = getattr(node, 'child1')
        lhs: RawSExprList = ['clk-prop-always-ranged', '<range>', '<clk_prop>']
        if isinstance(range1.upper_bound.value, int):
            rhs: RawSExprList = ['clk-prop-and'] + [['clk-prop-nexttime', str(x), '<clk_prop>'] for x in range(bounded_range.lower_bound, bounded_range.upper_bound + 1)] # type: ignore
        else:
            rhs = ['clk-prop-nexttime', str(range1.lower_bound), ['clk-prop-always', '<clk_prop>']]

    # (s_nexttime m p or ... or s_nexttime n p) [bounded range]
    # or to (s_nexttime m s_eventually p) [unbounded range]
    elif isinstance(node, ClkPropStrongEventuallyRanged):
        range2: Range = getattr(node, 'child1')
        lhs: RawSExprList = ['clk-prop-strong-eventually-ranged', '<range>', '<clk_prop>']
        if isinstance(range2.upper_bound.value, int):
            rhs: RawSExprList = ['clk-prop-or'] + [['clk-prop-strong-nexttime', str(x), '<clk_prop>'] for x in range(bounded_range.lower_bound, bounded_range.upper_bound + 1)] # type: ignore
        else:
            rhs = ['clk-prop-strong-nexttime', str(range2.lower_bound), ['clk-prop-strong-eventually', '<clk_prop>']]

    # (nexttime m p or ... or nexttime n p)
    elif isinstance(node, ClkPropEventually):
        bounded_range: BoundedRange = getattr(node, 'child1')
        lhs: RawSExprList = ['clk-prop-eventually', '<bounded_range>', '<clk_prop>']
        rhs: RawSExprList = ['clk-prop-or'] + [['clk-prop-nexttime', str(x), '<clk_prop>'] for x in range(bounded_range.lower_bound, bounded_range.upper_bound + 1)] # type: ignore

    return (lhs, rhs)




dual_primitives: dict[type[PropertyIrNode], type[PropertyIrNode]] = {

    And: Or,
    Or: And,
    FutureGclk: FutureGclk, # child1 (bool) negated, child2 (bool) not negated

    PropOverlappedImplication: PropOverlappedFollowedBy, # child1 (seq) not negated
    PropOverlappedFollowedBy: PropOverlappedImplication, # child1 (seq) not negated
    PropRejectOn: PropAcceptOn, # child1 (bool) not negated
    PropAcceptOn: PropRejectOn, # child1 (bool) not negated
    PropNexttime: PropStrongNexttime,
    PropStrongNexttime: PropNexttime,
    PropUntil: PropStrongUntilWith, # swap child1 and child2
    PropStrongUntilWith: PropUntil, # swap child1 and child2
    PropOr: PropAnd,
    PropAnd: PropOr,

    PropStrongBool: PropWeakBool, # move negation into Bool
    PropWeakBool: PropStrongBool,  # move negation into Bool

    PropWeak: PropRefuted # child (seq) not negated
}


op_to_cls: dict[str, type[PropertyIrNode]] = get_op_symbols()



def replace_single_node(container: IrContainer, node_id: NodeId, rule: RewriteRule, add_identifiers_to_container: bool = False):
    """Replace a single node in the container in-place by an expression. The LHS of the rewrite rule has the form
    ['new_primitive_name', 'argument_identifier1', ...] and the RHS is a RawSExprList that can use the
    argument identifiers of the LHS to refer to the children of the node to replace.
    Thus, the LHS must be a list of strings (might extend to more complex patterns as needed).
    If add_identifiers_to_container is True, the child identifiers of the LHS of the rule will be uniquified and
    added to the container as local names (for debugging purposes).
    """

    node_to_replace: PropertyIrNode = container[node_id]
    node_id_repr: NodeId = node_to_replace.node_id

    rhs: RawSExprList = rule[1]

    primitive, arg_identifiers = get_lhs_primitive_and_identifiers(rule)

    # get children of node to replace
    # and put them into dict associating with identifiers in rule

    signature = type(node_to_replace).signature()
    if len(signature) != len(arg_identifiers):
        raise ValueError(f'Number of argument identifiers in {rule} does not match with child count of node {node_id}')

    children_dict: dict[str, NodeId | LiteralType] = dict() # individually named children
    children_list: list[NodeId] = list() # children list of arbitrary length (for primitives like 'and', 'or', etc.)
    children_list_identifier: Optional[str] = None # identifier the rule uses to refer to the list-type parameter

    for index, field in enumerate(node_to_replace.get_child_fields()):
        field_type: type = signature[index]
        if get_origin(field_type) is list:
            if len(arg_identifiers) != 1:
                raise ValueError(f'Rewrite rule {rule} for node {node_to_replace} with list-type argument must have exactly 1 argument identifier')
            children_list_identifier = arg_identifiers[0]
            children_list += getattr(node_to_replace, field.name)
        else:
            assert arg_identifiers[index] not in children_dict, f'Duplicate identifier {arg_identifiers[index]} in LHS of rewrite rule {rule}'
            children_dict[arg_identifiers[index]] = getattr(node_to_replace, field.name)

    # prepare dicts to replace literals in RHS of rewrite rule
    # (because they are not PropertyIr nodes, they cannot be bound to container identifiers)
    # and expand list of non-literal nodes in case of argument list

    children_node_dict: dict[str, NodeId] = dict() # map identifiers used in LHS to actual child nodes
    literals_to_replace: dict[str, RawSExpr] = dict() # map literal identifiers used in LHS to actual literals

    for identifier, child_elem in children_dict.items():
        if isinstance(child_elem, NodeId):
            children_node_dict[identifier] = child_elem
        elif isinstance(child_elem, LiteralType.__value__):
            literal_raw_sexpr: RawSExpr = container._generate_literal_raw_sexpr(child_elem)
            literals_to_replace[identifier] = literal_raw_sexpr

    if children_list_identifier is not None:
        for index, elem in enumerate(children_list):
            identifier: str = children_list_identifier + str(index)
            children_node_dict[identifier] = elem

    uniquified_children_node_dict: dict[str, NodeId] = dict() # map uniquified name to node id - only used for debug information
    local_nodes: dict[str, NodeId] = dict(container.global_nodes) # node identifier information handed to parse_expression
    child_name_mapping: dict[str, str] = dict() # map name used in LHS to uniquified name
    expanded_children_list: list[str] = [] # when the child of the LHS primitive is a list, it needs to be expanded to this list of identifiers

    # uniquify names used in LHS and add these node identifiers to the container as local node names
    if add_identifiers_to_container:
        for name in children_node_dict:
            unique_name: str = container.uniquify(name)
            container.node_names[unique_name] = children_node_dict[name]
            uniquified_children_node_dict[unique_name] = children_node_dict[name]
            child_name_mapping[name] = unique_name
            local_nodes[unique_name] = children_node_dict[name]
            if children_list_identifier is not None:
                expanded_children_list.append(unique_name)
        logger.debug('uniquified children: %s', uniquified_children_node_dict)

    else: # do not add the names to the container, but overwrite the dict local_nodes that will get handed to parse_expression
        for name in children_node_dict:
            local_nodes[name] = children_node_dict[name]
            if children_list_identifier is not None:
                expanded_children_list.append(name)

    # replace literals and child list identifier in RHS

    prepared_rhs: RawSExprList = prepare_rhs(rhs, literals_to_replace, child_name_mapping, (children_list_identifier, expanded_children_list))

    # call parse_expression on RHS

    root_node_id: NodeId = parse_expression(expr=prepared_rhs, expected_type=node_to_replace.type_class(), local_nodes=local_nodes, ir_container=container)
    root_node: PropertyIrNode = container[root_node_id]

    # replace node in container by root of parsed RHS expression
    # for this, add new placeholder that has the (representative) node_id of the node to replace
    # then instantiate/merge this new placeholder with root of the RHS (no references need to be rewritten this way)

    new_placeholder_node: PropertyIrNode = PlaceholderNode(ir_container=container, node_id=node_id_repr, expected_type=node_to_replace.type_class())
    container.nodes[node_id_repr] = new_placeholder_node
    new_placeholder_node.instantiate_placeholder(root_node)




def prepare_rhs(rhs: RawSExprList, literals_to_replace: dict[str, RawSExpr], child_name_mapping: dict[str, str], children_list_to_expand: tuple[Optional[str], list[str]]) -> RawSExprList:

    children_list_identifier: Optional[str] = children_list_to_expand[0]
    expanded_children_list: list[str] = children_list_to_expand[1]

    logger.debug('Prepare RHS subcall for input %s with children_list_identifier %s', rhs, children_list_identifier)
    logger.debug('Prepare RHS subcall for input %s with literals_to_replace %s', rhs, literals_to_replace)
    output_expression: RawSExprList = []
    for index, elem in enumerate(rhs):
        if index == 0 and type(elem) is str:
            output_expression.append(elem)
        elif index != 0 and type(elem) is str:
            if elem in literals_to_replace:
                output_expression.append(literals_to_replace[elem])
            elif elem == children_list_identifier:
                output_expression += expanded_children_list
            elif elem in child_name_mapping:
                output_expression.append(child_name_mapping[elem])
            else:
                output_expression.append(elem)
        elif isinstance(elem, list):
            prepared_sublist = prepare_rhs(elem, literals_to_replace, child_name_mapping, children_list_to_expand)
            output_expression.append(prepared_sublist)

    logger.debug('Prepared RHS subcall result for input %s: %s', rhs, output_expression)
    return output_expression



def get_lhs_primitive_and_identifiers(rule: RewriteRule) -> tuple[type[PropertyIrNode], list[str]]:

    lhs: RawSExprList = rule[0]

    primitive_name: Optional[str] = None
    children_identifiers: list[str] = list()

    for index, elem in enumerate(lhs):
        if type(elem) is not str:
            raise TypeError(f"LHS of rule {rule} must be list of strings of the form ['new_primitive_name', 'argument_identifier1', ...]")
        if index == 0:
            primitive_name = elem
        else:
            children_identifiers.append(elem)

    if primitive_name is None:
        raise TypeError(f"LHS of rule {rule} must be list of strings of the form ['new_primitive_name', 'argument_identifier1', ...]")
    new_primitive: type[PropertyIrNode] = op_to_cls[primitive_name]

    logger.debug('LHS: new primitive %s with children_identifiers %s', new_primitive, children_identifiers)

    return new_primitive, children_identifiers





def apply_rules(container: IrContainer, rules: dict[type, RewriteRule]):
    """Apply the provided rules to the expression graph in the container in a greedy way
    in-place until none of the rules can be applied anymore. Use a seminaive approach,
    where only nodes are considered for rewriting that changed in the previous pass
    through the graph. The rules must not enable any circular rewriting, or else this will
    end up in an infinite loop. For each node type, there can only be one rewrite rule."""

    nodes_to_visit: deque[NodeId] = deque(container.sink_nodes)
    encountered_nodes: set[NodeId] = set()

    logger.debug('Apply rules %s to container %s', rules, container)
    logger.debug('nodes_to_visit: %s', nodes_to_visit)

    nodes_to_rewrite: dict[NodeId, RewriteRule] = dict()

    # collect nodes to rewrite

    while len(nodes_to_visit) > 0: # outer loop will terminate when there are not more nodes to rewrite (when graph does not change anymore)
        while len(nodes_to_visit) > 0: # inner loop for one pass through the graph

            current_id: NodeId = nodes_to_visit.popleft()
            current_node = container[current_id]
            current_id_repr: NodeId = current_node.node_id
            current_cls = type(current_node)
            if current_cls in rules:
                nodes_to_rewrite[current_id_repr] = rules[current_cls]
            child_ids: list[NodeId] = current_node.get_child_ids()
            for child_id in child_ids:
                child_node: PropertyIrNode = container[child_id]
                child_cls = type(child_node)
                logger.debug('Child class: %s', child_cls)
                if child_id not in encountered_nodes:
                    nodes_to_visit.append(child_id)
                    encountered_nodes.add(child_id)

        logger.debug('encountered_nodes: %s', encountered_nodes)
        logger.debug('nodes_to_rewrite: %s', nodes_to_rewrite)

        # apply rewriting to all collected nodes

        for node_id, rewrite_rule in nodes_to_rewrite.items():
            replace_single_node(container, node_id, rewrite_rule)

            # consider newly added nodes for rewriting in the next pass and ignore the old ones
            nodes_to_visit.append(node_id)

        nodes_to_rewrite: dict[NodeId, RewriteRule] = dict()





def reduce_primitives(container: IrContainer):
    """Replace all primitives that do not exist in simple sequences and simple
    properties."""
    pass



def rewrite_clocks(container: IrContainer):
    """Rewrite the expression graph such that the global clock is used."""
    pass



@typechecked
def nnf_process_node(
    node_id: NodeId,
    container: IrContainer,
    invert: bool,
    output_container: IrContainer,
    corresponding_nodes: dict[tuple[NodeId, bool], NodeId],
    nodes_in_call_stack: set[tuple[NodeId, bool]]) -> NodeId:
    """Recursive function to process a node and all nodes reachable from it,
    to create corresponding expression graph in negation normal form.
    Bool parameter 'invert' states whether the input node needs to change polarity.
    The input expression is expected to be simple (unclocked, no empty matches)
    and contain none of the following primitives:
    xor, eq, glkc_rising, gclk_falling, gclk_changing."""


    # dicts should store representatives
    repr_id = container.merged_nodes.find(node_id)
    current_node = container[repr_id]

    logger.debug('--- nnf_process_node ---')
    logger.debug('Nodes in call stack: %s', nodes_in_call_stack)
    logger.debug('Current node: %s', current_node)
    logger.debug('Invert: %s', invert)

    # if same node is reached again in same call with conflicting polarity, cycle with odd number of negations detected
    if (repr_id, not invert) in nodes_in_call_stack:
        raise ValueError('Cycle with odd number of negations detected at node %s', container[repr_id])

    # if already existent and handled, return stored node from dict
    if (repr_id, invert) in corresponding_nodes:
        return corresponding_nodes[(repr_id, invert)]

    # generate output nodes for leaf cases

    if isinstance(current_node, Signal):
        if invert:
            added_node = output_container.add_node_by_kwargs(Not, {'child': corresponding_nodes[(repr_id, False)]})
            corresponding_nodes[(repr_id, True)] = added_node.node_id
            logger.debug('Added Not node: %s', added_node.node_id)
            return added_node.node_id
        else:
            raise ValueError('Signal with node id %s is missing in corresponding_nodes', repr_id)

    elif isinstance(current_node, Constant):
        new_value = current_node.value if not invert else not current_node.value
        added_node = output_container.add_node_by_kwargs(Constant, {'value': new_value})
        corresponding_nodes[(repr_id, invert)] = added_node.node_id
        logger.debug('Added Constant node: %s', added_node.node_id)
        return added_node.node_id

    elif isinstance(current_node, Initial) and invert:
        added_initial_node = output_container.add_node_by_kwargs(Initial, {})
        corresponding_nodes[(repr_id, False)] = added_initial_node.node_id
        added_not_node = output_container.add_node_by_kwargs(Not, {'child': corresponding_nodes[(repr_id, False)]})
        corresponding_nodes[(repr_id, True)] = added_not_node.node_id
        logger.debug('Added Not node: %s', added_not_node.node_id)
        logger.debug('Added Initial node: %s', added_initial_node.node_id)
        return added_not_node.node_id

    # negation of strong can be replaced by implication with consequent weak constant false
    # special case because the inverted primitive has not the same fields as the positive one
    elif invert and (isinstance(current_node, PropStrong)):

        placeholder_node = output_container.add_placeholder_node() # placeholder for implication with unknown child
        corresponding_nodes[(repr_id, True)] = placeholder_node.node_id
        logger.debug('Added placeholder node: %s', placeholder_node.node_id)

        nodes_in_call_stack.add((repr_id, True))

        result_id = nnf_process_node(current_node.child, container, False, output_container, corresponding_nodes, nodes_in_call_stack) # sequence type child of strong
        logger.debug('Output container nodes %s', output_container.nodes)

        # consequent of implication
        added_constant_false = output_container.add_node_by_kwargs(Constant, {'value': False})
        added_prop_bool = output_container.add_node_by_kwargs(PropWeakBool, {'child': added_constant_false.node_id})

        added_node_impl = output_container.add_node_by_kwargs(PropOverlappedImplication, {'child1': result_id, 'child2': added_prop_bool.node_id})
        placeholder_node.instantiate_placeholder(added_node_impl)
        logger.debug('Instantiated placeholder node %s with %s', placeholder_node.node_id, added_node_impl.node_id)

        nodes_in_call_stack.remove((repr_id, True))

        return added_node_impl.node_id

    elif isinstance(current_node, PropSeq) or isinstance(current_node, PropBool):
            raise ValueError(f'Encountered sequence property without weak or strong qualifier at node {current_node}')


    # add current node to recursion stack
    # which detects when there is a cycle and not just a shared subgraph
    nodes_in_call_stack.add((repr_id, invert))

    # handle negation, which does not cause a primitive to be generated, but only invokes a subcall with flipped polarity
    if isinstance(current_node, Not) or isinstance(current_node, PropNot):
        placeholder_node = output_container.add_placeholder_node()
        corresponding_nodes[(repr_id, invert)] = placeholder_node.node_id
        logger.debug('Added placeholder node: %s', placeholder_node.node_id)
        result_id = nnf_process_node(current_node.child, container, not invert, output_container, corresponding_nodes, nodes_in_call_stack)
        logger.debug('Output container nodes %s', output_container.nodes)
        placeholder_node.instantiate_placeholder(output_container[result_id])
        logger.debug('Instantiated placeholder node %s with %s', placeholder_node.node_id, result_id)
        nodes_in_call_stack.remove((repr_id, invert))
        return result_id


    # generate output nodes for other non-leaf cases

    # create PlaceholderNode for current node and put into dict
    # set type of placeholder to expected type, depending on polarity
    new_primitive_type = type(current_node) if not invert else dual_primitives[type(current_node)]
    placeholder_node = output_container.add_placeholder_node(expected_type=new_primitive_type)
    corresponding_nodes[(repr_id, invert)] = placeholder_node.node_id
    logger.debug('Added placeholder node: %s', placeholder_node.node_id)

    # call recursion for all non-literal children, with correct polarity
    # obtain child node ids

    signature = type(current_node).signature()
    kwargs: dict[str, Any] = {}

    for index, field in enumerate(current_node.get_child_fields()):
        field_type: type = signature[index]
        if get_origin(field_type) is list:
            list_elems = getattr(current_node, field.name)
            output_child_list = []
            for child_id in list_elems:
                output_child_id = nnf_process_node(child_id, container, invert, output_container, corresponding_nodes, nodes_in_call_stack)
                output_child_list.append(output_child_id)
            kwargs[field.name] = output_child_list

        elif issubclass(field_type, PropertyIrNode):
            child_id = getattr(current_node, field.name)
            # the following case includes PropWeak
            if issubclass(field_type, Sequence) or \
                (issubclass(field_type, Bool) and (isinstance(current_node, PropAcceptOn) or isinstance(current_node, PropRejectOn))) or \
                (issubclass(field_type, Bool) and (isinstance(current_node, FutureGclk) and field.name == 'child2')) or \
                isinstance(current_node, Sequence):
                output_child_id = nnf_process_node(child_id, container, False, output_container, corresponding_nodes, nodes_in_call_stack)
            elif issubclass(field_type, Property) or issubclass(field_type, Bool):
                output_child_id = nnf_process_node(child_id, container, invert, output_container, corresponding_nodes, nodes_in_call_stack)
            else:
                raise ValueError(f'Unexpected child node with name {field.name} of type {field_type} while processing {current_node}')
            kwargs[field.name] = output_child_id

        elif issubclass(field_type, LiteralType.__value__):
            child_literal = getattr(current_node, field.name)
            kwargs[field.name] = child_literal

    # swap children of PropUntil / PropStrongUntilWith
    if(isinstance(current_node, PropUntil) or isinstance(current_node, PropStrongUntilWith)):
        child1_temp = kwargs['child1']
        kwargs['child1'] = kwargs['child2']
        kwargs['child2'] = child1_temp

    # instantiate current placeholder node and set its children
    new_node = output_container.add_node_by_kwargs(new_primitive_type, kwargs)
    placeholder_node.instantiate_placeholder(new_node)
    logger.debug('Instantiated placeholder node %s with %s', placeholder_node.node_id, new_node.node_id)

    # remove current node from call stack
    nodes_in_call_stack.remove((repr_id, invert))

    return placeholder_node.node_id




@typechecked
def nnf(container: IrContainer) -> IrContainer:
    """Create a new expression graph that is the negation normal form of the
    graph stored in the container. If there are cycles with an odd number of
    negations, this results in an error. Cycles with an even number of negations
    are acceptable.
    The input expression is expected to be simple (unclocked, no empty matches)
    and contain none of the following primitives:
    xor, eq, glkc_rising, gclk_falling, gclk_changing."""

    output_container: IrContainer = IrContainer()

    corresponding_nodes: dict[tuple[NodeId, bool], NodeId] = dict() # input nodes and corresponding output nodes
    polarity_changed: dict[NodeId, bool] = dict() # keeps track if the polarity of an input node has been changed for odd loop detection

    # add signals to output container = set source nodes and their names
    for name, node_id in container.source_nodes.items():
        signal_repr_id = container.merged_nodes.find(node_id)
        signal_node = output_container.add_signal_node(name)
        corresponding_nodes[(signal_repr_id, False)] = signal_node.node_id
        logger.debug('Added Signal node %s', signal_node)
        output_container.global_nodes[name] = signal_node.node_id
        output_container.node_names[name] = signal_node.node_id
        output_container.source_nodes[name] = (signal_node.node_id)

    # depth-first search through expression graph
    # start recursion at unnamed roots (sink nodes), which will later be those used directly in assertion statements
    nodes_to_process: deque[NodeId] = deque(container.sink_nodes)

    while len(nodes_to_process) > 0:

        # for each node, call recursive helper function
        # hand down the dicts to keep track of visited nodes and polarity changes, and the output container

        current_id: NodeId = nodes_to_process.popleft()

        # if the node is already finished with positive polarity through another recursive function call, skip it
        # (but it is an unnamed root, so add it to sink nodes, or else it might get removed)
        if (current_id, False) in corresponding_nodes:
            corresponding_id = corresponding_nodes[current_id, False]
            output_container.sink_nodes.append(corresponding_id)
            continue

        logger.debug('nnf rewriting process node %s', container[current_id])

        # start with empty set as recursion stack
        output_node_id = nnf_process_node(current_id, container, False, output_container, corresponding_nodes, set())

        # add to sink nodes of output container because it corresponds to an unnamed rooot
        output_container.sink_nodes.append(output_node_id)


    # keep global node names of input nodes and transfer to output nodes
    # and set inner nodes of output container accordingly
    # (ignoring local node names)

    # if negation (Not etc.) has global name, it is moved to child node, except for literal case
    # (the negation is not removed, so the corresponding negation keeps the label unnegated)
    # (this happens without any special treatment of these cases)

    for (name, node_id) in container.global_nodes.items():

        logger.debug('Process global name %s of node %s', name, node_id)

        if name not in container.inner_nodes: # ignore Signal nodes without other global names
            continue

        # if uninverted, add to output container
        if (node_id, False) in corresponding_nodes:
            new_name = output_container.uniquify(name)
            output_container.global_nodes[new_name] = corresponding_nodes[(node_id, False)]
            output_container.node_names[new_name] = corresponding_nodes[(node_id, False)]
            output_container.inner_nodes[new_name] = corresponding_nodes[(node_id, False)]

        # if negated node, add negation indicator to node label
        if (node_id, True) in corresponding_nodes:
            new_name = output_container.uniquify(name + '_neg')
            output_container.global_nodes[new_name] = corresponding_nodes[(node_id, True)]
            output_container.node_names[new_name] = corresponding_nodes[(node_id, True)]
            output_container.inner_nodes[new_name] = corresponding_nodes[(node_id, True)]


    logger.debug('Global names output: %s', output_container.global_nodes.items())
    logger.debug('Inner nodes output: %s', output_container.inner_nodes.items())


    return output_container
