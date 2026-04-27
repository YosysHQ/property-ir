:orphan:

Internal Primitives
----------------------

The following primitives are used internally during the verification flow.


Automaton
^^^^^^^^^^

TODO

.. code-block:: sexpr

    <state> = (<sort_of_state> [<bool>] <child1> <child2> ... )

    <child> = <state>

    <sort_of_state> = state-or | state-and | state-followed-by | state-as-long-as | state-next | state-immediate


States:

.. code-block:: sexpr

    (state-immediate <bool>)

Check the boolean expression and enter an implicit accepting sink


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


Automata Examples
"""""""""""""""""""

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