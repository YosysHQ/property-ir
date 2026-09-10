
from __future__ import annotations

from dataclasses import dataclass

from typeguard import typechecked

from ir.base import (
    Bool,
    NodeId,
    FiniteAutomaton,
    OmegaAutomaton
)



#-------------------------------+
#  Finite Automaton Primitives  |
#  (represents a Sequence)      |
#-------------------------------+

# accepting state

@typechecked
@dataclass
class AutAcc(FiniteAutomaton):
    child: NodeId[FiniteAutomaton]


# read/consume

@typechecked
@dataclass
class AutRead(FiniteAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[FiniteAutomaton]
    child3: NodeId[FiniteAutomaton]

@typechecked
@dataclass
class AutConsume(FiniteAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[FiniteAutomaton]
    child3: NodeId[FiniteAutomaton]

# alternation

@typechecked
@dataclass
class AutAnd(FiniteAutomaton):
    children: list[NodeId[FiniteAutomaton]]

@typechecked
@dataclass
class AutOr(FiniteAutomaton):
    children: list[NodeId[FiniteAutomaton]]

@typechecked
@dataclass
class AutTrue(FiniteAutomaton):
    pass

@typechecked
@dataclass
class AutFalse(FiniteAutomaton):
    pass

# subcalls

@typechecked
@dataclass
class AutCallEx(FiniteAutomaton):
    child1: NodeId[FiniteAutomaton]
    child2: NodeId[FiniteAutomaton]

@typechecked
@dataclass
class AutCallFirst(FiniteAutomaton):
    child1: NodeId[FiniteAutomaton]
    child2: NodeId[FiniteAutomaton]

# repeat

@typechecked
@dataclass
class AutRepeat(FiniteAutomaton):
    child1: int
    child2: NodeId[FiniteAutomaton]

@typechecked
@dataclass
class AutRepeatUpTo(FiniteAutomaton):
    child1: int
    child2: NodeId[FiniteAutomaton]

# refuted

@typechecked
@dataclass
class AutRefuted(FiniteAutomaton):
    child: NodeId[FiniteAutomaton]



#-------------------------------+
#  Omega Automaton Primitives   |
#  (represents a Property)      |
#-------------------------------+


# read/consume

@typechecked
@dataclass
class OmegaStrongRead(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaWeakRead(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaStrongConsume(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaWeakConsume(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaStrongConsumeAcc(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaWeakConsumeAcc(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
    child3: NodeId[OmegaAutomaton]

# alternation

@typechecked
@dataclass
class OmegaAnd(OmegaAutomaton):
    children: list[NodeId[OmegaAutomaton]]

@typechecked
@dataclass
class OmegaOr(OmegaAutomaton):
    children: list[NodeId[OmegaAutomaton]]

@typechecked
@dataclass
class OmegaTrue(OmegaAutomaton):
    pass

@typechecked
@dataclass
class OmegaFalse(OmegaAutomaton):
    pass

# subcalls

@typechecked
@dataclass
class OmegaCallAll(OmegaAutomaton):
    child1: NodeId[FiniteAutomaton]
    child2: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaCallExWeak(OmegaAutomaton):
    child1: NodeId[FiniteAutomaton]
    child2: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaCallExStrong(OmegaAutomaton):
    child1: NodeId[FiniteAutomaton]
    child2: NodeId[OmegaAutomaton]

# accept-on / reject-on

@typechecked
@dataclass
class OmegaAcceptOn(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]

@typechecked
@dataclass
class OmegaRejectOn(OmegaAutomaton):
    child1: NodeId[Bool]
    child2: NodeId[OmegaAutomaton]
