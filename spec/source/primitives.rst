Primitives
---------------------

.. role:: sexpr(code)
   :language: sexpr

By convention, except for ``bool``,
each primitive symbol has as a prefix the type that it returns.
This makes the type of an expression immediately evident, and is necessary
to disambiguate between for example :sexpr:`and`, :sexpr:`seq-and`, and :sexpr:`prop-and`.


Boolean Expression
^^^^^^^^^^^^^^^^^^^^

.. Recall that ``x`` and ``z`` do not exist inside Property IR, and are treated
.. as they usually are in SystemVerilog in a purely Boolean context.

.. note::

    Extended Booleans like sampled value functions (``$past``, ``$rose``, ``$fell``, ``$stable`` etc.)
    as well as ``triggered`` and ``matched``
    need to be handled outside of Property IR.


Base Booleans
""""""""""""""""

.. code-block:: sexpr

    <signal_name>

    (constant <bool_literal>) ; can be abbreviated as (<bool_literal>)

    (initial)

After declaring a one-bit signal as external input using :sexpr:`declare-input`,
it can be used as an expression of type ``bool``.

A Boolean that is constant high (``1'b1``) resp. low (``1'b0``) is written as
:sexpr:`(constant true)` resp. :sexpr:`(constant false)`, or abbreviated as
:sexpr:`(true)` resp. :sexpr:`(false)`.

The Boolean primitive :sexpr:`initial` corresponds to a signal that is high only in
the first time step.



Boolean primitives
""""""""""""""""""""

.. code-block:: sexpr

    (not <bool>)

    (and <bool1> <bool2> ...)

    (or <bool1> <bool2> ...)

These primitives correspond to the logical operators ``!``, ``&&``, and ``||`` of SystemVerilog.
The primitives ``and`` and ``or`` accept any positive number of arguments of type ``bool``.




Clocked Sequence
^^^^^^^^^^^^^^^^^

Clocked sequences use a clock that may be different from the global clock.
Each primitive has the prefix ``clk-seq-``.
All their arguments that are sequences need to be of type ``clk-seq`` as well.


.. The extended Booleans ``triggered`` and ``matched`` operating on sequences
.. are handled outside of Property IR.


Specifying the sequence clock
""""""""""""""""""""""""""""""

The following primitive is used for specifying the clock.
The clock can be changed anywhere within the sequence.

.. code-block:: sexpr

    (clk-seq-clocked <bool> <clk_seq>) ; @(bool) clk_seq

The clock can explicitly be specified to be the global clock by using
the argument :sexpr:`(constant true)` or :sexpr:`(true)`.

.. code-block:: sexpr

    (clk-seq-clocked (constant true) <clk_seq>)

If on the outermost layer of a clocked sequence expression no clock is
specified, it is assumed to be the global clock until it is changed to
another clock with :sexpr:`clk-seq-clocked`.


Clocked sequence base primitive
"""""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (clk-seq-bool <bool>)

The :sexpr:`clk-seq-bool` primitive converts a Boolean expression to a
clocked sequence of length 1. In SystemVerilog, there exists no
equivalent operator because this happens implicitly by using a Boolean
expression in a sequence context.

Clocked sequence primitives
""""""""""""""""""""""""""""

.. note::

    For :sexpr:`clk-seq-delay`, :sexpr:`clk-seq-repeat`, :sexpr:`clk-seq-goto-repeat`, and
    :sexpr:`clk-seq-nonconsecutive-repeat`, the case with a single integer argument can
    be represented with a constant range with :math:`n = m` and is not
    handled as a separate case.

    Unbounded delay (``##[*]``, ``##[+]``) and unbounded
    repetition (``clk_seq [*]``, ``clk_seq [+]``) shorthand notation is written
    out with :sexpr:`(range 0 $)` resp. :sexpr:`(range 1 $)`.

Concatenation, repetition, and delay
''''''''''''''''''''''''''''''''''''''

.. code-block:: sexpr

    (clk-seq-repeat <range> <clk_seq>) ; clk_seq [m:n]

    (clk-seq-delay <range> <clk_seq>) ; ##[m:n] clk_seq

    (clk-seq-concat <clk_seq1> <clk_seq2> ...) ; clk_seq1 ##1 clk_seq2

    (clk-seq-fusion <clk_seq1> <clk_seq2> ...) ; clk_seq1 ##0 clk_seq2


:sexpr:`clk-seq-repeat` -- The sequence :sexpr:`<clk_seq>` is repeated
the number of times specified by :sexpr:`<range>` (may be unbounded).

:sexpr:`clk-seq-delay` -- The sequence :sexpr:`<clk_seq>` is delayed
by the number of time steps specified by :sexpr:`<range>` (may be
unbounded). Equivalent to
:sexpr:`(clk-seq-concat (clk-seq-repeat (seq-bool (true)) <range>) <clk_seq>)` .

:sexpr:`clk-seq-concat` -- Non-overlapping concatenation of any positive number
of argument sequences.
The first time step of each argument sequence is the time step after the last
time step of the previous argument sequence.

:sexpr:`clk-seq-fusion`-- Overlapping concatenation of any positive number of
argument sequences. The last time step of each argument sequence
coincides with the first time step of the subsequent argument sequence.


.. code-block:: sexpr

    (clk-seq-goto-repeat <range> <bool>) ; bool [m->n]

    (clk-seq-nonconsecutive-repeat <range> <bool>) ; bool [=m:n]

These repetition primitives operate on Boolean expressions and not on sequences.

:sexpr:`clk-seq-goto-repeat` -- Boolean expression :sexpr:`<bool>` holds
:sexpr:`<range>` number of time steps (may be unbounded), with gaps allowed inbetween.
The matched sequence needs to end in a time step where :sexpr:`<bool>` holds.

:sexpr:`clk-seq-nonconsecutive-repeat` -- Boolean expression :sexpr:`<bool>` holds
:sexpr:`<range>` number of time steps (may be unbounded), with gaps allowed inbetween.
The matched sequence may end with a gap.



Parallel sequences
''''''''''''''''''''''''''''''''''''''

.. code-block:: sexpr

    (clk-seq-and <clk_seq1> <clk_seq2> ...)

    (clk-seq-intersect <clk_seq1> <clk_seq2> ...)

    (clk-seq-or <clk_seq1> <clk_seq2> ...)


These primitives take any positive number of argument sequences.

:sexpr:`clk-seq-and` -- All argument sequences need to match and have the same
start point, but they may have different end points. The end point of the match
is the latest end point of an argument sequence.


:sexpr:`clk-seq-intersect` -- All argument sequences need to match and have the same
start point and end point.

:sexpr:`clk-seq-or` -- At least one of the argument sequences needs to match
in order to produce a match in a given time step. The set of matches of the
sequence is the union of the matches of argument sequences.



Conditions on sequences
''''''''''''''''''''''''''''''''''''''

.. code-block:: sexpr

    (clk-seq-first-match <clk_seq>)

Only the first match of :sexpr:`<clk_seq>` of an evaluation attempt is considered,
all other matches are discarded.
The first match is the match with the earliest end point.


.. code-block:: sexpr

    (clk-seq-throughout <bool> <clk_seq>)

    (clk-seq-within <clk_seq1> <clk_seq2>)


:sexpr:`clk-seq-throughout` -- Boolean expression :sexpr:`<bool>` must hold on
each time step of :sexpr:`<clk_seq>`.

:sexpr:`clk-seq-within` -- Sequence :sexpr:`<clk_seq1>` must have a match in
a subinterval of :sexpr:`<clk_seq2>`.
It may span over the complete length of :sexpr:`<clk_seq2>`.





Clocked Property
^^^^^^^^^^^^^^^^^

Like clocked sequences, clocked properties use a clock that may
be different from the global clock.
Each primitive has the prefix ``clk-prop-``.
All their sequence arguments need to be of type ``clk-seq``, and all
property arguments need to be of type ``clk-prop``.


Specifying the property clock
""""""""""""""""""""""""""""""

The following primitive is used for specifying the clock.
The clock can be changed anywhere within the property.

.. code-block:: sexpr

    (clk-prop-clocked <bool> <clk_prop>) ; @(bool) clk_prop

The clock can explicitly be specified to be the global clock by using
the argument :sexpr:`(constant true)` or :sexpr:`(true)`.

.. code-block:: sexpr

    (clk-prop-clocked (true) <clk_prop>)

If on the outermost layer of a clocked property expression no clock is
specified, it is assumed to be the global clock until it is changed to
another clock with :sexpr:`clk-prop-clocked`.


Clocked property base primitives
""""""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (clk-prop-seq <clk_seq>)

    (clk-prop-bool <bool>)

convert boolean expression to sequence property
equivalent to (prop-seq (seq-bool <bool>))

convert sequence to sequence property

must not admit an empty match



.. code-block:: sexpr

    (clk-prop-strong <clk_seq>)

    (clk-prop-weak <clk_seq>)


weak / strong default depends on assertion type:


strong: there must exist a nonempty match

weak: no finite prefix witnesses the inability to match


Clocked property primitives
""""""""""""""""""""""""""""

Logical property operators
''''''''''''''''''''''''''''

.. code-block:: sexpr

    (clk-prop-not <clk_prop>)

    (clk-prop-or <clk_prop1> <clk_prop2> ...)

    (clk-prop-and <clk_prop1> <clk_prop2> ...)

    (clk-prop-iff <clk_prop1> <clk_prop2>)

    (clk-prop-implies <clk_prop1> <clk_prop2>)


These primitives correspond to the logical operators applied to properties.

The primitives :sexpr:`clk-prop-or` and  :sexpr:`clk-prop-and`
take any positive number of argument properties.


Primitive :sexpr:`clk-prop-iff` is the logical operator :math:`\Leftrightarrow`
that is true iff both argument properties have the same truth value.

Primitive :sexpr:`clk-prop-implies` is the logical operator :math:`\Rightarrow`
that is true if the first argument property is false or if the second
argument property is true.
Do not confuse with implication operators ``|->`` (overlapped)
and ``|=>`` (non-overlapped), which take a sequence and a property as arguments.

Negation :sexpr:`clk-prop-not` requires some attention in order to avoid
unintuitive behavior in combination with weak satisfaction. Assume we
assert the following property.

.. code-block:: sexpr

    (clk-prop-not (clk-prop-seq
        (clk-seq-concat (seq-bool a) (seq-bool b))))

By default, :sexpr:`assert-property` uses weak satisfaction, and the property
fails on any finite sequence ending in a time step where ``a`` holds (because it
is possible that ``b`` holds in the following time step).
More intuitive behavior is achieved by explicitly using strong satisfaction
to fail only if the offending sequence is witnessed.

.. code-block:: sexpr

    (clk-prop-not (clk-prop-strong
        (clk-seq-concat (seq-bool a) (seq-bool b))))

Negation must not be applied to recursive properties.


Conditionals
''''''''''''''''''

.. note::

    The ``case`` property block needs to be translated into a (nested) ``if ... else`` block
    to be represented in Property IR.

.. code-block:: sexpr

    (clk-prop-if <bool> <clk_prop>)

    (clk-prop-if-else <bool> <clk_prop1> <clk_prop2>)

In the case of :sexpr:`clk-prop-if`, the property is satisfied if :sexpr:`<bool>` does not hold, or if
:sexpr:`<bool>` holds and the first argument property holds (equivalent to overlapped implication).
In the case of :sexpr:`clk-prop-if-else`, if :sexpr:`<bool>` does
not holds, additionally, the second argument property must hold in order for
the property to be satisfied.


Nexttime
''''''''''''''''''

.. note::

    In SVA, if the integer argument is omitted, :sexpr:`<int> = 1` is assumed.
    In Property IR, we explicitly need to provide it.

.. code-block:: sexpr

    (clk-prop-nexttime <int> <clk_prop>)

    (clk-prop-strong-nexttime <int> <clk_prop>)

This primitive checks if the argument property holds :sexpr:`<int>`
time steps in the future.
In the weak variant, the property evaluates to true if the referenced time step
does not exist.
In the strong variant, the property evaluates to false if the referenced time step
does not exist.
If the evaluation attempt begins inbetween clock ticks,
the evaluation is moved to the next clock tick.
Therefore, the integer argument :sexpr:`<int> = 0` can be used for alignment.
In other words, the argument property has to hold on time step :sexpr:`<int> + 1`,
beginning to count at the current time step (which might have already started)
for the property to evaluate to true.
For example, :sexpr:`(clk-prop-nexttime 2 (clk-prop-bool a))` checks whether ``a``
holds at the second future clock tick.


Implication and followed-by
''''''''''''''''''''''''''''''

.. code-block:: sexpr

    (clk-prop-overlapped-implication <clk_seq> <clk_prop>) ; clk_seq |-> clk_prop

    (clk-prop-non-overlapped-implication <clk_seq> <clk_prop>) ; clk_seq |=> clk_prop

Witnessing the sequence :sexpr:`<clk_seq>` triggers the evaluation of property
:sexpr:`<clk_prop>`, which has to hold either on the last time step of the sequence
(overlapped), or on the next time step after the sequence matched (non-overlapped)
to satisfy the implication.

Do not confuse with :sexpr:`clk-prop-implies`, which takes two properties as arguments.

.. code-block:: sexpr

    (clk-prop-overlapped-followed-by <clk_seq> <clk_prop>) ; clk_seq #-# clk_prop

    (clk-prop-non-overlapped-followed-by <clk_seq> <clk_prop>) ; clk_seq #=# clk_prop

These primitives are the duals of the implication primitives.
For example, the overlapped followed-by primitive is equivalent to to the following expression.

.. code-block:: sexpr

    (clk-prop-not (clk-prop-overlapped-implication <clk_seq> (clk-prop-not <clk-prop>)))

The followed-by property evaluates to true iff
there exists at least one match for the sequence :sexpr:`<clk_seq>`, and at the
end of one of its matches, the property :sexpr:`<clk_prop>` holds --
either in the last time step of the sequence (overlapped), or in the next time
step (non-overlapped), depending on the variant.


Until
''''''''

.. code-block:: sexpr

    (clk-prop-until <clk_prop1> <clk_prop2>)

    (clk-prop-strong-until <clk_prop1> <clk_prop2>)

    (clk-prop-until-with <clk_prop1> <clk_prop2>)

    (clk-prop-strong-until <clk_prop1> <clk_prop2>)

These primitives requires that :sexpr:`<clk_prop1>` holds up until to the point
where :sexpr:`<clk_prop2>` holds for the first time.
The ``until-with`` variants are overlapping, meaning that it is required that
:sexpr:`<clk_prop1>` and :sexpr:`<clk_prop2>` hold simultaneously for at least
one time step before :sexpr:`<clk_prop1>` is allowed to not hold anymore.
In linear temporal logic (LTL), this operator is called *release*.
In the weak variants, the property as a whole evaluates to true even if :sexpr:`<clk_prop2>`
is not witnessed, provided that :sexpr:`<clk_prop1>` holds until the end of the trace.
In the strong variants, :sexpr:`<clk_prop2>` must be witnessed in order for the
property as a whole to evaluate to true.

The strong variants can not be used in recursive properties.


Always and eventually
''''''''''''''''''''''''

If the evaluation attempt begins inbetween clock ticks,
the evaluation is moved to the next clock tick.

.. code-block:: sexpr

    (clk-prop-always <clk_prop>) ; Question: should we omit the version without a range?

    (clk-prop-always-ranged <range> <clk_prop>)

    (clk-prop-strong-always <bounded_range> <clk_prop>)

The property :sexpr:`<clk_prop>` provided to :sexpr:`clk-prop-always` (weak), must hold
at every current or future time step, if it exists.

In the ranged variant (weak), the property must hold at each time step in the
(possibly unbounded) range, if the time step exists.

In the strong variant, the property must hold at each time step of the
provided bounded range, and each of these time steps has to exist.

In LTL, the ``always`` operator is called *globally*.

.. code-block:: sexpr

    (clk-prop-eventually <bounded_range> <clk_prop>)

    (clk-prop-strong-eventually <clk_prop>)  ; Question: should we omit the version without a range?

    (clk-prop-strong-eventually-ranged <range> <clk_prop>)

The weak variant expects a bounded range as a parameter and
requires that somewhere in that range :sexpr:`<clk_prop>` holds. It evaluates to
true if the trace ends before the bounded range has ended, even when
:sexpr:`<clk_prop>` has not been witnessed yet.

In the strong variant, there must exist a current or future time step where
:sexpr:`<clk_prop>` holds.

In the strong ranged variant, there must exist a current or future time step
within the (possibly unbounded) range where :sexpr:`<clk_prop>` holds.

In LTL, the ``eventually`` operator is called *finally*.

The strong variants can not be used in recursive properties.

Abort properties
''''''''''''''''''

.. code-block:: sexpr

    (clk-prop-accept-on <bool> <clk_prop>)

    (clk-prop-reject-on <bool> <clk_prop>)

    (clk-prop-sync-accept-on <bool> <clk_prop>)

    (clk-prop-sync-reject-on <bool> <clk_prop>)



Simple Sequence
^^^^^^^^^^^^^^^^^^^^

Simple sequences use the global clock and do not admit empty matches.

See ... for more information on the differences to clocked sequences.

There is a reduced set of primitives for simple sequence. All derived
primitives that can be expressed using other more basic primitives are removed
in a rewriting pass as a step in the transformation from clocked sequences to
simple sequences.

no empty repeat

Simple sequence base primitive
""""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (seq-bool <bool>)

The ``seq-bool`` primitive converts a Boolean expression to a simple sequence
of length 1.

Simple sequence primitives
"""""""""""""""""""""""""""


..    For ``seq-delay``, ``seq-repeat``, ``seq-goto-repeat``, and
..    ``seq-nonconsecutive-repeat``, the case with a single integer argument can
..    be represented as a constant range with :math:`n = m` and is not
..    handled as a separate case.

.. code-block:: sexpr

    (seq-repeat <range> <seq>) ; seq [m:n]

    (seq-concat <seq1> <seq2> ...) ; seq1 ##1 seq2

    (seq-fusion <seq1> <seq2> ...) ; seq1 ##0 seq2

    (seq-or <seq1> <seq2> ...)

    (seq-intersect <seq1> <seq2> ...)

    (seq-first-match <seq>)


..    (seq-delay <range> <seq>) ; ##[m:n] seq

..    (seq-goto-repeat <range> <bool>) ; bool [m->n]

..    (seq-nonconsecutive-repeat <range> <bool>) ; bool [=m:n]

..    (seq-and <seq1> <seq2> ...)
..
..    (seq-within <seq1> <seq2>)
..
..    (seq-throughout <bool> <seq>)




Simple Property
^^^^^^^^^^^^^^^^^

Uses the global clock and does not contain sequences that admit empty matches.

Simple property base primitives
"""""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (prop-seq <seq>) ; convert sequence to sequence property

    (prop-bool <bool>) ; convert boolean expression to sequence property
                       ; equivalent to (prop-seq (seq-bool <bool>))

    (prop-strong <seq>)

    (prop-weak <seq>)


Simple property primitives
"""""""""""""""""""""""""""""

.. code-block:: sexpr

    (prop-and <prop1> <prop2> ...)

    (prop-or <prop1> <prop2> ...)

    (prop-not <prop>)

    (prop-nexttime <int> <prop>)

    (prop-overlapped-implication <seq> <prop>) ; seq |-> prop

    (prop-until <prop1> <prop2>)

    (prop-accept-on <bool> <prop>)



..    (prop-strong-until <prop1> <prop2>)
..
..    (prop-until-with <prop1> <prop2>)
..
..    (prop-strong-until <prop1> <prop2>)


..    (prop-always <prop>) ; Question: should we omit the version without a range?
..
..    (prop-always-ranged <range> <prop>)
..
..    (prop-strong-always <bounded_range> <prop>)
..
..    (prop-eventually <bounded_range> <prop>)
..
..    (prop-strong-eventually <prop>)  ; Question: should we omit the version without a range?
..
..    (prop-strong-eventually-ranged <range> <prop>)

..    (prop-iff <prop1> <prop2>)

..    (prop-implies <prop1> <prop2>)

..    (prop-if <bool> <prop>)

..    (prop-if-else <bool> <prop1> <prop2>)



..    (prop-non-overlapped-implication <seq> <prop>) ; seq |=> prop

..    (prop-overlapped-followed-by <seq> <prop>) ; seq #-# prop

..    (prop-non-overlapped-followed-by <seq> <prop>) ; seq #=# prop


..    (prop-reject-on <bool> <prop>)
..
..    (prop-sync-accept-on <bool> <prop>)
..
..    (prop-sync-reject-on <bool> <prop>)



