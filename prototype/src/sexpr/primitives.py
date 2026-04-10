from __future__ import annotations
from dataclasses import dataclass
from typeguard import typechecked

from .base import NodeId, Bool, Sequence, Property, Range



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

@typechecked
@dataclass
class PropAnd(Property):
    children: list[NodeId[Property]]