from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from logging import getLogger
from typing import Literal

from ir.base import (
    Bool,
    FiniteAutomaton,
    IrContainer,
    NodeId,
    OmegaAutomaton,
    PropertyIrNode,
    Range,
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
    Not,
    Or,
    RisingGclk,
    Xor,
)
from ir.primitives.simple_primitives import (
    SeqBool,
    SeqConcat,
    SeqFirstMatch,
    SeqFusion,
    SeqIntersect,
    SeqNoMatch,
    SeqOr,
    SeqRepeat,
)

logger = getLogger(__name__)


type MaybeBool = bool | Literal['unknown']


@dataclass(frozen=True)
class Trace:
    """Trace consisting of a finite prefix and possibly an infinite suffix of
    top/bottom symbols. The finite prefix consists for each time step of a set
    of signal names that are true in that time step. It may also contain top and
    bottom symbols."""

    finite_part: tuple[frozenset[str] | Literal['top', 'bot'], ...]
    suffix: Literal['end', 'top_omega', 'bot_omega', 'bot_star_top_omega', 'top_star_bot_omega']

    def symbol_at_pos(self, pos: FencepostPosition) -> frozenset[str] | Literal['top', 'bot', 'unknown']:
        if pos.value == 'unknown':
            return 'unknown'
        if isinstance(pos.value, tuple):
            if pos.value[1] < len(self.finite_part):
                return self.finite_part[pos.value[1]]
        if self.suffix in ['end', 'bot_star_top_omega', 'top_star_bot_omega']:
            return 'unknown'
        elif self.suffix == 'top_omega':
            return 'top'
        elif self.suffix == 'bot_omega':
            return 'bot'
        return 'unknown'

    @classmethod
    def symbol_bar(cls, symbol: frozenset[str] | Literal['top', 'bot']) -> frozenset[str] | Literal['top', 'bot']:
        """Applies the bar operator to a single symbol, exchanging top and bottom
        symbols and leaving all other symbols untouched."""

        if symbol == 'top':
            return 'bot'
        elif symbol == 'bot':
            return 'top'
        else:
            return symbol

    def bar(self) -> Trace:
        """Applies the bar operator to the trace, exchanging all top and bottom
        symbols and leaving all other symbols untouched."""

        finite_part_bar: tuple[frozenset[str] | Literal['top', 'bot'], ...] = tuple([Trace.symbol_bar(symbol) for symbol in self.finite_part])

        suffix_bar: Literal['end', 'top_omega', 'bot_omega', 'bot_star_top_omega', 'top_star_bot_omega']

        match(self.suffix):
            case('end'):
                suffix_bar = 'end'
            case('top_omega'):
                suffix_bar = 'bot_omega'
            case('bot_omega'):
                suffix_bar = 'top_omega'
            case('bot_star_top_omega'):
                suffix_bar = 'top_star_bot_omega'
            case('top_star_bot_omega'):
                suffix_bar = 'bot_star_top_omega'

        return Trace(finite_part_bar, suffix_bar)



@dataclass(frozen=True)
@total_ordering
class FencepostPosition:
    """Fencepost position inside a Trace.
    The last fencepost position at the end of the finite part of a trace should
    be represented as ('at', pos) and NOT as 'within_infinite_suffix'."""

    value: tuple[Literal['at'], int] | Literal['within_infinite_suffix', 'unknown']

    def next_pos(self, trace: Trace) -> FencepostPosition:
        if self.value == 'within_infinite_suffix' or self.value == 'unknown':
            return self
        else:
            if self.value[1] >= len(trace.finite_part):
                return FencepostPosition('within_infinite_suffix')
            else:
                return FencepostPosition(('at', self.value[1]+1))

    def prev_pos(self, trace: Trace) -> FencepostPosition:
        if self.value == 'within_infinite_suffix' or self.value == 'unknown':
            return self
        else:
            if self.value[1] == 0:
                return FencepostPosition('unknown')
            else:
                return FencepostPosition(('at', self.value[1]-1))

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        """Treat within_infinite_suffix as the highest value, and unknown as the
        lowest."""

        # NOTE
        # Should unknown be treated differently?
        # It could be assumed that it only happens in a mixed infinite suffix
        # if all primitives are implemented

        if self.value == 'unknown':
            return True
        if self.value == 'within_infinite_suffix':
            return False
        if isinstance(self.value, tuple) and isinstance(other.value, tuple):
            return self.value[1] < other.value[1]
        if isinstance(self.value, tuple) and other.value == 'within_infinite_suffix':
            return True
        if isinstance(self.value, tuple) and other.value == 'unknown':
            return False


#---------+
#  BOOL   |
#---------+


def evaluate_bool(node_id: NodeId[Bool], container: IrContainer, trace: Trace, pos: FencepostPosition) -> MaybeBool:
    """Evaluate a Bool type node starting at a specific fencepost position in
    some input trace. It is assumed that the Bool does not contain cycles."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, Bool))

    # because we get the position where the evaluation starts
    # we are already in the infinite suffix at the last fencepost position
    if isinstance(pos.value, tuple):
        if pos.value[1] >= len(trace.finite_part):
            pos = FencepostPosition('within_infinite_suffix')

    if pos.value == 'within_infinite_suffix':
        match(trace.suffix):
            case('end' | 'bot_star_top_omega' | 'top_star_bot_omega'):
                return 'unknown'
            case('top_omega'):
                return True
            case('bot_omega'):
                return False
    elif pos.value == 'unknown':
        return 'unknown'

    if trace.finite_part[pos.value[1]] == 'top':
        return True
    elif trace.finite_part[pos.value[1]] == 'bot':
        return False


    if isinstance(node, Constant):
            return node.value

    if isinstance(node, Signal):
        return node.signal_name in trace.finite_part[pos.value[1]]

    if isinstance(node, Not):
        child_value: MaybeBool = evaluate_bool(node.child, container, trace, pos)
        if child_value == 'unknown':
            return 'unknown'
        return not child_value

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
        child_value1: MaybeBool = evaluate_bool(node.child1, container, trace, pos)
        child_value2: MaybeBool = evaluate_bool(node.child2, container, trace, pos)
        if child_value1 == 'unknown' or child_value2 == 'unknown':
            return 'unknown'

        if isinstance(node, Xor):
            return (child_value1 and not child_value2) or (not child_value1 and child_value2)

        elif isinstance(node, Eq):
            return child_value1 == child_value2

    # TODO add MaybeBool elements 'any' and 'none' to handle 'bot' and 'top'
    if isinstance(node, FutureGclk):
        if trace.symbol_at_pos(pos.next_pos(trace)) in ['bot', 'top']:
            return 'unknown'
        return evaluate_bool(node.child, container, trace, pos.next_pos(trace))

    elif isinstance(node, (ChangingGclk, FallingGclk, RisingGclk)):
        clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos)
        clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos)
        next_clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos.next_pos(trace))
        next_clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos.next_pos(trace))
        if 'unknown' in { clock_value, clock_defined, next_clock_value, next_clock_defined }:
            return 'unknown'
        if trace.symbol_at_pos(pos.next_pos(trace)) in ['bot', 'top']:
            return 'unknown'

        if isinstance(node, ChangingGclk):
            return clock_value != next_clock_value or clock_defined != next_clock_defined

        elif isinstance(node, FallingGclk):
            return (clock_value or not clock_defined) and (not next_clock_value and next_clock_defined)

        elif isinstance(node, RisingGclk):
            return (not clock_value or not clock_defined) and (next_clock_value and next_clock_defined)

    elif isinstance(node, Initial):
        return pos.value[1] == 0

    # TODO add reg and ite?
    # TODO memoization

    return 'unknown'



#--------------------+
#  SIMPLE PROPERTIES |
#--------------------+


def sequence_matches(node_id: NodeId[Sequence], container: IrContainer, trace: Trace, pos: FencepostPosition) -> frozenset[FencepostPosition]:
    """Evaluate a Sequence type node on some input trace starting at a specific
    fencepost position. The fencepost positions in the returned frozenset are
    the end points of the sequence matches, so they mark the end of the last
    matched symbol. It is assumed that the Sequence does not contain cycles."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, Sequence))

    logger.debug('Compute sequence matches of %s at %s', node, pos)

    if isinstance(node, SeqNoMatch):
        return frozenset()

    elif isinstance(node, SeqBool):
        child_id: NodeId = node.child
        result: MaybeBool = evaluate_bool(child_id, container, trace, pos)
        if result == False:
            return frozenset([])
        if result == True:
            return frozenset([pos.next_pos(trace)])

    elif isinstance(node, SeqRepeat):
        start_positions: set[FencepostPosition] = {pos}
        result_positions = set()
        rng: Range = node.child1

        for _ in range(rng.lower_bound):
            next_start_positions = set()
            for start_pos in start_positions:
                next_start_positions = next_start_positions.union(sequence_matches(node.child2, container, trace, start_pos))
            start_positions = next_start_positions
        result_positions = result_positions.union(start_positions)

        # this will terminate because we will reach the infinite suffix
        # because there are no empty matches
        if rng.upper_bound.value == '$':
            while True:
                next_start_positions = set()
                for start_pos in start_positions:
                    next_start_positions = next_start_positions.union(sequence_matches(node.child2, container, trace, start_pos))
                if start_positions == next_start_positions:
                    return frozenset(result_positions)
                start_positions = next_start_positions
                result_positions = result_positions.union(start_positions)

        else:
            for _ in range(rng.upper_bound.value - rng.lower_bound):
                next_start_positions = set()
                for start_pos in start_positions:
                    next_start_positions = next_start_positions.union(sequence_matches(node.child2, container, trace, start_pos))
                start_positions = next_start_positions
                result_positions = result_positions.union(start_positions)
                if start_positions == next_start_positions:
                    return frozenset(result_positions)

        return frozenset(result_positions)

    elif isinstance(node, SeqConcat):
        logger.debug('Compute sequence matches of seq-concat %s', node)
        start_positions: set[FencepostPosition] = {pos}
        for child_id in node.children:
            next_start_positions = set()
            for start_pos in start_positions:
                next_start_positions = next_start_positions.union(sequence_matches(child_id, container, trace, start_pos))
            start_positions = next_start_positions
        return frozenset(start_positions)

    elif isinstance(node, SeqFusion):
        start_positions: set[FencepostPosition] = {pos}
        first_child: bool = True
        for child_id in node.children:
            if not first_child:
                start_positions = {start_pos.prev_pos(trace) for start_pos in start_positions}
            first_child = False
            logger.debug('Start positions at seq-fusion child_id %s: %s', child_id, start_positions)
            next_start_positions = set()
            for start_pos in start_positions:
                next_start_positions = next_start_positions.union(sequence_matches(child_id, container, trace, start_pos))
            start_positions = next_start_positions
        return frozenset(start_positions)

    elif isinstance(node, SeqOr):
        child_matches: set[FencepostPosition] = set()
        for child_id in node.children:
            child_matches = child_matches.union(sequence_matches(child_id, container, trace, pos))
        return frozenset(child_matches)

    elif isinstance(node, SeqIntersect):
        child_matches: set[FencepostPosition] = set()
        first_child: bool = True
        for child_id in node.children:
            if first_child:
                child_matches = set(sequence_matches(child_id, container, trace, pos))
            first_child = False
            child_matches = child_matches.intersection(sequence_matches(child_id, container, trace, pos))
        if FencepostPosition('within_infinite_suffix') in child_matches:
            child_matches.remove(FencepostPosition('within_infinite_suffix'))
            child_matches.add(FencepostPosition('unknown'))
        return frozenset(child_matches)

        # TODO what about matches in the infinite suffix?
        # they must happen at the same position, but that information is not
        # available

    # matches contain the earliest non-top match and all earlier top-matches
    # if the earliest match is in the infinite suffix, only within_infinite_suffix is returned
    # although there might be several matches in the infinite suffix
    # (because of the top-symbol, which also matches false, all possibilities for
    # where the first match could happen are considered)
    # if there is any match 'unknown', only 'unknown' will be returned
    elif isinstance(node, SeqFirstMatch):
        logger.debug('trace %s', trace)
        logger.debug('trace.bar() %s', trace.bar())
        child_matches: set[FencepostPosition] = set(sequence_matches(node.child, container, trace, pos))
        if FencepostPosition('unknown') in child_matches:
            return frozenset([FencepostPosition('unknown')])
        logger.debug('seq-first-match child_matches: %s', child_matches)
        bar_matches: set[FencepostPosition] = set(sequence_matches(node.child, container, trace.bar(), pos))
        logger.debug('seq-first-match bar_matches: %s', bar_matches)
        result_matches: set[FencepostPosition] = set()
        for child_match in child_matches:
            smaller_bar_matches: set[FencepostPosition] = {match for match in bar_matches if match < child_match}
            if len(smaller_bar_matches) == 0:
                result_matches.add(child_match)
        return frozenset(result_matches)



    # SeqRefuted? Or instead allow PropNot in the input?

    return frozenset([FencepostPosition('unknown')])


def evaluate_property(node_id: NodeId[Bool], container: IrContainer, trace: Trace) -> MaybeBool:

    return 'unknown'







#------------+
#  AUTOMATA  |
#------------+


def evaluate_finite_automaton(node_id: NodeId[FiniteAutomaton], container: IrContainer, trace: Trace) -> frozenset[FencepostPosition]:
    return frozenset([FencepostPosition('unknown')])





def evaluate_omega_automaton(node_id: NodeId[OmegaAutomaton], container: IrContainer, trace: Trace) -> frozenset[FencepostPosition]:
    return frozenset([FencepostPosition('unknown')])
