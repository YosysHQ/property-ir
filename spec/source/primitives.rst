Types and Operations
---------------------


Boolean Expression
^^^^^^^^^^^^^^^^^^^^

**Operations**: ``and, or, not``

*Note:* Do not use  &&, ||, !, because it becomes too confusing if there are many
different names for the same concept. Use ``seq_and``, ``prop_and`` etc. for
sequences and properties.

.. code-block:: sexpr

    <bool> = true | false | <signal> | (<operation> <bool1> <bool2> ...)


Examples:

.. code-block:: sexpr

    (and c a)

    (or (and a b) (not (and (not a) c)) d)

    (not (and (not a) c))

Clocked Sequence
^^^^^^^^^^^^^^^^^

TODO: clocked sequence
(Simple) Sequence
Uses the global clock and does not have empty matches.

.. code-block:: sexpr

    <sequence> = (<sequence_operation> <argument1> <argument2> ...)

Basic sequence (convert Boolean expression to sequence of length 1): ``(seq_bool <bool>)``

**Example operations:** repeat, delay, concat, fusion, intersect, seq-bool, seq-and

**Argument types:** sequence, boolean expression, integer, bounded range, range

.. code-block:: sexpr

    <bounded_range> = (range <integer1> <integer2>) with <integer1> <= <integer2>

    <range> = <bounded_range> | (range <integer> $)

*Note:* For delay and repeat, the case with a single integer argument can be represented as a bounded range with <integer1> = <integer2> and must not be represented as a separate case.

Sequence operations:

.. code-block:: sexpr

    (seq-bool <bool>)

    (seq-repeat <range> <sequence>)

    (seq-delay <range> <sequence>)

    (seq-concat <sequence1> <sequence2> ...)

    (seq-fusion <sequence1> <sequence2> ...)

    (seq-intersect <sequence1> <sequence2> ...)

    (seq-and <sequence1> <sequence2> ...)

Examples:

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

TODO: clocked property

Property
^^^^^^^^^^

..
    Question: Should something of a specific sort be allowed everywhere where an argument of that sort is allowed? If that is the case, does that mean that a special sort for top-level properties / disable-iff expressions is required?

    Answer:
    Yes, every instance of some sort should be allowed where an argument of that sort is expected.
    Possible solutions:
    Allow disable iff more flexibly
    Add Top-level property sort
    Assert-property gets option to add optional disable iff
    -> check why there is that restriction in SVA

    Question: The same issue occurs for recursive properties because there are restrictions on what kind of properties can be recursive. How should that be treated?

    Answer:
    Allow everything there in the syntax, and handle these additional conditions on the level of semantics. This means everything can be written down in the syntax as a fixpoint, but there might not exist a useful or unambiguous fixpoint. Either reject these cases later when they are handled, or the result can be anything.
    Also allow all types in let-rec expressions on the level of syntax. Semantically cyclic Boolean expressions can be detected and rejected later.
    Keep all restrictions of the SVA standard (although not all of them might be strictly necessary). ::


    <top_property> = <property> | (prop-disable-iff <bool> <property>)
    <property> = (<property_operation> <argument1> <argument2> ...)

**Example operations:** ``and, implication, until, always, disable-iff, accept-on``

.. code-block:: sexpr

    (prop-seq <sequence>)		convert sequence to sequence property

    (prop-bool <bool>)		convert Boolean expression to property
    === (prop-seq (seq-bool <bool>))

    (prop-and <property1> <property2> ...)

    (prop-non-overlapped-implication <sequence> <property>)

    (prop-until <property1> <property2>)

    (prop-always <property)

    (prop-accept-on <bool> <property>)




Property Examples:
^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (prop-non-overlapped-implication
    (seq-concat (seq-bool a) (seq-bool b))
    (prop-always (prop-bool c)))

    (until
    (prop-not (prop-seq (seq-concat (seq-bool a) (seq-bool b))))
    (prop-seq (seq-and (seq-bool c) (seq-bool a)))

    (always
    (range 4 $)
    (prop-seq (seq-bool (not b))))

Recursive property
""""""""""""""""""""

See recursion ``(let-rec)`` above.

Several restrictions apply to recursive properties:
``prop-not`` cannot be applied to a recursive property, no ``disable-iff`` in
recursive property, advance in time before reinstantiation, restrictions on
arguments of recursive properties (these will be checked by Verific beforehand)


Example:

.. code-block:: sexpr

    (let-rec (prop1
    (prop-and
    (prop-bool a)
    (prop-non-overlapped-implication (seq-bool true) prop1)))
    prop1)

Mutually recursive properties

.. code-block:: sexpr

    (let-rec
        (prop1 (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool true) prop2))
        (prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool true) prop1))
    prop1)


Statement form:

.. code-block:: sexpr

    (declare-rec
    (prop1 (prop-and
    (prop-bool a)
    (prop-non-overlapped-implication (seq-bool true) prop2)))
    (prop2 (prop-and
    (prop-bool b)
    (prop-non-overlapped-implication (seq-bool true) prop1))))
    (assert-property prop1)


Example for graph (Verific output or automaton) -> ``let-rec``

.. code-block:: sexpr

    (let-rec
    	(node1 (<operation-of-node-1> <name-of-first-arg-node> ...))
    	(node2 (<operation-of-node-2> <name-of-first-arg-node> ...))
    ...
    <root-or-initial-state-or-whatever>)


Automaton
^^^^^^^^^^

.. code-block:: sexpr

    <state> = (<sort-of-state> [<bool>] <child1> <child2> ... )

    <child> = <state>

    <sort-of-state> = state-or | state-and | state-followed-by | state-as-long-as | state-next | state-immediate


States:

.. code-block:: sexpr

    (state-immediate <bool>)

Check the boolean expression and enter an implicit accepting sink

..
    Question: Regarding the acceptance condition, would this not mean that the
    computation of the whole automaton succeeds, because an accepting state is seen infinitely often?
    Question: implicit accepting sink = sink has self-loop? Why is it called implicit?

.. code-block:: sexpr

    (state-next <state>)

Go to the successor state and read one (any) input symbol

.. code-block:: sexpr

    (state-or <child1> <child2> ... )

Disjunctive / existential state

.. code-block:: sexpr

    (state-and <child1> <child2> ... )
Conjunctive / universal state

.. code-block:: sexpr

    (state-as-long-as <child1> <child2>)

Used for disable iff
As long as the child1 automaton does not reject, run the child2 automaton

.. code-block:: sexpr

    child1 = (automaton-representation-of (not <bool_disable_iff_condition>))

.. code-block:: sexpr

    (state-followed-by <if_child1> <if_child2> ... <then_followed_by_child>)

Used for sequence intersection + concatenation
All if_child successors need to accept simultaneously to start the computation of the then_followed_by_child successor


Guarded next:

.. code-block:: sexpr

    (state-guarded-next <bool> <child>)
    === (state-and (state-immediate <bool>) (state-next <child>))

Works like a standard transition that checks a condition and enters the next state

.. Question: Is the rewriting correct?


..
    Features:
    DAGs: use declare
    Loops, self-loops: use let-rec or declare-rec
    Universal and existential states state-or and state-and
    Epsilon transitions: expressed by universal/existential states, which can have a single child
    Transitions labeled by Boolean expressions immediate(c)
    Initial and final states
    Go to state q for every possible input symbol: next(q)
    Followed-by, as-long-as


Examples:

.. code-block:: sexpr

    (declare q4 (state-immediate a))
    (declare q5 (state-immediate b))
    (declare q1 (state-or q4 (state-and q5)))

    (declare-rec (q1 (state-and q1 (state-immediate a))) )

    (let-rec
    (q1 (state-and q1 (state-immediate (state-and b (not c))) )))

    (let-rec
    	(q1 (state-and (state-immediate a) q2)
    	(q2 (state-or q2 q1))
    q1)

    (state-guarded-next (and a (not b)) q2)
    or
    (state-and
    	(state-immediate (and a (not b)))
    		(state-next q2)))




Circuit
^^^^^^^^

TODO