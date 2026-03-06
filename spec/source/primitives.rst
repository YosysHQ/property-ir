Primitives
---------------------

By convention, except for ``bool``,
each primitive symbol has as a prefix the type that it returns.


Boolean Expression
^^^^^^^^^^^^^^^^^^^^

.. *Note:* Do not use  &&, ||, !, because it becomes too confusing if there are many
    different names for the same concept. Use ``seq_and``, ``prop_and`` etc. for
    sequences and properties.

*Notes:*

* Sampled value functions (``$rose``, ``$fell``, ``$stable`` etc.)
  are handled outside of Property IR.


Basic booleans:

.. code-block:: sexpr

    <bool> = <signal_name>

           | (constant <bool_literal>) ; can be abbreviated as (<bool_literal>)


Boolean primitives:

.. code-block:: sexpr

    (not <bool>)

    (and <bool1> <bool2> ...)

    (or <bool1> <bool2> ...)


.. Are there other Boolean primitives we need to consider?

Examples
""""""""""""""

.. code-block:: sexpr

    (and c a)

    (or (and a b) (not (and (not a) c)) d)

    (not (and (not a) c))


Clocked Sequence
^^^^^^^^^^^^^^^^^

Clocked sequences use a clock that may be different from the global clock.
The available primitives are the same as for simple sequences, but with the
additional prefix ``clk-``.
All their arguments that are sequences need to be of type ``clk-seq``.

There is an additional primitive for specifying the clock.

.. code-block:: sexpr

    (clk-seq-clocked <bool> <clk_seq>) ; @(bool) clk-seq

The clock can explicitly be specified to be the global clock by using the argument ``(constant true)`` or ``(true)``.

.. code-block:: sexpr

    (clk-seq-clocked (true) <clk-seq>)


Transformation to Simple Sequence
""""""""""""""""""""""""""""""""""

The clocked sequence can be rewritten to a simple sequence using the macros
``#clk-seq-apply-clock``, ``#clk-seq-nonempty-part``, and ``#seq-remove-clock`` in
this order.

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


Simple Sequence
^^^^^^^^^^^^^^^^^^^^

Uses the global clock and does not admit empty matches.

.. Basic sequence (convert Boolean expression to sequence of length 1): ``(seq-bool <bool>)``


*Notes:*

* For ``seq-delay``, ``seq-repeat``, ``seq-goto-repeat``, and
  ``seq-nonconsecutive-repeat``, the case with a single integer argument can
  be represented as a bounded range with :math:`n = m` and is not
  handled as a separate case.
* ``triggered`` and ``matched`` are handled outside of Property IR.


Basic simple sequence:

.. code-block:: sexpr

    (seq-bool <bool>) ; convert Boolean expression to sequence of length 1
                      ; has no equivalent operator in SVA

Simple sequence primitives:

.. code-block:: sexpr

    (seq-repeat <range> <seq>) ; seq [m:n]

    (seq-delay <range> <seq>) ; ##[m:n] seq

    (seq-concat <seq1> <seq2> ...) ; seq1 ##1 seq2

    (seq-fusion <seq1> <seq2> ...) ; seq1 ##0 seq2

    (seq-intersect <seq1> <seq2> ...)

    (seq-and <seq1> <seq2> ...)

    (seq-or <seq1> <seq2> ...)

    (seq-goto-repeat <range> <bool>) ; bool [m->n]

    (seq-nonconsecutive-repeat <range> <bool>) ; bool [=m:n]

    (seq-first-match <seq>)

    (seq-within <seq1> <seq2>)

    (seq-throughout <bool> <seq>)



Examples
""""""""""""""""""""""

.. code-block:: sexpr

    (seq-concat (seq-bool a) (seq-bool (not b)) (seq-bool c))

    (seq-concat
        (seq-repeat 5 (seq-bool a))
        (seq-concat (seq-bool b) (seq-bool c)))


    (seq-intersect
        (seq-concat (seq-delay (range 2 $) (seq-bool b)))
        (seq-fusion
            (seq-concat (seq-bool a) (seq-bool b))
            (seq-repeat 3 (seq-bool b))))

Clocked Property
^^^^^^^^^^^^^^^^^

Clocked properties are analogous to clocked sequences and use a clock that may
be different from the global clock.
The available primitives are the same as for simple properties, but with the
additional prefix ``clk-``.
All their arguments that are sequences need to be of type ``clk-seq`` and all
arguments that are properties need to be of type ``clk-prop``.

There is an additional primitive for specifying the clock.

.. code-block:: sexpr

    (clk-prop-clocked <bool> <clk_prop>) ; @(bool) clk_prop

The clock can explicitly be specified to be the global clock by using the argument ``(constant true)`` or ``(true)``.

.. code-block:: sexpr

    (clk-prop-clocked (true) <clk_prop>)


The tranformation to a simple property is analogous to sequences, using the
macros ``#clk-prop-apply-clock``, ``#clk-prop-nonempty-part``, and
``#prop-remove-clock`` in this order.




Simple Property
^^^^^^^^^^^^^^^^^

Uses the global clock and does not contain sequences that admit empty matches.

..
    Question: Should something of a specific sort be allowed everywhere where an argument of that sort is allowed?
    If that is the case, does that mean that a special sort for top-level properties / disable-iff expressions is
    required?

    Answer:
    Yes, every instance of some sort should be allowed where an argument of that sort is expected.
    Possible solutions:
    1. Allow disable iff more flexibly
    2. Add Top-level property sort
    3. Assert-property gets option to add optional disable iff
    -> check why there is that restriction in SVA

    Question: The same issue occurs for recursive properties because there are
    restrictions on what kind of properties can be recursive. How should that be treated?

    Answer:
    Allow everything there in the syntax, and handle these additional conditions
    on the level of semantics. This means everything can be written down in the
    syntax as a fixpoint, but there might not exist a useful or unambiguous fixpoint.
    Either reject these cases later when they are handled, or the result can be anything.
    Also allow all types in let-rec expressions on the level of syntax.
    Semantically cyclic Boolean expressions can be detected and rejected later.
    Keep all restrictions of the SVA standard (although not all of them might be
    strictly necessary). ::


    <top_property> = <property> | (prop-disable-iff <bool> <property>)
    <property> = (<property_operation> <argument1> <argument2> ...)

Basic simple properties:

.. code-block:: sexpr

    (prop-seq <seq>) ; convert sequence to sequence property

    (prop-bool <bool>) ; convert boolean expression to sequence property
                       ; equivalent to (prop-seq (seq-bool <bool>))

    (prop-strong <seq>)

    (prop-weak <seq>)


Simple property primitives:

.. code-block:: sexpr

    (prop-and <prop1> <prop2> ...)

    (prop-or <prop1> <prop2> ...)

    (prop-not <prop>)

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




Examples
""""""""""""""

Property expressions:

.. code-block:: sexpr

    (prop-non-overlapped-implication
        (seq-concat (seq-bool a) (seq-bool b))
        (prop-always (prop-bool c)))

    (prop-until
        (prop-not (prop-seq (seq-concat (seq-bool a) (seq-bool b))))
        (prop-seq (seq-and (seq-bool c) (seq-bool a))))

    (prop-always-ranged
        (range 4 $)
        (prop-seq (seq-bool (not b))))

Recursive property:

.. code-block:: sexpr

    (let-rec (prop1
        (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool (true)) prop1)))
        prop1)

Mutually recursive properties:

.. code-block:: sexpr

    (let-rec
        (prop1 (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool (true)) prop2)))
        (prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool (true)) prop1)))
    prop1)


Declaration form:

.. code-block:: sexpr

    (declare-rec
        (declare prop1 (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool (true)) prop2)))
        (declare prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool (true)) prop1))))



