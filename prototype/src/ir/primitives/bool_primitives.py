
from __future__ import annotations

from dataclasses import dataclass

from typeguard import typechecked

from ir.base import (
    Bool,
    NodeId,
)


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

@typechecked
@dataclass
class FutureGclk(Bool):
    child: NodeId[Bool]

@typechecked
@dataclass
class ChangingGclk(Bool):
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class FallingGclk(Bool):
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class RisingGclk(Bool):
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class Initial(Bool):
    pass
