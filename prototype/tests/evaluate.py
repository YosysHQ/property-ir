from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering
from logging import getLogger
from typing import Literal

from ir.base import (
    Bool,
    IrContainer,
    NodeId,
    Property,
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
    Ite,
    Not,
    Or,
    RegGclk,
    RisingGclk,
    Xor,
)
from ir.primitives.simple_primitives import (
    PropAcceptOn,
    PropAnd,
    PropFalse,
    PropNexttime,
    PropNot,
    PropOr,
    PropOverlappedFollowedBy,
    PropOverlappedImplication,
    PropRefuted,
    PropRejectOn,
    PropStrong,
    PropStrongBool,
    PropStrongNexttime,
    PropStrongUntilWith,
    PropTrue,
    PropUntil,
    PropWeak,
    PropWeakBool,
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


type MaybeBool = bool | Literal['unknown', 'top', 'bot']

type BoolMemoDict = dict[tuple[NodeId, Trace, FencepostPosition], MaybeBool]
type SequenceMemoDict = dict[tuple[NodeId, Trace, FencepostPosition], frozenset[FencepostPosition]]
type PropertyMemoDict = dict[tuple[NodeId, Trace], MaybeBool]


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

    def remove_first_symbols(self, num: int) -> Trace:
        """Remove the first n symbols from the finite part of the Trace."""

        return Trace(self.finite_part[num:], self.suffix)

    def replace_from(self, pos: FencepostPosition, suffix: Literal['top_omega', 'bot_omega']) -> Trace:
        """Starting from the given FencepostPosition, replace the following
        symbols by either top_omega or bot_omega. If the position is the
        position marking the end of the finite part, the suffix is replaced.
        If the position is within_finite_suffix, the suffix will become a
        mixed top_star_bot_omega or bot_star_top_omega."""

        replace_within_suffix: bool = False
        if isinstance(pos.value, tuple):
            if pos.value[1] <= len(self.finite_part):
                return Trace(finite_part=self.finite_part[:pos.value[1]], suffix=suffix)
            else:
                replace_within_suffix = True

        if pos == FencepostPosition('within_infinite_suffix') or replace_within_suffix:
            if self.suffix in ['top_omega', 'end'] and suffix == 'top_omega':
                return Trace(finite_part=self.finite_part, suffix='top_omega')
            elif self.suffix in ['bot_omega', 'end'] and suffix == 'bot_omega':
                return Trace(finite_part=self.finite_part, suffix='bot_omega')
            elif self.suffix == 'top_omega' and suffix == 'bot_omega':
                return Trace(finite_part=self.finite_part, suffix='top_star_bot_omega')
            elif self.suffix == 'bot_omega' and suffix == 'top_omega':
                return Trace(finite_part=self.finite_part, suffix='bot_star_top_omega')
            elif self.suffix in ['bot_star_top_omega', 'top_star_bot_omega']:
                raise ValueError('Cannot replace suffix of trace %s within mixed suffix', self)

        if pos == FencepostPosition('unknown'):
            raise ValueError('Cannot replace suffix of trace %s at unknown position', self)

        raise ValueError('Cannot replace suffix of trace %s at %s', self, pos)



@dataclass(frozen=True)
@total_ordering
class FencepostPosition:
    """Fencepost position inside a Trace. When interpreted as a sequence match,
    the last fencepost position at the end of the finite part of a trace should
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

    def prev_pos(self) -> FencepostPosition:
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


def eval_and(values: set[MaybeBool]) -> MaybeBool:
    if False in values:
        return False
    elif 'unknown' in values:
        return 'unknown'
    elif 'bot' in values:
        return 'bot'
    elif 'top' in values:
        return 'top'
    return True

def eval_or(values: set[MaybeBool]) -> MaybeBool:
    if True in values:
        return True
    elif 'unknown' in values:
        return 'unknown'
    elif 'top' in values:
        return 'top'
    elif 'bot' in values:
        return 'bot'
    return False

def eval_not(value: MaybeBool) -> MaybeBool:
    if value in ['top', 'bot', 'unknown']:
        return value
    return not value

def eval_xor(value1: MaybeBool, value2: MaybeBool) -> MaybeBool:
    not1: MaybeBool = eval_not(value1)
    not2: MaybeBool = eval_not(value2)
    sub_result1 = eval_and({value1, not2})
    sub_result2 = eval_and({not1, value2})
    return eval_or({sub_result1, sub_result2})


def evaluate_bool(node_id: NodeId[Bool],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition,
    bool_results: BoolMemoDict) -> MaybeBool:
    """Evaluate a Bool type node starting at a specific fencepost position in
    some input trace. It is assumed that the Bool does not contain cycles."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, Bool))

    logger.debug('Evaluate bool %s on trace %s at position %s', node, trace, pos)

    # because we get the position where the evaluation starts
    # we are already in the infinite suffix at the last fencepost position
    if isinstance(pos.value, tuple):
        if pos.value[1] >= len(trace.finite_part):
            pos = FencepostPosition('within_infinite_suffix')

    if (node_id, trace, pos) in bool_results:
        logger.debug('Found result in bool_results')
        return bool_results[node_id, trace, pos]

    result: MaybeBool | None = None

    # special symbols

    if pos.value == 'within_infinite_suffix':
        match(trace.suffix):
            case('top_omega'):
                result = 'top'
            case('bot_omega' | 'bot_star_top_omega' | 'end'):
                result = 'bot'
            case('top_star_bot_omega'):
                result = 'unknown'
    elif pos.value == 'unknown':
        result = 'unknown'

    elif trace.finite_part[pos.value[1]] == 'top':
        result = 'top'
    elif trace.finite_part[pos.value[1]] == 'bot':
        result = 'bot'

    # evaluate primitives

    elif isinstance(node, Constant):
        result = node.value

    elif isinstance(node, Signal):
        result = node.signal_name in trace.finite_part[pos.value[1]]

    elif isinstance(node, Not):
        child_value: MaybeBool = evaluate_bool(node.child, container, trace, pos, bool_results)
        result = eval_not(child_value)

    elif isinstance(node, And):
        child_values: set[MaybeBool] = {evaluate_bool(child_id, container, trace, pos, bool_results) for child_id in node.children}
        result = eval_and(child_values)

    elif isinstance(node, Or):
        child_values: set[MaybeBool] = {evaluate_bool(child_id, container, trace, pos, bool_results) for child_id in node.children}
        result = eval_or(child_values)

    elif isinstance(node, Xor):
        value1: MaybeBool = evaluate_bool(node.child1, container, trace, pos, bool_results)
        value2: MaybeBool = evaluate_bool(node.child2, container, trace, pos, bool_results)
        result = eval_xor(value1, value2)

    elif isinstance(node, Eq):
        value1: MaybeBool = evaluate_bool(node.child1, container, trace, pos, bool_results)
        value2: MaybeBool = evaluate_bool(node.child2, container, trace, pos, bool_results)
        result = eval_not(eval_xor(value1, value2))

    elif isinstance(node, FutureGclk):
        result = evaluate_bool(node.child, container, trace, pos.next_pos(trace), bool_results)

    elif isinstance(node, (ChangingGclk, FallingGclk, RisingGclk)):
        clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos, bool_results)
        clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos, bool_results)
        next_clock_value: MaybeBool = evaluate_bool(node.child1, container, trace, pos.next_pos(trace), bool_results)
        next_clock_defined: MaybeBool = evaluate_bool(node.child2, container, trace, pos.next_pos(trace), bool_results)

        if isinstance(node, ChangingGclk):
            result = eval_or({eval_xor(clock_value, next_clock_value), eval_xor(clock_defined, next_clock_defined)})

        elif isinstance(node, FallingGclk):
            result = eval_and({
                eval_or({clock_value, eval_not(clock_defined)}),
                eval_and({eval_not(next_clock_value), next_clock_defined})})

        elif isinstance(node, RisingGclk):
            result = eval_and({
                eval_or({eval_not(clock_value), eval_not(clock_defined)}),
                eval_and({next_clock_value, next_clock_defined})
            })

    elif isinstance(node, Initial):
        result = pos.value[1] == 0

    elif isinstance(node, (Ite)):
        value1: MaybeBool = evaluate_bool(node.child1, container, trace, pos, bool_results)
        value2: MaybeBool = evaluate_bool(node.child2, container, trace, pos, bool_results)
        value3: MaybeBool = evaluate_bool(node.child3, container, trace, pos, bool_results)
        result = eval_or({
            eval_and({value1, value2}),
            eval_and({eval_not(value1), value3}),
        })

    elif isinstance(node, (RegGclk)):
        if pos == FencepostPosition(('at', 0)):
            result = evaluate_bool(node.child1, container, trace, pos, bool_results) # initial value
        else:
            result = evaluate_bool(node.child2, container, trace, pos.prev_pos(), bool_results) # set value


    if result is None:
        result = 'unknown'
    bool_results[node_id, trace, pos] = result
    return result




#--------------------+
#  SIMPLE SEQUENCES  |
#--------------------+



def sequence_matches_evaluate_primitive(node: Sequence,
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict) -> frozenset[FencepostPosition]:
    """Evaluate a Sequence type node on some input trace starting at a specific
    fencepost position. This function is called from sequence_matches as a
    separate function to facilitate memoization."""

    if isinstance(node, SeqNoMatch):
        return frozenset()

    elif isinstance(node, SeqBool):
        child_id: NodeId = node.child
        result: MaybeBool = evaluate_bool(child_id, container, trace, pos, bool_results)
        if result in [False, 'bot']:
            return frozenset([])
        if result in [True, 'top']:
            return frozenset([pos.next_pos(trace)])

    elif isinstance(node, SeqRepeat):
        start_positions: set[FencepostPosition] = {pos}
        result_positions = set()
        rng: Range = node.child1

        for _ in range(rng.lower_bound):
            next_start_positions = set()
            for start_pos in start_positions:
                next_start_positions = next_start_positions.union(
                    sequence_matches(node.child2, container, trace, start_pos, bool_results, seq_results))
            start_positions = next_start_positions
        result_positions = result_positions.union(start_positions)

        # this will terminate because we will reach the infinite suffix
        # because there are no empty matches
        if rng.upper_bound.value == '$':
            while True:
                next_start_positions = set()
                for start_pos in start_positions:
                    next_start_positions = next_start_positions.union(
                        sequence_matches(node.child2, container, trace, start_pos, bool_results, seq_results))
                if start_positions == next_start_positions:
                    return frozenset(result_positions)
                start_positions = next_start_positions
                result_positions = result_positions.union(start_positions)

        else:
            for _ in range(rng.upper_bound.value - rng.lower_bound):
                next_start_positions = set()
                for start_pos in start_positions:
                    next_start_positions = next_start_positions.union(
                        sequence_matches(node.child2, container, trace, start_pos, bool_results, seq_results))
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
                next_start_positions = next_start_positions.union(
                    sequence_matches(child_id, container, trace, start_pos, bool_results, seq_results))
            start_positions = next_start_positions
        return frozenset(start_positions)

    elif isinstance(node, SeqFusion):
        start_positions: set[FencepostPosition] = {pos}
        first_child: bool = True
        for child_id in node.children:
            if not first_child:
                start_positions = {start_pos.prev_pos() for start_pos in start_positions}
            first_child = False
            logger.debug('Start positions at seq-fusion child_id %s: %s', child_id, start_positions)
            next_start_positions = set()
            for start_pos in start_positions:
                next_start_positions = next_start_positions.union(
                    sequence_matches(child_id, container, trace, start_pos, bool_results, seq_results))
            start_positions = next_start_positions
        return frozenset(start_positions)

    elif isinstance(node, SeqOr):
        child_matches: set[FencepostPosition] = set()
        for child_id in node.children:
            child_matches = child_matches.union(
                sequence_matches(child_id, container, trace, pos, bool_results, seq_results))
        return frozenset(child_matches)

    elif isinstance(node, SeqIntersect):
        child_matches: set[FencepostPosition] = set()
        first_child: bool = True
        for child_id in node.children:
            if first_child:
                child_matches = set(sequence_matches(child_id, container, trace, pos, bool_results, seq_results))
            first_child = False
            child_matches = child_matches.intersection(
                sequence_matches(child_id, container, trace, pos, bool_results, seq_results))
        if FencepostPosition('within_infinite_suffix') in child_matches:
            child_matches.remove(FencepostPosition('within_infinite_suffix'))
            child_matches.add(FencepostPosition('unknown'))
        return frozenset(child_matches)

        # NOTE
        # intersection matches in the infinite suffix must happen at the same position
        # but we do not compute that information in the infinite suffix
        # this case is very rare, so add 'unknown' to the result

        # the treatment of 'unknown' could be improved by spliiting it into
        # ('unknown_at', position) and 'unknown_within_infinite_suffix'
        # but unknown results are very rare in any case

    # matches contain the earliest non-top match and all earlier top-matches
    # if the earliest match is in the infinite suffix, only within_infinite_suffix is returned
    # although there might be several matches in the infinite suffix
    # (because of the top-symbol, which also matches false, all possibilities for
    # where the first match could happen are considered)
    # if there is any match 'unknown', only 'unknown' will be returned
    elif isinstance(node, SeqFirstMatch):
        child_matches: set[FencepostPosition] = set(sequence_matches(node.child, container, trace, pos,
            bool_results, seq_results))
        if FencepostPosition('unknown') in child_matches:
            return frozenset([FencepostPosition('unknown')])
        bar_matches: set[FencepostPosition] = set(sequence_matches(node.child, container, trace.bar(), pos,
            bool_results, seq_results))
        result_matches: set[FencepostPosition] = set()
        for child_match in child_matches:
            smaller_bar_matches: set[FencepostPosition] = {match for match in bar_matches if match < child_match}
            if len(smaller_bar_matches) == 0:
                result_matches.add(child_match)
        return frozenset(result_matches)


    return frozenset([FencepostPosition('unknown')])




def sequence_matches(node_id: NodeId[Sequence],
    container: IrContainer,
    trace: Trace,
    pos: FencepostPosition,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict) -> frozenset[FencepostPosition]:
    """Evaluate a Sequence type node on some input trace starting at a specific
    fencepost position. The fencepost positions in the returned frozenset are
    the end points of the sequence matches, so they mark the end of the last
    matched symbol. It is assumed that the Sequence does not contain cycles."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, Sequence))

    logger.debug('Compute sequence matches of %s at %s', node, pos)

    if isinstance(pos.value, tuple):
        if pos.value[1] >= len(trace.finite_part):
            pos = FencepostPosition('within_infinite_suffix')

    if (node_id, trace, pos) in seq_results:
        logger.debug('Found result in seq_results')
        return seq_results[node_id, trace, pos]

    if pos == FencepostPosition('unknown'):
        return frozenset([FencepostPosition('unknown')])

    result = sequence_matches_evaluate_primitive(node, container, trace, pos, bool_results, seq_results)
    seq_results[node_id, trace, pos] = result
    return result





#--------------------+
#  SIMPLE PROPERTIES |
#--------------------+




def evaluate_accept_reject_on(node: PropertyIrNode,
    container: IrContainer,
    trace: Trace,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict,
    prop_results: PropertyMemoDict) -> tuple[MaybeBool, MaybeBool | None, MaybeBool | None]:
    """Evaluate a property on the necessary traces to determine the result of a
    prop-accept-on or prop-reject-on primitive. The resulting MaybeBool values,
    if they exist, are the results of the evaluation of the property on the input
    trace, on the trace with replaced suffix at the earliest position where the
    bool holds, and on the trace with a replaced suffix at an earlier unknown
    position."""

    if isinstance(node, PropAcceptOn):
        trace_for_bool: Trace = trace
        suffix: Literal['top_omega', 'bot_omega'] = 'top_omega'
    elif isinstance(node, PropRejectOn):
        trace_for_bool: Trace = trace.bar()
        suffix: Literal['top_omega', 'bot_omega'] = 'bot_omega'
    else:
        raise TypeError('Wrong node type in evaluate_accept_reject_on on node %s', node)

    p_result: MaybeBool = evaluate_property(node.child2, container, trace, bool_results, seq_results, prop_results)
    earliest_bool_result: MaybeBool | None = None
    unknown_bool_result: MaybeBool | None = None

    earliest_bool: int | None = None
    earliest_unknown: int | None = None
    for index in range(len(trace.finite_part) + 1):
        bool_result: MaybeBool = evaluate_bool(node.child1, container, trace_for_bool, FencepostPosition(('at', index)), bool_results)
        if bool_result == True:
            earliest_bool = index
            break
        elif bool_result == 'unknown' and earliest_unknown is None:
            earliest_unknown = index
    if earliest_bool is not None:
        earliest_bool_result = evaluate_property(node.child2, container,
            trace.replace_from(FencepostPosition(('at', earliest_bool)), suffix),
            bool_results, seq_results, prop_results)

    earlier_unknown = False
    if earliest_unknown is not None and earliest_bool is None:
        earlier_unknown = True
    elif earliest_unknown is not None and earliest_bool is not None:
        if earliest_unknown < earliest_bool:
            earlier_unknown = True
    if earlier_unknown:
        assert earliest_unknown is not None
        unknown_bool_result = evaluate_property(node.child2, container,
            trace.replace_from(FencepostPosition(('at', earliest_unknown)), suffix),
            bool_results, seq_results, prop_results)

    return (p_result, earliest_bool_result, unknown_bool_result)




def evaluate_strong(node: PropertyIrNode,
    container: IrContainer,
    trace: Trace,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict):
    """Evaluate the child sequence of the given node as though it is strong.
    This is used to implement PropStrong, PropWeak, and PropRefuted, where the
    trace gets modified before this method is called."""

    assert isinstance(node, (PropStrong, PropWeak, PropRefuted))

    if trace.suffix == 'end':
        trace = trace.replace_from(FencepostPosition('within_infinite_suffix'), 'bot_omega')

    child_matches: frozenset[FencepostPosition] = sequence_matches(node.child, container, trace, FencepostPosition(('at', 0)), bool_results, seq_results)
    logger.debug('child_matches with trace %s in evaluate_strong: %s', trace, child_matches)
    for match in child_matches:
        if isinstance(match.value, tuple) or (match.value == 'within_infinite_suffix' and trace.suffix in ['top_omega']):
            return True
    if FencepostPosition('unknown') in child_matches:
        return 'unknown'
    return False




def evaluate_property_primitive(node: PropertyIrNode,
    container: IrContainer,
    trace: Trace,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict,
    prop_results: PropertyMemoDict
    ) -> MaybeBool:
    """Evaluate a Property type node on some input trace. This function is called
    from evaluate_property as a separate function to facilitate memoization."""

    if isinstance(node, PropFalse):
        return False
    elif isinstance(node, PropTrue):
        return True

    elif isinstance(node, PropStrongBool):
        if len(trace.finite_part) == 0 and trace.suffix == 'end':
            return False
        bool_result: MaybeBool = evaluate_bool(node.child, container, trace, FencepostPosition(('at', 0)), bool_results)
        if bool_result in [True, 'top']:
            return True
        elif bool_result in [False, 'bot']:
            return False
        return 'unknown'

    elif isinstance(node, PropStrong):
        return evaluate_strong(node, container, trace, bool_results, seq_results)

    elif isinstance(node, PropWeakBool):

        if len(trace.finite_part) == 0:
            match(trace.suffix):
                case('end' | 'top_omega'):
                    return True
                case('bot_omega'):
                    return False
                case('bot_star_top_omega' | 'top_star_bot_omega'):
                    return 'unknown'

        modified_trace: Trace = trace.replace_from(FencepostPosition('within_infinite_suffix'), 'top_omega')

        bool_result: MaybeBool = evaluate_bool(node.child, container, modified_trace, FencepostPosition(('at', 0)), bool_results)
        if bool_result in [True, 'top']:
            return True
        elif bool_result in [False, 'bot']:
            return False
        return 'unknown'

    elif isinstance(node, PropWeak):
        modified_trace: Trace = trace.replace_from(FencepostPosition('within_infinite_suffix'), 'top_omega')
        return evaluate_strong(node, container, modified_trace, bool_results, seq_results)

    elif isinstance(node, PropNot):
        child_result = evaluate_property(node.child, container, trace.bar(), bool_results, seq_results, prop_results)
        if child_result == 'unknown':
            return 'unknown'
        return not child_result

    elif isinstance(node, PropAnd):
        unknown_seen: bool = False
        for child_id in node.children:
            child_value: MaybeBool = evaluate_property(child_id, container, trace, bool_results, seq_results, prop_results)
            if child_value == False:
                return False
            elif child_value == 'unknown':
                unknown_seen = True
        if unknown_seen:
            return 'unknown'
        return True

    elif isinstance(node, PropOr):
        unknown_seen: bool = False
        for child_id in node.children:
            child_value: MaybeBool = evaluate_property(child_id, container, trace, bool_results, seq_results, prop_results)
            if child_value == True:
                return True
            elif child_value == 'unknown':
                unknown_seen = True
        if unknown_seen:
            return 'unknown'
        return False

    elif isinstance(node, PropNexttime):
        shortened_trace: Trace = trace.remove_first_symbols(num=node.child1)
        if len(shortened_trace.finite_part) == 0 and shortened_trace.suffix == 'end':
            return True
        return evaluate_property(node.child2, container, shortened_trace, bool_results, seq_results, prop_results)

    elif isinstance(node, PropStrongNexttime):
        shortened_trace: Trace = trace.remove_first_symbols(num=node.child1)
        if len(shortened_trace.finite_part) == 0 and shortened_trace.suffix == 'end':
            return False
        return evaluate_property(node.child2, container, shortened_trace, bool_results, seq_results, prop_results)

    # TODO improve unknown result behavior
    elif isinstance(node, PropOverlappedImplication):
        all_bar_matches: frozenset[FencepostPosition] = sequence_matches(
            node.child1, container, trace.bar(), FencepostPosition(('at', 0)), bool_results, seq_results)
        logger.debug('PropOverlappedImplication all_bar_matches: %s', all_bar_matches)
        unknown_result: bool = False
        for match in all_bar_matches:
            if isinstance(match.value, tuple) or match.value == 'within_infinite_suffix':
                if isinstance(match.value, tuple):
                    result: MaybeBool = evaluate_property(node.child2, container, trace.remove_first_symbols(num=match.value[1]-1),
                        bool_results, seq_results, prop_results)
                else:
                    result: MaybeBool = evaluate_property(node.child2, container, trace.remove_first_symbols(num=len(trace.finite_part)),
                        bool_results, seq_results, prop_results)
                if result == 'unknown':
                    unknown_result = True
                elif result == False:
                    return False
            else:
                unknown_result = True
        if unknown_result:
            return 'unknown'
        return True

    elif isinstance(node, PropOverlappedFollowedBy):
        all_matches: frozenset[FencepostPosition] = sequence_matches(
            node.child1, container, trace, FencepostPosition(('at', 0)), bool_results, seq_results)
        logger.debug('PropOverlappedFollowedBy all_matches: %s', all_matches)
        unknown_result: bool = False
        for match in all_matches:
            if isinstance(match.value, tuple) or match.value == 'within_infinite_suffix':
                if isinstance(match.value, tuple):
                    result: MaybeBool = evaluate_property(
                        node.child2, container, trace.remove_first_symbols(num=match.value[1]-1),
                        bool_results, seq_results, prop_results)
                else:
                    result: MaybeBool = evaluate_property(
                        node.child2, container, trace.remove_first_symbols(num=len(trace.finite_part)),
                        bool_results, seq_results, prop_results)
                if result == 'unknown':
                    unknown_result = True
                elif result == True:
                    return True
            else:
                unknown_result = True
        if unknown_result:
            return 'unknown'
        return False

    elif isinstance(node, PropUntil):
        next_trace: Trace = trace
        p2_unknown: bool = False
        p1_unknown: bool = False
        for _ in range(len(trace.finite_part)+1):

            if len(next_trace.finite_part) == 0 and next_trace.suffix == 'end':
                break

            p1_result: MaybeBool = evaluate_property(node.child1, container, next_trace, bool_results, seq_results, prop_results)
            p2_result: MaybeBool = evaluate_property(node.child2, container, next_trace, bool_results, seq_results, prop_results)

            if p2_result == True and p1_unknown:
                return 'unknown'
            elif p2_result == True and not p1_unknown:
                return True
            elif p2_result == 'unknown':
                p2_unknown = True

            if p1_result == False and p2_unknown:
                return 'unknown'
            elif p1_result == False and not p2_unknown:
                return False
            elif p1_result == 'unknown':
                p1_unknown = True

            next_trace = next_trace.remove_first_symbols(num=1)

        if p1_unknown:
            return 'unknown'

        return True

    elif isinstance(node, PropStrongUntilWith):
        next_trace: Trace = trace
        p1_unknown: bool = False
        p1_p2_unknown: bool = False
        for _ in range(len(trace.finite_part)+1):

            if len(next_trace.finite_part) == 0 and next_trace.suffix == 'end':
                break

            p1_result: MaybeBool = evaluate_property(node.child1, container, next_trace, bool_results, seq_results, prop_results)
            p2_result: MaybeBool = evaluate_property(node.child2, container, next_trace, bool_results, seq_results, prop_results)

            if p1_result == True and p2_result == True:
                if p1_unknown:
                    return 'unknown'
                return True
            elif p1_result == False or p2_result == False:
                pass
            else:
                p1_p2_unknown = True

            if p1_result == False and p1_p2_unknown:
                return 'unknown'
            elif p1_result == False and not p1_p2_unknown:
                return False
            elif p1_result == 'unknown':
                p1_unknown = True

            next_trace = next_trace.remove_first_symbols(num=1)

        if p1_p2_unknown:
            return 'unknown'

        return False

    elif isinstance(node, PropAcceptOn):
        (p_result, earliest_bool_result, earliest_unknown) = evaluate_accept_reject_on(node, container, trace,
            bool_results, seq_results, prop_results)
        if p_result == True or earliest_bool_result == True:
            return True
        elif p_result == 'unknown' or earliest_bool_result == 'unknown' or earliest_unknown in [True, 'unknown']:
            return 'unknown'
        return False

    elif isinstance(node, PropRejectOn):
        (p_result, earliest_bool_result, earliest_unknown) = evaluate_accept_reject_on(node, container, trace,
            bool_results, seq_results, prop_results)
        if p_result == False or earliest_bool_result == False:
            return False
        elif p_result == 'unknown' or earliest_bool_result == 'unknown' or earliest_unknown in [False, 'unknown']:
            return 'unknown'
        return True


    elif isinstance(node, PropRefuted):
        # refuted is equivalent to not weak
        # apply bar (needed for not), then replace suffix by top_omega (to evaluate weak)

        modified_trace: Trace = trace.bar().replace_from(FencepostPosition('within_infinite_suffix'), 'top_omega')
        child_result =  evaluate_strong(node, container, modified_trace, bool_results, seq_results)

        if child_result == 'unknown':
            return 'unknown'
        return not child_result

    return 'unknown'


def evaluate_property(node_id: NodeId[Property],
    container: IrContainer,
    trace: Trace,
    bool_results: BoolMemoDict,
    seq_results: SequenceMemoDict,
    prop_results: PropertyMemoDict
    ) -> MaybeBool:
    """Evaluate a Property type node on some input trace. It is assumed that the
    input property is valid. This must be checked beforehand. Not checking it may
    result in an infinite loop if the property is recursive without progressing
    in time."""

    node: PropertyIrNode = container[node_id]
    assert(isinstance(node, Property))

    logger.debug('Evaluate property %s on trace %s', node, trace)

    if (node_id, trace) in prop_results:
        logger.debug('Found result in prop_results')
        return prop_results[node_id, trace]

    result = evaluate_property_primitive(node, container, trace, bool_results, seq_results, prop_results)
    prop_results[node_id, trace] = result
    return result
