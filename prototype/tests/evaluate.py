from dataclasses import dataclass
from typing import Literal

from ir.base import (
    Bool,
    FiniteAutomaton,
    IrContainer,
    NodeId,
    OmegaAutomaton,
    PropertyIrNode,
    Sequence,
    Signal,
)
from ir.primitives.bool_primitives import (
    And,
    ChangingGclk,
    Constant,
    Eq,
    FallingGclk,
    FutureGclk,
    Initial,
    Or,
    RisingGclk,
    Xor,
)

type MaybeBool = bool | Literal['unknown']

type SequenceMatchEnd = tuple[Literal['at'], int] | Literal['within_infinite_suffix', 'unknown']

@dataclass(frozen=True)
class Trace:
    """Trace consisting of a finite prefix and possibly an infinite suffix of
    top/bottom symbols. The finite prefix consists for each time step of a set
    of signal names that are true in that time step. It may also contain top and
    bottom symbols."""

    finite_part: tuple[frozenset[str] | Literal['top', 'bot'], ...]
    suffix: Literal['end', 'top_omega', 'bot_omega', 'bot_star_top_omega', 'top_star_bot_omega']



#---------+
#  BOOL   |
#---------+


def evaluate_bool(node_id: NodeId[Bool], container: IrContainer, trace: Trace, pos: int) -> MaybeBool:
    """Evaluate a Bool type node on some input trace. It is assumed that the
    Bool does not contain cycles."""

    node: PropertyIrNode = container[node_id]

    if pos >= len(trace.finite_part):
        match(trace.suffix):
            case('end' | 'bot_star_top_omega' | 'top_star_bot_omega'):
                return 'unknown'
            case('top_omega'):
                return True
            case('bot_omega'):
                return False

    if isinstance(node, Constant):
            return node.value

    if isinstance(node, Signal):
        return node.signal_name in trace.finite_part[pos]

    elif isinstance(node, And):
        unknown_seen: bool = False
        for child_id in node.children:
            child_value: MaybeBool = evaluate_bool(child_id, container, trace, pos)
            if child_value == False:
                return False
            elif child_value == 'unknown':
                unknown_seen = True
        if unknown_seen:
            return 'unknown'
        return True

    elif isinstance(node, Or):
        unknown_seen: bool = False
        for child_id in node.children:
            child_value: MaybeBool = evaluate_bool(child_id, container, trace, pos)
            if child_value == True:
                return True
            elif child_value == 'unknown':
                unknown_seen = True
        if unknown_seen:
            return 'unknown'
        return False

    elif isinstance(node, (Xor, Eq)):
        clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos)
        clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos)
        if clock_value == 'unknown' or clock_defined == 'unknown':
            return 'unknown'

        if isinstance(node, Xor):
            return (clock_value and not clock_defined) or (not clock_value and clock_defined)

        elif isinstance(node, Eq):
            return clock_value == clock_defined

    if isinstance(node, FutureGclk):
        return evaluate_bool(node.child, container, trace, pos+1)

    elif isinstance(node, (ChangingGclk, FallingGclk, RisingGclk)):
        clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos) # clock value
        clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos) # clock defined
        next_clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos+1)
        next_clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos+1)
        if 'unknown' in { clock_value, clock_defined, next_clock_value, next_clock_defined }:
            return 'unknown'

        if isinstance(node, ChangingGclk):
            return clock_value != next_clock_value or clock_defined != next_clock_defined

        elif isinstance(node, FallingGclk):
            return (clock_value or not clock_defined) and (not next_clock_value and next_clock_defined)

        elif isinstance(node, RisingGclk):
            return (not clock_value or not clock_defined) and (next_clock_value and next_clock_defined)

    elif isinstance(node, Initial):
        return pos == 0

    # TODO add reg and ite?
    # TODO memoization

    return 'unknown'



#--------------------+
#  SIMPLE PROPERTIES |
#--------------------+


def sequence_matches(node_id: NodeId[Sequence], container: IrContainer, trace: Trace) -> frozenset[SequenceMatchEnd]:

    return frozenset(['unknown'])


def evaluate_property(node_id: NodeId[Bool], container: IrContainer, trace: Trace) -> MaybeBool:

    return 'unknown'







#------------+
#  AUTOMATA  |
#------------+


def evaluate_finite_automaton(node_id: NodeId[FiniteAutomaton], container: IrContainer, trace: Trace) -> frozenset[SequenceMatchEnd]:
    return frozenset(['unknown'])





def evaluate_omega_automaton(node_id: NodeId[OmegaAutomaton], container: IrContainer, trace: Trace) -> frozenset[SequenceMatchEnd]:
    return frozenset(['unknown'])
