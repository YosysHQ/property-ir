from __future__ import annotations

from dataclasses import dataclass

from typeguard import typechecked

from ir.base import (
    Bool,
    NodeId,
    Property,
    Range,
    Sequence,
)


# Sequence primitives

# this primitive is a sequence with no matches, not even the top symbol is matched
# shorthand for intersection of conflictings sequence lengths
# used for empty sequence match removal
@typechecked
@dataclass
class SeqNoMatch(Sequence):
    pass

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

# this property will become a false-sink in the automaton representation
# used as a default RHS for overlapped implication/followed-by where the LHS is a no-match sequence
@typechecked
@dataclass
class PropFalse(Property):
    pass

# this property will become a true-sink in the automaton representation
# used as a default RHS for overlapped implication/followed-by where the LHS is a no-match sequence
@typechecked
@dataclass
class PropTrue(Property):
    pass

@typechecked
@dataclass
class PropWeakBool(Property):
    child: NodeId[Bool]

@typechecked
@dataclass
class PropStrongBool(Property):
    child: NodeId[Bool]

@typechecked
@dataclass
class PropStrong(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropWeak(Property):
    child: NodeId[Sequence]

# the primitive PropRefuted is equivalent to not(weak(seq))
# it means that there is evidence that the sequence cannot match, regardless of how it is extended
# it is a strong primitive because we need to observe that it provably fails on a finite prefix
# used for negation normal form (NNF)
@typechecked
@dataclass
class PropRefuted(Property):
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


## the following are probably not needed for simple properties
#
#@typechecked
#@dataclass
#class PropNonOverlappedImplication(Property):
#    child1: NodeId[Sequence]
#    child2: NodeId[Property]
#
#@typechecked
#@dataclass
#class PropAlways(Property):
#    child: NodeId[Property]
#
#@typechecked
#@dataclass
#class PropAlwaysRanged(Property):
#    child1: Range
#    child2: NodeId[Property]
