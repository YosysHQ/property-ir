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

type Configuration = frozenset[frozenset[NodeId]]


#------------------+
#  FINITE AUTOMATA |
#------------------+



def simplify_state_set(configuration: Configuration) -> Configuration:
    """For evaluating alternating automata, the configuration is a frozenset of
    frozensets (disjunction of conjunctions). To keep this representation small,
    remove conjunctions that are a superset of other conjunctions, and check
    whether true/false-sinks are contained in a frozenset to simplify it."""

    # TODO

    # conjunction with False -> False
    # conjunction with True -> remove True
    # disjunction with False -> remove False
    # disjunction with True -> True

    # empty conjunction -> True
    # empty disjunction -> False

    raise NotImplementedError


def state_set_and(configurations: list[Configuration]) -> Configuration:
    """Combine two configurations using a conjunction."""

    # TODO
    if len(configurations) != 1:
        raise NotImplementedError
    return configurations[0]

def state_set_or(configurations: list[Configuration]) -> Configuration:
    """Combine two configurations using a disjunction."""

    # TODO
    if len(configurations) != 1:
        raise NotImplementedError
    return configurations[0]


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

    result_set: frozenset[frozenset[NodeId]]= frozenset()
    acceptance_result: bool = False

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, FiniteAutomaton))

    if isinstance(node, AutTrue): # stay in this state - accepting
        result_set = frozenset([frozenset([node_id])])
        acceptance_result: bool = True

    elif isinstance(node, AutFalse): # stay in this state - not accepting
        result_set = frozenset([frozenset([node_id])])

    elif isinstance(node, AutConsume):
        bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})
        if bool_result == 'top':
            result_set = frozenset([frozenset([node.child2]), frozenset([node.child3])])
        elif bool_result == 'bot':
            result_set = frozenset()
        elif bool_result == True:
            result_set = frozenset([frozenset([node.child2])])
        elif bool_result == False:
            result_set = frozenset([frozenset([node.child3])])
        else:
            raise ValueError('Encountered unknown bool result in AutConsume evaluation with trace %s at position %s', trace, pos)

    elif isinstance(node, AutRead):
        bool_result: MaybeBool = evaluate_bool(node.child1, container, trace, pos, {})
        if bool_result == 'top':
            result_set1, acc1 = evaluate_finite_automaton_primitive(node.child2, container, trace, pos)
            result_set2, acc2 = evaluate_finite_automaton_primitive(node.child3, container, trace, pos)
            result_set = state_set_or([result_set1, result_set2])
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


    elif isinstance(node, AutOr): # noqa
        raise NotImplementedError

    elif isinstance(node, AutAnd): # noqa
        raise NotImplementedError



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



def evaluate_finite_automaton(node_id: NodeId[FiniteAutomaton],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition) -> frozenset[FencepostPosition]:
    """Evaluate a single FiniteAutomaton node on a trace starting at
    FencepostPosition pos. Returns a frozenset of FencepostPositions
    where the automaton accepts."""


    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, FiniteAutomaton))


    return frozenset([FencepostPosition('unknown')])




#------------------+
#  OMEGA AUTOMATA  |
#------------------+


def evaluate_omega_automaton(node_id: NodeId[OmegaAutomaton], container: IrContainer, trace: Trace) -> frozenset[FencepostPosition]:
    raise NotImplementedError
