from __future__ import annotations
from dataclasses import dataclass
from typeguard import typechecked

from .base import NodeId, Bool, Sequence, Property, Range, BoundedRange, ClockedProperty, ClockedSequence



# Bool primitives

@typechecked
@dataclass
class Constant(Bool): # "(constant false)" "(constant true)"
    value: bool

@typechecked
@dataclass
class Not(Bool):
    child: NodeId[Bool]

@typechecked
@dataclass
class And(Bool):
    children: list[NodeId[Bool]]

@typechecked
@dataclass
class Or(Bool):
    children: list[NodeId[Bool]]

@typechecked
@dataclass
class Xor(Bool):
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class Eq(Bool):
    child1: NodeId[Bool]
    child2: NodeId[Bool]


# Sequence primitives

@typechecked
@dataclass
class SeqBool(Sequence):
    child: NodeId[Bool]

@typechecked
@dataclass
class SeqRepeat(Sequence):
    child1: Range
    child2: NodeId[Sequence]

@typechecked
@dataclass
class SeqConcat(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqFusion(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqOr(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqIntersect(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqFirstMatch(Sequence):
    child: NodeId[Sequence]




# Property primitives

# non-derived primitives

@typechecked
@dataclass
class PropBool(Property):
    child: NodeId[Bool]

@typechecked
@dataclass
class PropSeq(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropStrong(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropWeak(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropNot(Property):
    child: NodeId[Property]

@typechecked
@dataclass
class PropAnd(Property):
    children: list[NodeId[Property]]

@typechecked
@dataclass
class PropOr(Property):
    children: list[NodeId[Property]]

@typechecked
@dataclass
class PropNexttime(Property):
    child1: int
    child2: NodeId[Property]

@typechecked
@dataclass
class PropOverlappedImplication(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropUntil(Property):
    child1: NodeId[Property]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropAcceptOn(Property):
    child1: NodeId[Bool]
    child2: NodeId[Property]

# derived but dual primitives (needed for NNF)

@typechecked
@dataclass
class PropStrongNexttime(Property):
    child1: int
    child2: NodeId[Property]

@typechecked
@dataclass
class PropOverlappedFollowedBy(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropRejectOn(Property):
    child1: NodeId[Bool]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropStrongUntilWith(Property):
    child1: NodeId[Property]
    child2: NodeId[Property]


# the following are probably not needed for simple properties

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropAlways(Property):
    child: NodeId[Property]

@typechecked
@dataclass
class PropAlwaysRanged(Property):
    child1: Range
    child2: NodeId[Property]





# Clocked Sequence primitives

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

@typechecked
@dataclass
class ClkPropSeq(ClockedProperty):
    child: NodeId[ClockedSequence]

@typechecked
@dataclass
class ClkPropBool(ClockedProperty):
    child: NodeId[Bool]

@typechecked
@dataclass
class ClkPropClocked(ClockedProperty):
    child: NodeId[ClockedProperty]

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
class ClkStrongEventually(ClockedProperty):
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