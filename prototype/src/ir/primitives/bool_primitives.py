
from __future__ import annotations

from dataclasses import dataclass

from typeguard import typechecked

from ir.base import Bool, NodeId

# Bool primitives

@typechecked
@dataclass
class Constant(Bool):
    """Constant high (1'b1) or low (1'b0) value. Written as (constant true) and
    (constant false), or abbreviated as (true) and (false)."""
    value: bool

@typechecked
@dataclass
class Not(Bool):
    """Logical not primitive (!)."""
    child: NodeId[Bool]

@typechecked
@dataclass
class And(Bool):
    """Logical and primitive (&&)."""
    children: list[NodeId[Bool]]

@typechecked
@dataclass
class Or(Bool):
    """Logical or primitive (||)."""
    children: list[NodeId[Bool]]

@typechecked
@dataclass
class Xor(Bool):
    """Logical inequality primitive (!=)."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class Eq(Bool):
    """Logical equality primitive (==)."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class FutureGclk(Bool):
    """The value of the input signal in the next global time step."""
    child: NodeId[Bool]

@typechecked
@dataclass
class ChangingGclk(Bool):
    """Evaluates to true iff the input signal (child1) or the clock defined value
    (child2) differ in the current and in the next global time step."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class FallingGclk(Bool):
    """Evaluates to true iff the input signal (child1) is true or undefined in the
    current time step and is defined and false in the next global time step."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class RisingGclk(Bool):
    """Evaluates to true iff the input signal (child1) is false or undefined in the
    current time step and is defined and true in the next global time step."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]

@typechecked
@dataclass
class Initial(Bool):
    """True in the first time step, else false. Yosys-specific operation."""

@typechecked
@dataclass
class Ite(Bool):
    """If the condition (child1) evaluates to true, the result is the value of
    child2, else the result is the value of child3."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]
    child3: NodeId[Bool]

@typechecked
@dataclass
class Reg(Bool):
    """In the first global time step, is has the initial value (child1),
    and in every other global time step, it has the value of child2 in the
    previous global time step."""
    child1: NodeId[Bool]
    child2: NodeId[Bool]
