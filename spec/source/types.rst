
Types
=======

.. role:: sexpr(code)
   :language: sexpr

Literal types
~~~~~~~~~~~~~~~

* Boolean literal: :sexpr:`<bool_literal> ::= true | false`
* Non-negative integer: :sexpr:`<int> ::= n` with :math:`n \in \mathbb N_{0}`
* Bounded range: :sexpr:`<bounded_range> ::= (bounded-range m n)` with :math:`m,n \in \mathbb N_{0}` and :math:`m \leq n`
* Constant range: :sexpr:`<range> ::= (range m n) | (range m $)` with :math:`m,n \in \mathbb N_{0}` and :math:`m \leq n`

Literal types are used as parameters for primitives.

Boolean literals :sexpr:`true` and :sexpr:`false` are used to define constant
signals :sexpr:`(constant true)`  and :sexpr:`(constant false)`, which correspond
to ``1'b1`` and ``1'b0``.

There are two variants of ranges. A bounded range has an upper bound and a lower
bound, which are both non-negative integers, with the upper bound being equal to
or higher than the lower bound. The constant range can have the upper bound :sexpr:`$`,
indicating that it is unbounded.
It is important to use the correct range type expected by a primitive.
For example, delay accepts unbounded ranges, but weak eventually does not.

.. code-block:: sexpr

   (clk-seq-delay (range 2 $) (clk-seq-bool b)) ; ##[2:$] b

   (clk-prop-eventually (bounded-range 3 5) (clk-prop-bool b)) ; eventually [3:5] b


Most SVA operations with integer parameters also accept ranges.
In that case, Property IR has only a primitive that accepts a range, and a
single integer can be provided by having the same lower and upper bound.

.. code-block:: sexpr

   (clk-seq-delay (range 2 2) (clk-seq-bool b)) ; ##2 b

An exception are the primitives corresponding to ``nexttime``,
which have only an integer parameter.


.. code-block:: sexpr

   (clk-prop-nexttime 2 (clk-prop-bool b)) ; nexttime[2] b



Expression types
~~~~~~~~~~~~~~~~~

* Boolean Expression ``bool``
* Clocked Sequence ``clk-seq``
* Clocked Property ``clk-prop``

There exist additional internal types to represent automata states and circuits.
They are used internally during the verification flow and are not part of the
public interface.
There exist additional types to represent
:ref:`simple sequences and simple properties <simple sequences and simple properties>`.
Although they are used internally, they are included here because it is possible to use them
in assertions by applying the :sexpr:`clk-prop-prop` or :sexpr:`clk-seq-seq` primitives to them.
However, if you want to translate a SystemVerilog property into a Property IR expression,
you want to use the clocked versions of properties and sequences.

Boolean Expressions
^^^^^^^^^^^^^^^^^^^^

Boolean expressions correspond to signals, either directly through the declaration of
and external signal, as Boolean constants, or as a Boolean function using a basic set of logical operators.
They can only take the values true or false, and signal values ``x`` and ``z``
are interpreted as false.

.. code-block:: sexpr

   (declare-input a)
   (declare-input b)
   (declare c (and (or a b) (not b) (constant true)))

Also note that extended expressions, that depend not only on the current values
of inputs, like sampled value functions and the ``triggered`` and ``matched``
functions, need to be handled outside of Property IR.

Clocked Sequences
^^^^^^^^^^^^^^^^^^

Sequences model the progression of Boolean expression values over time, with one
value sampled at each clock tick.
Clocked sequences use a clock that may be different from the global clock.
The basic building blocks of sequences are sequences of length 1, consisting of
one value of a Boolean expression. They can be combined via concatenation, repetition,
and more complex operations.


.. code-block:: sexpr

   (declare-input a)
   (declare-input b)
   (declare-input c)
   (declare seq_1 (clk-seq-and
      (clk-seq-concat
         (clk-seq-delay (range 0 3) (clk-seq-bool (not a)))
         (clk-seq-bool (or a b)))
      (clk-seq-repeat (range 3 $) (clk-seq-bool c))))


Clocked Properties
^^^^^^^^^^^^^^^^^^

Properties model the behavior of a design and are built on the basis of sequences,
whose presence can be checked and tied to various conditions.
Like clocked sequences, clocked properties use a clock that may be different
from the global clock.

.. code-block:: sexpr

   (declare-input a)
   (declare-input b)
   (declare prop_1 (clk-prop-non-overlapped-implication
      (clk-seq-bool a)
      (clk-prop-until (clk-prop-bool b) (clk-prop-always a))))


Simple Sequences and Simple Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Simple Sequence ``seq``
* Simple Property ``prop``

Simple properties and simple sequences are used internally in a preparation
step for the verification flow, where
clocked properties and clocked sequences are first rewritten to their respective simple
versions by applying several rewriting passes.
They are simple in the following sense:

* They have a smaller set of primitives.
* They use the global clock, which is why there is no need to explicitly specify a clock.
* They do not contain any subsequences that admit empty matches.

Establishing these restrictions will facilitate the subsequent automata constructions.
These separate types were introduced to avoid
inconsistencies that would result from clock rewriting.

The following explanations can be skipped if wanting to use Property IR,
but might be interesting as a background.

Smaller primitive set
"""""""""""""""""""""""""""""

The reduced set of primitives was chosen in such a way that at least

* nonderived primitives are included, and
* dual operations are included.

Additional primitives may be added if they turn out benefical for automata
constructions or subsequent optimizations.

Including dual operations is necessary in order to establish the *negation normal form*, which
is done before the transformation into automata.
For example, :sexpr:`(prop-overlapped-followed-by <seq> <prop>)` is equivalent to
:sexpr:`(prop-not (prop-overlapped-implication <seq> (prop-not <prop>)))`
and is therefore the dual of the nonderived
primitive :sexpr:`prop-overlapped-implication`.

.. not (seq |-> not prop)

On the other hand, an example for a derived primitive that can be removed
is :sexpr:`(seq-goto-repeat <range> <bool>)`, because it can be
rewritten in the following way.

.. code-block:: sexpr

   (seq-repeat <range> (seq-concat
      (seq-repeat (range 0 $) (not <bool>))
      <bool>))

.. expr [->m:n]	for m < n
.. ( !expr [*0:$] ##1 expr )[*m:n]


Global clock
"""""""""""""""

All clock controls are expected to be *level-sensitive*
(or rather a time-discrete global-clock sampled clock control), i.e., they are high
in the global clock tick where they have their rising (resp. falling) edge.
Clocked properties, that can have one or multiple clocks,
are rewritten in such a way that they use the global clock.
Roughly speaking, this is achieved by recursively rewriting property expressions
such that sequences of length 1 are replaced by a sequence waiting for the clock
event to happen (and additional rewriting rules for handling operations like
``nexttime`` and ``until``).

Let ``b`` be a signal, and ``c`` the level-sensitive clock signal.
Then :sexpr:`(clk-seq-clocked c (clk-seq-bool b))` becomes
the following expression.

.. code-block:: sexpr

   (seq-concat (seq-repeat (range 0 $) (not c)) (and c b))

.. T s (b, c) = (!c[*0:$] ##1 c & b)


.. Clocks are handled by applying a rewriting pass to an expression to let it use the global clock.

.. For sequences and properties, there are two expression types, respectively:
.. A clocked version and a *simple* version, which uses the global clock and does
.. not contain sequences admitting empty matches.
.. Different types are necessary because else rewriting of the clock would lead
.. to inconsistencies.


Empty Matches
""""""""""""""""

A separate rewriting pass removes the empty part of sequences in order
to exclude special cases.
This is possible because on the level of
properties, empty matches only play a role insofar that they
have an influence on non-empty sequences via concatenation.
In an overlapped implication, an empty match of the antecedent sequence does not
cause it to trigger.
According to the SystemVerilog standard, the sequence expression of a sequential
property shall not admit an empty match.

example


Transformation to Simple Sequence
"""""""""""""""""""""""""""""""""""

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