from collections.abc import Callable
from itertools import product
from logging import getLogger

from ir.base import IrContainer, NodeId, PropertyIrNode
from ir.primitives.automata_primitives import (
    AutAcc,
    AutAnd,
    AutCallEx,
    AutCallFirst,
    AutConsume,
    AutFalse,
    AutOr,
    AutRead,
    AutRefuted,
    AutRepeat,
    AutRepeatUpTo,
    AutTrue,
    FiniteAutomaton,
    OmegaAcceptOn,
    OmegaAnd,
    OmegaAutomaton,
    OmegaCallAll,
    OmegaCallExStrong,
    OmegaCallExWeak,
    OmegaFalse,
    OmegaOr,
    OmegaRejectOn,
    OmegaStrongConsume,
    OmegaStrongConsumeAcc,
    OmegaStrongRead,
    OmegaTrue,
    OmegaWeakConsume,
    OmegaWeakConsumeAcc,
    OmegaWeakRead,
)

from tests.evaluate import (
    FencepostPosition,
    MaybeBool,
    Trace,
    eval_and,
    eval_or,
    evaluate_bool,
)

logger = getLogger(__name__)

type Conjunction = frozenset[State]

type Configuration = frozenset[Conjunction]

EMPTY_CONF: Configuration = frozenset()

# for subcalls we add delayed states (= NodeIdWithPos) to the configuration
# (initial state of the successor automaton for all acceptance positions of the subcall automaton)
# with the FencepostPosition when will become active
# that is necessary to enter those states with the correct boolean combination
type NodeIdWithPos = tuple[NodeId, FencepostPosition]
type State = NodeId | NodeIdWithPos


#------------------+
#  FINITE AUTOMATA |
#------------------+



def simplify_conf(configuration: Configuration, container: IrContainer) -> Configuration:
    """For evaluating alternating automata, the configuration is a frozenset of
    frozensets (disjunction of conjunctions). To keep this representation small,
    remove conjunctions that are a superset of other conjunctions, and check
    whether true/false-sinks are contained in a frozenset to simplify it."""

    logger.debug('simplify configuration %s', configuration)

    candidates: set[frozenset[State]] = set()
    false_sinks: set[NodeId] = set()

    # conjunction with True -> remove True
    # conjunction with False -> False
    # empty conjunction -> True
    for conjunction in configuration:
        non_sink_nodes: set[State] = set()
        true_sinks: set[NodeId] = set()
        has_false: bool = False
        for state in conjunction:
            if isinstance(state, NodeId):
                node_id: NodeId = state
                if isinstance(container[node_id], AutTrue):
                    true_sinks.add(node_id)
                elif isinstance(container[node_id], AutFalse):
                    has_false = True
                    false_sinks.add(node_id)
                else:
                    non_sink_nodes.add(node_id)
            else:
                non_sink_nodes.add(state)
        if not has_false and len(non_sink_nodes) > 0:
            candidates.add(frozenset(non_sink_nodes))
        if not has_false and len(non_sink_nodes) == 0:
            # there is no difference within True-sinks and False-sinks
            # but we do not need to identify them with each other because they will get removed anyway
            # choose one arbitrary to represent

            # disjunction with True -> True
            # thus if there is a conjunction that is a True-singleton, that becomes the whole configuration
            # but if there are no successor states at all, the empty configuration is returned that is False
            if len(true_sinks) == 0:
                return EMPTY_CONF
            return frozenset([frozenset([true_sinks.pop()])])
        # disjunction with False -> remove False
        # this

    # empty disjunction -> False
    # choose one False-sink as a representative of the whole configuration
    if len(candidates) == 0:
        return EMPTY_CONF
        #return frozenset([frozenset([false_sinks.pop()])])
        # TODO choose here the right (empty or False-singleton?)
        #return frozenset([frozenset()])

    # remove supersets from the remaining candidates
    filtered_candidates: set[frozenset[State]] = set()
    for conj1 in candidates:
        is_proper_superset: bool = False
        for conj2 in candidates:
            if conj1 != conj2 and conj1.issuperset(conj2):
                is_proper_superset = True
        if not is_proper_superset:
            filtered_candidates.add(conj1)

    return frozenset(filtered_candidates)


def conf_and(configurations: set[Configuration], container: IrContainer) -> Configuration:
    """Combine configurations using a conjunction."""

    # all possibilities where from each configuration, we select one conjunction
    # and take the union with the other selected conjunctions
    # = the cross product of configurations

    logger.debug('AND of %s', configurations)

    crossproduct: set[frozenset[State]] = {frozenset().union(*selection) for selection in product(*configurations)}
    return simplify_conf(frozenset(crossproduct), container)


def conf_or(configurations: set[Configuration], container: IrContainer) -> Configuration:
    """Combine configurations using a disjunction."""

    logger.debug('OR of %s', configurations)

    conf_union: Configuration = frozenset().union(*configurations)
    return simplify_conf(conf_union, container)


def evaluate_finite_automaton_primitive(node_id: NodeId[FiniteAutomaton],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> tuple[Configuration, bool]:
    """Evaluate a single FiniteAutomaton node on a trace starting at
    FencepostPosition pos. Returns a representation of the new configuration
    after reading one symbol as a frozenset of frozensets (disjunction of
    conjunctions). Also returns whether the automaton accepts at the current
    position."""

    # the next step is reached when consume, true, or false is encountered
    # then the result is returned
    # if aut-acc was encountered along the way, the the automaton accepts at the
    # current position
    # it is assumed that there are no cycles in the automaton without consume/true/false
    # (= no epsilon-cycles)
    # it is also assumed that after aut-acc there is no aut-read that can change that result
    # (because the automaton construction can not produce such automata)

    # TODO add memoization

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, FiniteAutomaton))
    node_repr: NodeId = container.merged_nodes.find(node_id)

    result_set: Configuration = frozenset()
    acceptance_result: bool = False

    if isinstance(node, AutTrue): # stay in this state - accepting
        result_set = frozenset([frozenset([node_repr])])
        acceptance_result: bool = True

    elif isinstance(node, AutFalse): # stay in this state - not accepting
        result_set = frozenset([frozenset([node_repr])])

    elif isinstance(node, AutConsume):
        bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})
        if bool_result == 'top':
            result_set = frozenset([
                frozenset([container.merged_nodes.find(node.child2)]),
                frozenset([container.merged_nodes.find(node.child3)])])
        elif bool_result == 'bot':
            result_set = frozenset()
        elif bool_result == True:
            result_set = frozenset([frozenset([container.merged_nodes.find(node.child2)])])
        elif bool_result == False:
            result_set = frozenset([frozenset([container.merged_nodes.find(node.child3)])])
        else:
            raise ValueError('Encountered unknown bool result in AutConsume evaluation with trace %s at position %s', trace, pos)

    elif isinstance(node, AutRead):
        bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})
        if bool_result == 'top':
            result_set1, acc1 = evaluate_finite_automaton_primitive(node.child2, container, trace, pos)
            result_set2, acc2 = evaluate_finite_automaton_primitive(node.child3, container, trace, pos)
            result_set = conf_or({result_set1, result_set2}, container)
            acceptance_result = acc1 or acc2
        elif bool_result == 'bot':
            result_set = frozenset()
        elif bool_result == True:
            result_set, acceptance_result = evaluate_finite_automaton_primitive(node.child2, container, trace, pos)
        elif bool_result == False:
            result_set, acceptance_result = evaluate_finite_automaton_primitive(node.child3, container, trace, pos)
        else:
            raise ValueError('Encountered unknown bool result in AutRead evaluation with trace %s at position %s', trace, pos)

    elif isinstance(node, AutAcc): # accept at pos
        result_set, _ = evaluate_finite_automaton_primitive(node.child, container, trace, pos)
        acceptance_result = True

    elif isinstance(node, (AutOr, AutAnd)):
        result_set_set: set[Configuration] = set()
        acc_set: set[bool] = set()
        for child in node.children:
            result_set_temp, acc_temp = evaluate_finite_automaton_primitive(child, container, trace, pos)
            result_set_set.add(result_set_temp)
            acc_set.add(acc_temp)
        if isinstance(node, AutOr):
            result_set = conf_or(result_set_set, container)
            acceptance_result = True in acc_set
        elif isinstance(node, AutAnd):
            result_set = conf_and(result_set_set, container)
            acceptance_result = False not in acc_set



    elif isinstance(node, (AutCallEx, AutCallFirst)):

        logger.debug('SUBCALL primitive at %s', node)

        subcall_init: NodeId = node.child1
        successor_init: NodeId = container.merged_nodes.find(node.child2)
        subcall_matches: list[FencepostPosition] = evaluate_finite_automaton(subcall_init, container, trace, pos)

        logger.debug('-- subcall_matches: %s', subcall_matches)

        if len(subcall_matches) == 0:
           result_set = EMPTY_CONF

        else:
            # if the first match is at the current step, we need to evaluate
            # the successor state to get the configuration for the next step
            first_match: FencepostPosition = subcall_matches[0]
            if first_match == pos:
                subcall_matches.pop(0)

            if isinstance(node, AutCallEx):
                successor_states: frozenset[frozenset[tuple[NodeId, FencepostPosition]]] = frozenset([
                    frozenset([(successor_init, match)]) for match in subcall_matches])
                if first_match == pos:
                    current_step_next_conf, acceptance_result = evaluate_finite_automaton_primitive(successor_init, container, trace, pos)
                    result_set = conf_or({current_step_next_conf, successor_states}, container)
                else:
                    result_set =  successor_states

            elif isinstance(node, AutCallFirst):

                if first_match == pos:
                    current_step_next_conf, acceptance_result = evaluate_finite_automaton_primitive(successor_init, container, trace, pos)
                    result_set = current_step_next_conf
                else:
                    result_set = frozenset([frozenset([(successor_init, first_match)])])


    elif isinstance(node, AutRepeat): # noqa
        raise NotImplementedError
    elif isinstance(node, AutRepeatUpTo): # noqa
        raise NotImplementedError
    elif isinstance(node, AutRefuted):
        raise NotImplementedError

    logger.debug('--> Return at pos %s acceptance %s with result_set %s', pos, acceptance_result, result_set)

    return result_set, acceptance_result


def remove_pos_from_current_states(conf: Configuration, pos: FencepostPosition) -> Configuration:
    """Modify each of the delayed states in the configuration (that were
    generated by subcalls) that coincide with the given FencepostPostition
    such that the position annotation gets removed and they can be handled in
    the same manner as other states for the current time step."""

    remove_pos_if_now: Callable[[State, FencepostPosition], State] = lambda state, pos:\
        state[0] if isinstance(state, tuple) and state[1] == pos else state
    updated_conf: set[frozenset[State]] = {frozenset({remove_pos_if_now(state, pos)\
        for state in conjunction}) for conjunction in conf}
    return frozenset(updated_conf)


def evaluate_finite_automaton_conf(conf: Configuration,
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> tuple[Configuration, bool]:
    """Evaluate a configuration on a trace starting at FencepostPosition pos.
    Returns a representation of the new configuration after reading one symbol
    as a frozenset of frozensets (disjunction of conjunctions).
    Also returns whether the automaton accepts at the current position.
    States that belong to the current position are evaluated immediately.
    Delayed states that should be handled in later time steps are put back into
    the result as-is."""

    updated_conf: Configuration = remove_pos_from_current_states(conf, pos)
    logger.debug('Evaluate configuration %s at pos %s', conf, pos)
    logger.debug('Updated configuration: %s', updated_conf)

    conjunction_conf_results: set[Configuration] = set()
    conjunction_acc_results: set[bool] = set()
    for conjunction in updated_conf:

        now_states: set[NodeId] = {state for state in conjunction if isinstance(state, NodeId)}
        delayed_states: set[NodeIdWithPos] = {state for state in conjunction if isinstance(state, tuple)}

        result_pairs: set[tuple[Configuration, bool]] = {
            evaluate_finite_automaton_primitive(node_id, container, trace, pos) for node_id in now_states}
        conf_results: set[Configuration] = {pair[0] for pair in result_pairs}
        acc_results: set[bool] = {pair[1] for pair in result_pairs}

        conf_results.add(frozenset([frozenset(delayed_states)]))
        conjunction_conf_results.add(conf_and(conf_results, container))
        conjunction_acc_results.add(all(acc_results) and len(delayed_states) == 0)

    disjunction_conf_result: Configuration = conf_or(conjunction_conf_results, container)
    disjunction_acc_result: bool = any(conjunction_acc_results)
    return (disjunction_conf_result, disjunction_acc_result)



def evaluate_finite_automaton_conf_infinite_suffix(conf: Configuration,
        container: IrContainer,
        trace: Trace) -> MaybeBool:
    """Evaluate the finite automaton on the infinite suffix. If the automaton
    accepts at any position in the infinite suffix, True is returned. If a loop
    of the configuration is detected without accepting, False is returned.
    A conjunction of accepting positions in the infinite suffix can lead to an
    unknown result. We do not keep track of where exactly a subcall with a
    match within the infinite suffix will continue the computation in the
    successor automaton. This corresponds to sequence intersection, which also
    can have an unknown result."""

    next_configuration: Configuration = conf
    seen_configurations: set[Configuration] = set()
    unknown_seen: bool = False

    while next_configuration not in seen_configurations:

        seen_configurations.add(next_configuration)

        # delayed states in the configuration are all 'within_infinite_suffix'
        # we do not know when they will become active, so we treat their result as 'unknown'
        # and let them stay in the next configuration
        # (they might yield any result in any step in the infinite suffix)

        conjunction_conf_results: set[Configuration] = set()
        conjunction_acc_results: set[MaybeBool] = set()
        for conjunction in next_configuration:

            now_states: set[NodeId] = {state for state in conjunction if isinstance(state, NodeId)}
            delayed_states: set[NodeIdWithPos] = {state for state in conjunction if isinstance(state, tuple)}

            result_pairs: set[tuple[Configuration, bool]] = {
                evaluate_finite_automaton_primitive(node_id, container, trace, FencepostPosition('within_infinite_suffix')) for node_id in now_states}
            conf_results: set[Configuration] = {pair[0] for pair in result_pairs}
            acc_results: set[MaybeBool] = {pair[1] for pair in result_pairs}

            conf_results.add(frozenset([frozenset(delayed_states)]))
            conjunction_conf_results.add(conf_and(conf_results, container))
            if len(delayed_states) > 0:
                acc_results.add('unknown')
            conjunction_acc_results.add(eval_and(acc_results))

        disjunction_conf_result: Configuration = conf_or(conjunction_conf_results, container)
        disjunction_acc_result: MaybeBool = eval_or(conjunction_acc_results)

        if disjunction_acc_result == True:
            return True
        elif disjunction_acc_result == 'unknown':
            unknown_seen = True

        next_configuration = disjunction_conf_result

    if unknown_seen:
        return 'unknown'

    return False



def evaluate_finite_automaton(node_id: NodeId[FiniteAutomaton],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> list[FencepostPosition]:
    """Evaluate a single FiniteAutomaton node on a trace starting at
    FencepostPosition pos. Returns a list of FencepostPositions
    where the automaton accepts."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, FiniteAutomaton))
    node_repr: NodeId = container.merged_nodes.find(node_id)

    logger.debug('---- START of evaluation %s on trace %s at pos %s', node, trace, pos)

    acc_pos: list[FencepostPosition] = []

    next_conf: Configuration = frozenset([frozenset([node_repr])])
    next_pos: FencepostPosition = pos

    while next_conf != EMPTY_CONF and next_pos != FencepostPosition('within_infinite_suffix'):
        assert isinstance(next_pos.value, tuple)

        logger.debug('Evaluate %s on trace %s at pos %s', node, trace, pos)
        logger.debug('CONFIGURATION: %s', next_conf)
        next_conf, acc_result = evaluate_finite_automaton_conf(next_conf, container, trace, next_pos)
        if acc_result:
            acc_pos.append(next_pos)
            logger.debug('Add pos %s to accepting positions', next_pos)
        next_pos = next_pos.next_pos(trace)

    # we assume that we can have only matches in the infinite suffix if it is top_omega
    if next_conf != EMPTY_CONF and trace.suffix == 'top_omega':
        suffix_result: MaybeBool = evaluate_finite_automaton_conf_infinite_suffix(next_conf, container, trace)
        if suffix_result == True:
            acc_pos.append(FencepostPosition('within_infinite_suffix'))
            logger.debug('Add pos within_infinite_suffix to accepting positions')
        elif suffix_result == 'unknown':
            acc_pos.append(FencepostPosition('unknown'))
            logger.debug('Add pos unknown to accepting positions')

    logger.debug('---- RETURN of evaluation %s on trace %s at pos %s', node, trace, pos)
    logger.debug('acc_pos: %s', acc_pos)

    return acc_pos




#------------------+
#  OMEGA AUTOMATA  |
#------------------+


type OmegaConjunction = tuple[Conjunction, Conjunction]

# each conjunction of the OmegaConfiguration is associated with a set of obligations
# these are the states that still owe a visit to an accepting state
# since that has not happened since the last reset of obligations
# (= the time step when the obligation set was empty and then fillied again for the next round)
type OmegaConfiguration = frozenset[OmegaConjunction]



def simplify_omega_conf(configuration: OmegaConfiguration, container: IrContainer):
    return configuration
    # TODO simplify OmegaConfiguration


def omega_conf_and(configurations: set[OmegaConfiguration], container: IrContainer) -> OmegaConfiguration:
    """Combine OmegaConfigurations using a conjunction. Select one conjunction+obligations
    from each OmegaConfiguration. Take the union of the states in the conjunction
    and obligations."""

    logger.debug('AND of %s', configurations)

    pairwise_crossproduct: set[tuple[frozenset[State], frozenset[State]]] = {
        (frozenset().union(*state_selection), frozenset().union(*obligations_selection))
            for (state_selection, obligations_selection)  in product(*configurations)}

    return simplify_omega_conf(frozenset(pairwise_crossproduct), container)


def omega_conf_or(configurations: set[OmegaConfiguration], container: IrContainer) -> OmegaConfiguration:
    """Combine OmegaConfigurations using a disjunction.
    The obligations of each conjunction remain unchanged."""

    logger.debug('OR of %s', configurations)

    conf_union: OmegaConfiguration = frozenset().union(*configurations)
    return simplify_omega_conf(conf_union, container)


def evaluate_omega_automaton_primitive(node_id: NodeId[OmegaAutomaton],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> OmegaConfiguration:
    """Evaluate a single OmegaAutomaton node on a trace starting at
    FencepostPosition pos. Returns a representation of the new configuration
    after reading one symbol (disjunction of conjunction-obligations pairs)."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, OmegaAutomaton))
    node_repr: NodeId = container.merged_nodes.find(node_id)
    result_configuration: OmegaConfiguration

    #---- SINKS

    if isinstance(node, OmegaTrue):
        conjunction: Conjunction = frozenset([node_repr])
        obligations: Conjunction = frozenset()
        result_configuration = frozenset([(conjunction, obligations)])

    elif isinstance(node, OmegaFalse):
        conjunction: frozenset[State] = frozenset([node_repr])
        obligations = frozenset([node_repr])
        result_configuration = frozenset([(conjunction, obligations)])

    #---- CONSUME/READ

    elif isinstance(node, (OmegaStrongConsume, OmegaWeakConsume, OmegaStrongConsumeAcc, OmegaWeakConsumeAcc)):

        if isinstance(node, (OmegaWeakConsume, OmegaWeakConsumeAcc)) and trace.suffix == 'end' and pos >= len(trace.finite_part):
            bool_result = 'top'
        else:
            bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})

        if bool_result == 'top':
            conjunction1 = frozenset([container.merged_nodes.find(node.child2)])
            conjunction2 = frozenset([container.merged_nodes.find(node.child3)])
            obligations1 = frozenset() if isinstance(node, (OmegaStrongConsumeAcc, OmegaWeakConsumeAcc)) else conjunction1
            obligations2 = frozenset() if isinstance(node, (OmegaStrongConsumeAcc, OmegaWeakConsumeAcc)) else conjunction2
            result_configuration = frozenset([(conjunction1, obligations1), (conjunction2, obligations2)])
        elif bool_result == 'bot':
            result_configuration = frozenset() # empty disjunction
        elif bool_result in [True, False]:
            if bool_result == True:
                conjunction = frozenset([container.merged_nodes.find(node.child2)])
            elif bool_result == False:
                conjunction = frozenset([container.merged_nodes.find(node.child3)])
            obligations = frozenset() if isinstance(node, (OmegaStrongConsumeAcc, OmegaWeakConsumeAcc)) else conjunction
            result_configuration = frozenset([(conjunction, obligations)])
        else:
            raise ValueError('Encountered unknown bool result in %s evaluation with trace %s at position %s', node.node_type(), trace, pos)


    elif isinstance(node, (OmegaStrongRead, OmegaWeakRead)):

        if isinstance(node, OmegaWeakRead) and trace.suffix == 'end' and pos >= len(trace.finite_part):
            bool_result = 'top'
        else:
            bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})

        if bool_result == 'top':
            child1_result = evaluate_omega_automaton_primitive(node.child2, container, trace, pos)
            child2_result = evaluate_omega_automaton_primitive(node.child3, container, trace, pos)
            result_configuration = omega_conf_or({child1_result, child2_result}, container)
        elif bool_result == 'bot':
            result_configuration = frozenset() # empty disjunction
        elif bool_result == True:
            result_configuration = evaluate_omega_automaton_primitive(node.child2, container, trace, pos)
        elif bool_result == False:
            result_configuration = evaluate_omega_automaton_primitive(node.child3, container, trace, pos)
        else:
            raise ValueError('Encountered unknown bool result in %s evaluation with trace %s at position %s', node.node_type(), trace, pos)

    #---- AND/OR

    elif isinstance(node, (OmegaAnd, OmegaOr)):

        child_results: set[OmegaConfiguration] = set()
        for child in node.children:
            child_results.add(evaluate_omega_automaton_primitive(child, container, trace, pos))

        if isinstance(node, OmegaAnd):
            result_configuration = omega_conf_and(child_results, container)
        elif isinstance(node, OmegaOr):
            result_configuration = omega_conf_or(child_results, container)

    #-----


    elif isinstance(node, OmegaAcceptOn): # noqa
        raise NotImplementedError
    elif isinstance(node, OmegaRejectOn): # noqa
        raise NotImplementedError

    #----- SUBCALLS

    elif isinstance(node, OmegaCallAll): # noqa
        raise NotImplementedError
        # end -> bot_omega
        # switch top_omega <-> bot_omega
        # conjunction of delayed states

    elif isinstance(node, OmegaCallExStrong): # noqa
        raise NotImplementedError
        # end -> bot_omega
        # disjunction of delayed states

    elif isinstance(node, OmegaCallExWeak):
        raise NotImplementedError
        # end -> top_omega
        # disjunction of delayed states

    else:
        raise ValueError('Unexpected primitive %s in omega automaton evaluation', node.node_type())


    return result_configuration





def evaluate_omega_automaton_conf(conf: Configuration,
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> tuple[Configuration, bool]:
    raise NotImplementedError


def evaluate_omega_automaton_conf_infinite_suffix(conf: Configuration,
    container: IrContainer,
    trace: Trace) -> bool:
    """Evaluate the omega automaton on the infinite suffix.
    Build a graph of conjunction-obligation pairs and check every 2^n steps
    whether there is a cycle containing a conjunction with empty obligations.
    If yes, return True.
    Return False if the same configuration is reached without such a cycle,
    or abort after a certain number of steps."""

    raise NotImplementedError



def evaluate_omega_automaton(node_id: NodeId[OmegaAutomaton],
    container: IrContainer,
    trace: Trace) -> MaybeBool:
    """Evaluate the omega automaton by first evaluating the finite part,
    and then starting from the configuration at the beginning of the suffix,
    detecting an accepting cycle in the infinite suffix.
    A result can already be returned in the finite part if the configuration
    is a true-/false-sink."""

    raise NotImplementedError
