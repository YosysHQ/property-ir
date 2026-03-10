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




# Sequence primitives

@typechecked
@dataclass
class SeqConcat(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqBool(Sequence):
    child: Bool

@typechecked
@dataclass
class SeqRepeat(Sequence):
    child1: Range
    child2: NodeId[Sequence]



# Property primitives

@typechecked
@dataclass
class PropBool(Property):
    child: NodeId[Bool]

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

@typechecked
@dataclass
class PropSeq(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]

@typechecked
@dataclass
class PropOverlappedImplication(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]


