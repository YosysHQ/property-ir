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
    OmegaAutomaton,
)

from tests.evaluate import FencepostPosition, MaybeBool, Trace, evaluate_bool

logger = getLogger(__name__)

type Configuration = frozenset[frozenset[NodeId]]

EMPTY_CONF: Configuration = frozenset([frozenset()])


#------------------+
#  FINITE AUTOMATA |
#------------------+



def simplify_conf(configuration: Configuration, container: IrContainer) -> Configuration:
    """For evaluating alternating automata, the configuration is a frozenset of
    frozensets (disjunction of conjunctions). To keep this representation small,
    remove conjunctions that are a superset of other conjunctions, and check
    whether true/false-sinks are contained in a frozenset to simplify it."""

    logger.debug('simplify configuration %s', configuration)

    candidates: set[frozenset[NodeId]] = set()
    false_sinks: set[NodeId] = set()

    # conjunction with True -> remove True
    # conjunction with False -> False
    # empty conjunction -> True
    for conjunction in configuration:
        non_sink_nodes: set[NodeId] = set()
        true_sinks: set[NodeId] = set()
        has_false: bool = False
        for node_id in conjunction:
            if isinstance(container[node_id], AutTrue):
                true_sinks.add(node_id)
            elif isinstance(container[node_id], AutFalse):
                has_false = True
                false_sinks.add(node_id)
            else:
                non_sink_nodes.add(node_id)
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
        return frozenset([frozenset([false_sinks.pop()])])
        # TODO choose here the right (empty or False-singleton?)
        #return frozenset([frozenset()])

    # remove supersets from the remaining candidates
    filtered_candidates: set[frozenset[NodeId]] = set()
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

    crossproduct: set[frozenset[NodeId]] = {frozenset().union(*selection) for selection in product(*configurations)}
    return simplify_conf(frozenset(crossproduct), container)


def conf_or(configurations: set[Configuration], container: IrContainer) -> Configuration:
    """Combine configurations using a disjunction."""

    logger.debug('OR of %s', configurations)

    conf_union = frozenset().union(*configurations)
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

    # TODO handle end of word
    # what to do with unknown bool results? or should those never occur?

    # TODO add memoization

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, FiniteAutomaton))
    node_repr: NodeId = container.merged_nodes.find(node_id)

    result_set: frozenset[frozenset[NodeId]]= frozenset()
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



    elif isinstance(node, AutCallEx): # noqa
        raise NotImplementedError
    elif isinstance(node, AutCallFirst): # noqa
        raise NotImplementedError
    elif isinstance(node, AutRepeat): # noqa
        raise NotImplementedError
    elif isinstance(node, AutRepeatUpTo): # noqa
        raise NotImplementedError
    elif isinstance(node, AutRefuted):
        raise NotImplementedError



    return result_set, acceptance_result



def evaluate_finite_automaton_conf(conf: Configuration,
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> tuple[Configuration, bool]:
    """Evaluate a configuration on a trace starting at FencepostPosition pos.
    Returns a representation of the new configuration after reading one symbol
    as a frozenset of frozensets (disjunction of conjunctions).
    Also returns whether the automaton accepts at the current position."""

    conjunction_conf_results: set[Configuration] = set()
    conjunction_acc_results: set[bool] = set()
    for conjunction in conf:
        result_pairs: set[tuple[Configuration, bool]] = {evaluate_finite_automaton_primitive(node_id, container, trace, pos) for node_id in conjunction}
        conf_results: set[Configuration] = {pair[0] for pair in result_pairs}
        acc_results: set[bool] = {pair[1] for pair in result_pairs}
        conjunction_conf_results.add(conf_and(conf_results, container))
        conjunction_acc_results.add(all(acc_results))
    disjunction_conf_result: Configuration = conf_or(conjunction_conf_results, container)
    disjunction_acc_result: bool = any(conjunction_acc_results)
    return (disjunction_conf_result, disjunction_acc_result)




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


    logger.debug('START of evaluation %s on trace %s at pos %s', node, trace, pos)

    acc_pos: list[FencepostPosition] = []

    next_conf: Configuration = frozenset([frozenset([node_repr])])
    next_pos: FencepostPosition = pos

    # TODO deal with infinite suffix

    while next_conf != EMPTY_CONF and next_pos != FencepostPosition('within_infinite_suffix'):
        assert isinstance(next_pos.value, tuple)

        logger.debug('Evaluate %s on trace %s at pos %s', node, trace, pos)
        logger.debug('CONFIGURATION: %s', next_conf)
        next_conf, acc_result = evaluate_finite_automaton_conf(next_conf, container, trace, next_pos)
        if acc_result:
            acc_pos.append(next_pos)
            logger.debug('Add pos %s to accepting positions', next_pos)
        next_pos = next_pos.next_pos(trace)

    return acc_pos




#------------------+
#  OMEGA AUTOMATA  |
#------------------+


def evaluate_omega_automaton(node_id: NodeId[OmegaAutomaton], container: IrContainer, trace: Trace) -> MaybeBool:
    raise NotImplementedError
