
Types
=======

Literal types
~~~~~~~~~~~~~~~

* Boolean literal: ``<bool_literal> = true | false``
* Non-negative integer: ``<int> = n`` with :math:`n \in \mathbb N_{0}`
* Bounded range: ``<bounded_range> = (bounded-range n m)`` with :math:`n,m \in \mathbb N_{0}` and :math:`n \leq m`
* Constant range: ``<range> = (range n m) | (range n $)`` with :math:`n,m \in \mathbb N_{0}` and :math:`n \leq m`



.. :math:`0 \leq n \leq m`

.. <bounded_range> = (bounded-range <integer1> <integer2>) with <integer1> <= <integer2>

.. <range> = (range <integer> $) | (range <integer1> <integer2>) with <integer1> <= <integer2>


Expression types
~~~~~~~~~~~~~~~~~

* Boolean Expression ``bool``
* Clocked Sequence ``clk-seq``
* Simple Sequence ``seq``
* Clocked Property ``clk-prop``
* Simple Property ``prop``
* Automata State
* Circuit



Clocked vs Simple Sequences/Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clocking
^^^^^^^^^^^^^

Clocks are handled by applying a rewriting pass to an expression to let it use
the global clock.
For sequences and properties, there are two expression types, respectively:
A clocked version and a *simple* version, which uses the global clock and does
not contain sequences admitting empty matches.
Different types are necessary because else rewriting of the clock would lead
to inconsistencies.


Empty Matches
^^^^^^^^^^^^^^^^

A separate rewriting pass removes the empty part of sequences in order
to exclude special cases.
This is possible because on the level of
properties, empty matches only play a role insofar that they
have an influence on non-empty sequences via concatenation.
In an overlapped implication, an empty match of the antecedent sequence does not
cause it to trigger.
According to the SV standard, the sequence expression of a sequential
property shall not admit an empty match.


(fewer primitives for simple sequences / simple properties?)