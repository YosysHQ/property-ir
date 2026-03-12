Primitives
---------------------

.. role:: sexpr(code)
   :language: sexpr

By convention, except for ``bool``,
each primitive symbol has as a prefix the type that it returns.
This makes the type of an expression immediately evident, and is necessary
to disambiguate between for example ``and``, ``seq-and``, and ``prop-and``.


Boolean Expression
^^^^^^^^^^^^^^^^^^^^

.. Recall that ``x`` and ``z`` do not exist inside Property IR, and are treated
.. as they usually are in SystemVerilog in a purely Boolean context.

.. note::

    Extended Booleans like sampled value functions (``$past``, ``$rose``, ``$fell``, ``$stable`` etc.)
    as well as ``triggered`` and ``matched``
    need to be handled outside of Property IR.


Basic Booleans
""""""""""""""""

.. code-block:: sexpr

    <signal_name>

    (constant <bool_literal>) ; can be abbreviated as (<bool_literal>)

    (initial)

After declaring a one-bit signal as external input using ``declare-input``,
it can be used as an expression of type ``bool``.

A Boolean that is constant high (``1'b1``) resp. low (``1'b0``) is written as
``(constant true)`` resp. ``(constant false)``, or abbreviated as ``(true)`` resp. ``(false)``.

The Boolean primitive ``initial`` corresponds to a signal that is high only in
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

.. note:

    The extended Booleans ``triggered`` and ``matched`` operating on sequences
    are handled outside of Property IR.


Specifying the clock
""""""""""""""""""""""

The following primitive is used for specifying the clock.

.. code-block:: sexpr

    (clk-seq-clocked <bool> <clk_seq>) ; @(bool) clk_seq

The clock can explicitly be specified to be the global clock by using
the argument ``(constant true)`` or ``(true)``.

.. code-block:: sexpr

    (clk-seq-clocked (true) <clk_seq>)


Basic clocked sequence
"""""""""""""""""""""""

.. code-block:: sexpr

    (clk-seq-bool <bool>)

The ``clk-seq-bool`` primitive converts a Boolean expression to a sequence of
length 1. In SystemVerilog, this happens implicitly, therefore there exists no
equivalent operator in SVA.

Clocked sequence primitives
""""""""""""""""""""""""""""

.. note::

    For ``clk-seq-delay``, ``clk-seq-repeat``, ``clk-seq-goto-repeat``, and
    ``clk-seq-nonconsecutive-repeat``, the case with a single integer argument can
    be represented as a constant range with :math:`n = m` and is not
    handled as a separate case.

.. code-block:: sexpr

    (clk-seq-repeat <range> <clk_seq>) ; seq [m:n]

    (clk-seq-delay <range> <clk_seq>) ; ##[m:n] seq

    (clk-seq-concat <clk_seq1> <clk_seq2> ...) ; clk_seq1 ##1 clk_seq2

    (clk-seq-fusion <clk_seq1> <clk_seq2> ...) ; clk_seq1 ##0 clk_seq2

    (clk-seq-or <clk_seq1> <clk_seq2> ...)

    (clk-seq-intersect <clk_seq1> <clk_seq2> ...)

    (clk-seq-and <clk_seq1> <clk_seq2> ...)

    (clk-seq-first-match <clk_seq>)

    (clk-seq-goto-repeat <range> <bool>) ; bool [m->n]

    (clk-seq-nonconsecutive-repeat <range> <bool>) ; bool [=m:n]

    (clk-seq-within <clk_seq1> <clk_seq2>)

    (clk-seq-throughout <bool> <clk_seq>)





Clocked Property
^^^^^^^^^^^^^^^^^

Clocked properties are analogous to clocked sequences and use a clock that may
be different from the global clock.
The available primitives are the same as for simple properties, but with the
additional prefix ``clk-``.
All their arguments that are sequences need to be of type ``clk-seq`` and all
arguments that are properties need to be of type ``clk-prop``.


Specifying the clock
""""""""""""""""""""""

The following primitive is used for specifying the clock.

.. code-block:: sexpr

    (clk-prop-clocked <bool> <clk_prop>) ; @(bool) clk_prop

The clock can explicitly be specified to be the global clock by using the argument ``(constant true)`` or ``(true)``.

.. code-block:: sexpr

    (clk-prop-clocked (true) <clk_prop>)


The tranformation to a simple property is analogous to sequences, using the
macros ``#clk-prop-apply-clock``, ``#clk-prop-nonempty-part``, and
``#prop-remove-clock`` in this order.


Basic clocked properties
""""""""""""""""""""""""""

.. code-block:: sexpr

    (prop-seq <seq>) ; convert sequence to sequence property

    (prop-bool <bool>) ; convert boolean expression to sequence property
                       ; equivalent to (prop-seq (seq-bool <bool>))

    (prop-strong <seq>)

    (prop-weak <seq>)


Clocked property primitives
""""""""""""""""""""""""""""

.. note:

    The ``case`` property block needs to be translated into an ``if else`` block
    to be represented in Property IR.

.. code-block:: sexpr

    (prop-not <prop>)

    (prop-or <prop1> <prop2> ...)

    (prop-and <prop1> <prop2> ...)

    (prop-iff <prop1> <prop2>)

    (prop-implies <prop1> <prop2>)

    (prop-if <bool> <prop>)

    (prop-if-else <bool> <prop1> <prop2>)


    (prop-nexttime <int> <prop>)


    (prop-overlapped-implication <seq> <prop>) ; seq |-> prop

    (prop-non-overlapped-implication <seq> <prop>) ; seq |=> prop

    (prop-overlapped-followed-by <seq> <prop>) ; seq #-# prop

    (prop-non-overlapped-followed-by <seq> <prop>) ; seq #=# prop


    (prop-until <prop1> <prop2>)

    (prop-strong-until <prop1> <prop2>)

    (prop-until-with <prop1> <prop2>)

    (prop-strong-until <prop1> <prop2>)


    (prop-always <prop>) ; Question: should we omit the version without a range?

    (prop-always-ranged <range> <prop>)

    (prop-strong-always <bounded_range> <prop>)

    (prop-eventually <bounded_range> <prop>)

    (prop-strong-eventually <prop>)  ; Question: should we omit the version without a range?

    (prop-strong-eventually-ranged <range> <prop>)


    (prop-accept-on <bool> <prop>)

    (prop-reject-on <bool> <prop>)

    (prop-sync-accept-on <bool> <prop>)

    (prop-sync-reject-on <bool> <prop>)



Simple Sequence
^^^^^^^^^^^^^^^^^^^^

Simple sequences use the global clock and do not admit empty matches.

See ... for more information on the differences to clocked sequences.

There is a reduced set of primitives for simple sequence. All derived
primitives that can be expressed using other more basic primitives are removed
in a rewriting pass as a step in the transformation from clocked sequences to
simple sequences.



Basic simple sequence
""""""""""""""""""""""

.. code-block:: sexpr

    (seq-bool <bool>)

The ``seq-bool`` primitive converts a Boolean expression to a sequence of
length 1.

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

Basic simple properties
""""""""""""""""""""""""

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



