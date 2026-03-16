Syntax
-----------------

.. role:: sexpr(code)
   :language: sexpr

.. role:: systemverilog(code)
   :language: systemverilog


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

Identifier form
^^^^^^^^^^^^^^^^^^

An identifier that is declared previously via a
:ref:`declare statement <declare statements>` is a valid
expression and can appear anywhere where expressions are allowed,
given that it has the correct type.

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
Note that it is not possible to bind literals to identifiers.
``let-rec`` expressions can appear anywhere where expressions are allowed,
given that they have the correct type. The type of a ``let-rec`` expression is
the type of its return expression.
They can be nested, but
reusing identifiers in nested ``let-rec`` expressions,
and reusing identifiers that are declared previously via a
:ref:`declare statement <declare statements>`,
is forbidden, i.e., *shadowig* is forbidden.

Moreover, it is forbidden to define circular references of identifiers
involving no primitives, like in the following example.

.. code-block:: sexpr

    (let-rec
        (identifier1 identifier2)
        (identifier2 identifier1))

.. note::

    SVA allows recursion only for properties, and
    several restrictions apply to them
    (that are expected to be checked by the frontend that reads Verilog):

    * ``prop-not`` can not be applied to recursive properties
    * no ``disable-iff`` in recursive properties
    * advance in time before reinstantiation
    * restrictions on arguments of recursive properties

    On the level of syntax, Property IR allows the use of recursive expressions
    (``let-rec``) and recursive declarations (``declare-rec``) regardless of the type.
    However, there might not exist a useful or unambiguous fixpoint, and these
    cases are rejected later during the verification flow,
    keeping all restrictions of the SV standard.


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
Recall that it is not possible to bind literals to identifiers.
An identifier that is declared once may not be redeclared later or used as an
identifier in a ``let-rec`` expression appearing later or nested inside the same
declare statement.
However, it is possible to first use an identifier locally inside a ``let-rec``
expression and then declare it later.


.. note::

    Any string may be used as an identifier, including the empty string and
    primitive symbols. This facilitates integration with other tools.
    Since the first element of each list in an expression is a primitive and all
    other elements are arguments, expressions can be parsed unambiguously.

.. Globally declared identifiers may not be redeclared, and also not used as local
.. identifiers later in a document. Nested ``let-rec`` may not reuse identifiers,
.. i.e., *shadowig* is forbidden.




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

TODO: what types should be available here? only one-bit signal for now?

Example:

.. code-block:: sexpr

    (declare-input a bool) ; bool may be optional if we only use this for “atomic” propositions
    (declare-input addr (bitvec 8)) ; maybe not, unsure about local variables


.. TODO: more information on this, and reference to the $property cell


Assertion Statements
^^^^^^^^^^^^^^^^^^^^^^^^^^

These directives correspond directly to the respective assertion statements in SVA.

.. code-block:: sexpr

    (assert-property <bool1> <bool2> <bool3> <clk_prop>)

    (cover-property <bool1> <bool2> <bool3> <clk_prop>)
    (cover-sequence <bool1> <bool2> <bool3> <clk_seq>)

    (assume-property <bool1> <bool2> <bool3> <clk_prop>)

    (restrict-property <bool1> <bool2> <bool3> <clk_prop>)



The :sexpr:`<bool1>` parameter is the *disable condition* (``disable iff``).
If no disable condition is used, it should be set to
:sexpr:`(constant false)` or :sexpr:`(false)`.
Provided that a disable condition is used, if it is true anytime during the
evaluation attempt of the assertion, the assertion is disabled asynchronously and
the evaluation attempt yields no result.

.. note::

    The disable condition must not reference local variables or the ``matched``
    function (``triggered`` is allowed). Except for ``$sampled``,
    if a sample value function is used, an explicit clock must be provided to
    the function.
    Note that these functions need to be handled outside of Property IR.


TODO: More informatio on disable iff

The :sexpr:`<bool2>` parameter is the *trigger condition*.
It states whether the assertion is active. For example, an assertion might be
located inside an ``if`` block and thus depend on the if
condition to be true.
Note how this is different from the disable condition.

The :sexpr:`<bool_literal>` parameter is the *vacuity bit*.
A property passes *vacuously* if the reason that it is satisfied is that
the precondition is not fulfilled. For example, the implication ``a |-> b``
is vacuously satisfied when ``a`` is false.
If this parameter is set to :sexpr:`true`, ...


The additional directive :sexpr:`trigger-sequence` does not have a corresponding
SVA operation, and is used to declare an output bit that is high in each time step
that the sequence matches, and low else.

.. code-block:: sexpr

    (trigger-sequence <bool1> <bool2> <bool3> <clk_prop>)


In order to use an assertion inside an ``initial`` block,
use the :sexpr:`initial` primitive that is high only in the first time step.

Assertion statements in SVA may contain a clocking event.
Property IR does not provide this option because it is semantically equivalent
to adding the clock directly to the property.

As defined by the SystemVerilog standard, there exist two cover statements:
While :sexpr:`cover-sequence` counts all matches per evaluation attempt,
:sexpr:`cover-property` counts only one match per evaluation attempt.
Since we do not count matches internally, the result of these two directives
will be the same, with the only difference being the provided type.

.. note::

    The trigger condition and the directive :sexpr:`trigger-sequence` should
    not be confused with the extended Boolean ``triggered`` function, that
    evaluates to true when the provided sequence matches. However, the
    :sexpr:`trigger-sequence` directive can be used to implement the
    ``triggered`` and ``matched`` function.

There exist variants of each of the directives that take simple sequences resp.
properties as parameters.

.. code-block:: sexpr

    (assert-simple-property <bool1> <bool2> <bool_literal> <prop>)

    (cover-simple-property <bool1> <bool2> <bool_literal> <prop>)
    (cover-simple-sequence <bool1> <bool2> <bool_literal> <seq>)

    (assume-simple-property <bool1> <bool2> <bool_literal> <prop>)

    (restrict-simple-property <bool1> <bool2> <bool_literal> <prop>)

    (trigger-simple-sequence <bool1> <bool2> <bool_literal> <prop>)

ALTERNATIVE: wrapper for type conversion clk-seq-seq and clk-prop-prop
instead of more directives

TODO:

* a clock can be provided to an assertion statement - is this different from
    adding the clock to ``prop``?
* explain vacuity parameter
* explain disable iff

