from __future__ import annotations

from dataclasses import dataclass

from typeguard import typechecked

from ir.base import (
    Bool,
    BoundedRange,
    ClockedProperty,
    ClockedSequence,
    NodeId,
    Property,
    Range,
    Sequence,
)



# Clocked Sequence primitives

# this primitive is a clocked sequence with no matches, not even the top symbol is matched
# shorthand for intersection of conflictings sequence lengths
# used for empty sequence match removal
@typechecked
@dataclass
class ClkSeqNoMatch(ClockedSequence):
    pass

@typechecked
@dataclass
class ClkSeqBool(ClockedSequence):
    child: NodeId[Bool]

@typechecked
@dataclass
class ClkSeqSeq(ClockedSequence):
    child: NodeId[Sequence]

@typechecked
@dataclass
class ClkSeqClocked(ClockedSequence):
    child1: NodeId[Bool]
    child2: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkSeqRepeat(ClockedSequence):
    child1: Range
    child2: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkSeqDelay(ClockedSequence):
    child1: Range
    child2: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkSeqConcat(ClockedSequence):
    children: list[NodeId[ClockedSequence]]

@typechecked
@dataclass
class ClkSeqFusion(ClockedSequence):
    children: list[NodeId[ClockedSequence]]

@typechecked
@dataclass
class ClkSeqGotoRepeat(ClockedSequence):
    child1: Range
    child2: NodeId[Bool]

@typechecked
@dataclass
class ClkSeqNonconsecutiveRepeat(ClockedSequence):
    child1: Range
    child2: NodeId[Bool]

@typechecked
@dataclass
class ClkSeqOr(ClockedSequence):
    children: list[NodeId[ClockedSequence]]

@typechecked
@dataclass
class ClkSeqIntersect(ClockedSequence):
    children: list[NodeId[ClockedSequence]]

@typechecked
@dataclass
class ClkSeqAnd(ClockedSequence):
    children: list[NodeId[ClockedSequence]]

@typechecked
@dataclass
class ClkSeqFirstMatch(ClockedSequence):
    child: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkSeqThroughout(ClockedSequence):
    child1: NodeId[Bool]
    child2: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkSeqWithin(ClockedSequence):
    child1: NodeId[ClockedSequence]
    child2: NodeId[ClockedSequence]


# Clocked Property primitives

# this property will become a false-sink in the automaton representation
# used as a default RHS for overlapped implication/followed-by where the LHS is a no-match sequence
@typechecked
@dataclass
class ClkPropFalse(ClockedProperty):
    pass

# this property will become a true-sink in the automaton representation
# used as a default RHS for overlapped implication/followed-by where the LHS is a no-match sequence
@typechecked
@dataclass
class ClkPropTrue(ClockedProperty):
    pass

@typechecked
@dataclass
class ClkPropClkSeq(ClockedProperty):
    child: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkPropBool(ClockedProperty):
    child: NodeId[Bool]

@typechecked
@dataclass
class ClkPropWeakBool(ClockedProperty):
    child: NodeId[Bool]

@typechecked
@dataclass
class ClkPropStrongBool(ClockedProperty):
    child: NodeId[Bool]

@typechecked
@dataclass
class ClkPropClocked(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropProp(ClockedProperty):
    child: NodeId[Property]




@typechecked
@dataclass
class ClkPropStrong(ClockedProperty):
    child: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkPropWeak(ClockedProperty):
    child: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkPropNot(ClockedProperty):
    child: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropAnd(ClockedProperty):
    children: list[NodeId[ClockedProperty]]

@typechecked
@dataclass
class ClkPropOr(ClockedProperty):
    children: list[NodeId[ClockedProperty]]

@typechecked
@dataclass
class ClkPropImplies(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropIff(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropIf(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropIfElse(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]
    child3: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropNexttime(ClockedProperty):
    child1: int
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongNexttime(ClockedProperty):
    child1: int
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropOverlappedImplication(ClockedProperty):
    child1: NodeId[ClockedSequence]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropNonOverlappedImplication(ClockedProperty):
    child1: NodeId[ClockedSequence]
    child2: NodeId[ClockedProperty]



@typechecked
@dataclass
class ClkPropOverlappedFollowedBy(ClockedProperty):
    child1: NodeId[ClockedSequence]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropNonOverlappedFollowedBy(ClockedProperty):
    child1: NodeId[ClockedSequence]
    child2: NodeId[ClockedProperty]


@typechecked
@dataclass
class ClkPropUntil(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropUntilWith(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongUntil(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongUntilWith(ClockedProperty):
    child1: NodeId[ClockedProperty]
    child2: NodeId[ClockedProperty]



@typechecked
@dataclass
class ClkPropAlways(ClockedProperty):
    child: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropAlwaysRanged(ClockedProperty):
    child1: Range
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongAlways(ClockedProperty):
    child1: BoundedRange
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropEventually(ClockedProperty):
    child1: BoundedRange
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongEventually(ClockedProperty):
    child: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropStrongEventuallyRanged(ClockedProperty):
    child1: Range
    child2: NodeId[ClockedProperty]


@typechecked
@dataclass
class ClkPropAcceptOn(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropRejectOn(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropSyncAcceptOn(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]

@typechecked
@dataclass
class ClkPropSyncRejectOn(ClockedProperty):
    child1: NodeId[Bool]
    child2: NodeId[ClockedProperty]
