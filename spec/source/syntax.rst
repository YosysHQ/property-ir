Syntax
-----------------


Types
~~~~~~~

Literal types
^^^^^^^^^^^^^^^

* Boolean literal: ``<bool_literal> = true | false``
* Non-negative integer: ``<int> = n`` with :math:`n \in \mathbb N_{0}`
* Bounded range: ``<bounded_range> = (bounded-range n m)`` with :math:`n,m \in \mathbb N_{0}` and :math:`n \leq m`
* Constant range: ``<range> = (range n m) | (range n $)`` with :math:`n,m \in \mathbb N_{0}` and :math:`n \leq m`



.. :math:`0 \leq n \leq m`

.. <bounded_range> = (bounded-range <integer1> <integer2>) with <integer1> <= <integer2>

.. <range> = (range <integer> $) | (range <integer1> <integer2>) with <integer1> <= <integer2>


Expression types
^^^^^^^^^^^^^^^^^

* Boolean Expression ``bool``
* Clocked Sequence ``clk-seq``
* Simple Sequence ``seq``
* Clocked Property ``clk-prop``
* Simple Property ``prop``
* Automata State
* Circuit




Expressions
~~~~~~~~~~~~~~

An expression has a return value and
can take one of three forms.

Primitive form
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (<primitive_symbol> <arg1> <arg2> ...)

An expression in primitive form consists of a primitive symbol and its arguments.
It is enclosed in parentheses.
Each primitive has a *signature* that determines the argument types
and the return type.
Each argument is either a literal or an expression.
Every instance of a type is allowed where an argument of that type is expected.


Recursive form
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (let-rec
        (<identifier1> <expr1>)
        (<identifier2> <expr2>)
        ...
        <return_expression>)

The ``let-rec`` expression can be used to model cycles and (mutual) recursion.
The identifiers bound in a ``let-rec`` expression can only be accessed locally,
either inside any of the named subexpressions (including the same and earlier ones),
or in the return expression.
(That is, the order of named subexpressions inside a ``let-rec`` expression can be changed without changing the semantics.)
``let-rec`` expressions can appear anywhere where expressions are allowed,
given that they have the correct type. The type of a ``let-rec`` expression is
the type of its return expression.
They can be nested, but
reusing identifiers in nested ``let-rec`` expressions,
and reusing identifiers that are declared previously via a declare statement,
is forbidden.


Identifier form
^^^^^^^^^^^^^^^^^^

An identifier that is declared previously via a declare statement is a valid
expression and can appear anywhere where expressions are allowed,
given that it has the correct type.


Statements
~~~~~~~~~~~~~

Statements do not have a return value.
They cannot be nested.
Several statements are organized in a Property IR *document*.
Note that the order of statements matters, as declared identifiers can only be
used inside later statements (except for recursive declarations, which
allow using declared identifiers immediately inside the same statement).



Declare Statements
^^^^^^^^^^^^^^^^^^^^^^^

Declare statements are used to bind expressions to identifiers that can
be referred to in later statements.
Any UTF-16 string may be used as an identifier.
An identifier that is declared once may not be redeclared later or used as an
identifier in a ``let-rec`` expression appearing later or nested inside the same
declare statement.
However, it is possible to first use an identifier locally inside a ``let-rec``
expression and then declare it later.



Expression declaration
""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (declare <identifier> <expr>)

With the ``declare`` keyword, an expression can be bound to an identifier.
The type of the identifier is the type of the expression.
``<expr>`` must not contain the identifier.


Recursive declaration
"""""""""""""""""""""""""

The ``declare-rec`` statement allows to declare several identifiers at once
that can be used immediately in each of the named subexpressions.
This allows to model cycles and (mutual) recursion, where several of the
involved primitives shall be referred to in later statements.
The named subexpressions can appear in any order without affecting semantics.

The optional ``declare`` keyword at the beginning of a named subexpression
will make the identifier available globally in any later statement, while
omitting it makes the identifier available only locally inside the ``declare-rec``
statement.

Note that the named subexpression with the ``declare`` keyword is semantically
different from the non-recursive declaration and is in itself not a statement.
(Recall that statements cannot be nested.)

.. code-block:: sexpr

    (declare-rec
        ([declare] <identifier1> <expr1>)
        ([declare] <identifier2> <expr2>)
        ...)

Example:

.. code-block:: sexpr

    (declare-rec
            (foo (and a bar))
            (declare bar (or b c)))

Only the identifier ``bar`` can be referred to outside this statement, since
``foo`` does not use the ``declare`` keyword.


External input declaration
"""""""""""""""""""""""""""

Signals that are handled outside of Property IR, but referred to in statements,
need to be declared using the ``declare-input`` statement.

.. code-block:: sexpr

    (declare-input <identifier> <type>)

Example:

.. code-block:: sexpr

    (declare-input a bool) ; bool may be optional if we only use this for “atomic” propositions
    (declare-input addr (bitvec 8)) ; maybe not, unsure about local variables


.. TODO: more information on this, and reference to the $property cell


Assertion Statements
^^^^^^^^^^^^^^^^^^^^^^^^^^

These directives correspond directly to the respective assertion statements in SVA.

.. code-block:: sexpr

    (assert-property <property_expr>)
    (cover-property <property_expr>)
    (assume-property <property_expr>)
    (restrict-property <property_expr>)
