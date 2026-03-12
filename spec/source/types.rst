
Types
=======

.. role:: sexpr(code)
   :language: sexpr

Literal types
~~~~~~~~~~~~~~~

* Boolean literal: :sexpr:`<bool_literal> = true | false`
* Non-negative integer: :sexpr:`<int> = n` with :math:`n \in \mathbb N_{0}`
* Bounded range: :sexpr:`<bounded_range> = (bounded-range m n)` with :math:`m,n \in \mathbb N_{0}` and :math:`m \leq n`
* Constant range: :sexpr:`<range> = (range m n) | (range m $)` with :math:`m,n \in \mathbb N_{0}` and :math:`m \leq n`



.. :math:`0 \leq n \leq m`

.. <bounded_range> = (bounded-range <integer1> <integer2>) with <integer1> <= <integer2>

.. <range> = (range <integer> $) | (range <integer1> <integer2>) with <integer1> <= <integer2>


Expression types
~~~~~~~~~~~~~~~~~

* Boolean Expression ``bool``
* Clocked Sequence ``clk-seq``
* Clocked Property ``clk-prop``
* Simple Sequence ``seq``
* Simple Property ``prop``

There exist internal types to represent automata state and circuits.
They are used internally during the verification flow and are not part of the
public interface.



Clocked vs Simple Sequences/Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: revise this section

Removing Derived Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO: include


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


Transformation to Simple Sequence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The clocked sequence can be rewritten to a simple sequence using the macros
``#clk-seq-apply-clock``, ``#clk-seq-nonempty-part``, and ``#seq-remove-clock`` in
this order.

The tranformation of a clocked property to a simple property is analogous to sequences, using the
macros ``#clk-prop-apply-clock``, ``#clk-prop-nonempty-part``, and
``#prop-remove-clock`` in this order.

.. code-block:: sexpr

    (clk-seq-clocked <bool> <clk_seq>)  ; clocked

    |   #clk-seq-apply-clock
    V

    (clk-seq-clocked (true) <clk_seq2>)   ; global-clocked

    |  #clk-seq-nonempty-part
    V

    (clk-seq-clocked (true) <clk_seq3>)   ; global-clocked and non-empty-matching

    |  #seq-remove-clock
    V

    <seq>                               ; simple/unclocked