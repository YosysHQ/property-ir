Syntax
-----------------

.. role:: sexpr(code)
   :language: sexpr

.. role:: systemverilog(code)
   :language: systemverilog


We will now come to the more formal part of the Property IR specification,
starting with the syntax of expressions and statements.
While we have already seen many of the following features in the introduction,
here we provide a comprehensive description.



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
provided that it has the correct type.

Recursive form
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (let-rec
        (<identifier1> <expr1>)
        (<identifier2> <expr2>)
        ...
        <return_expression>)

The :sexpr:`let-rec` expression can be used to model cycles and (mutual) recursion.
The identifiers bound in a :sexpr:`let-rec` expression can only be accessed locally,
either inside any of the named subexpressions (including the same and earlier ones),
or in the return expression.
Note that it is not possible to bind literals to identifiers,
for example :sexpr:`(declare n 5)` and :sexpr:`(let-rec (c true) (constant c))` are forbidden.
:sexpr:`let-rec` expressions can appear anywhere where expressions are allowed,
provided that they have the correct type. The type of a :sexpr:`let-rec` expression is
the type of its return expression.
They can be nested, but
reusing identifiers in nested :sexpr:`let-rec` expressions,
and reusing identifiers that are declared previously via a
:ref:`declare statement <declare statements>`,
is forbidden, i.e., *shadowing* is forbidden.

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

    * ``not`` and the strong operators ``s_nexttime``, ``s_eventually``,
      ``s_always``, ``s_until``, and ``s_until_with`` can not be applied to
      recursive properties (or to properties instantiating recursive properties)
    * no ``disable-iff`` in recursive properties
    * advance in time before reinstantiation
    * restrictions on arguments of recursive properties

    On the level of syntax, Property IR allows the use of recursive expressions
    (:sexpr:`let-rec`) and recursive declarations (:sexpr:`declare-rec`) regardless of the type.
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
identifier in a :sexpr:`let-rec` expression appearing later or nested inside the same
declare statement.
However, it is possible to first use an identifier locally inside a :sexpr:`let-rec`
expression and then declare it later.


.. note::

    Any string may be used as an identifier, including the empty string and
    primitive symbols. This facilitates integration with other tools.
    Since the first element of each list in an expression is a primitive and all
    other elements are arguments, expressions can be parsed unambiguously.




Expression declaration
""""""""""""""""""""""""""""""

.. code-block:: sexpr

    (declare <identifier> <expr>)

With the :sexpr:`declare` keyword, an expression can be bound to an identifier.
The type of the identifier is the type of the expression.
:sexpr:`<expr>` must not contain the identifier.


Recursive declaration
"""""""""""""""""""""""""

The :sexpr:`declare-rec` statement allows to declare several identifiers at once
that can be used immediately in each of the named subexpressions.
This allows to model cycles and (mutual) recursion, where several of the
involved primitives shall be referred to in later statements.
The named subexpressions can appear in any order without affecting semantics.

The optional :sexpr:`declare` keyword at the beginning of a named subexpression
will make the identifier available globally in any later statement, while
omitting it makes the identifier available only locally inside the :sexpr:`declare-rec`
statement.

Note that the named subexpression with the :sexpr:`declare` keyword is semantically
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
``foo`` does not use the :sexpr:`declare` keyword.


External input declaration
"""""""""""""""""""""""""""

Signals that are handled outside of Property IR, but referred to in statements,
need to be declared using the :sexpr:`declare-input` statement.
At the moment only one-bit signals are supported.

.. code-block:: sexpr

    (declare-input <identifier> <type>)


Note that signal values ``x`` and ``z`` do not exist inside Property IR, and
are interpreted as false (as usual in SystemVerilog in a purely
Boolean context, like in ``if`` conditions).




Assertion Statements
^^^^^^^^^^^^^^^^^^^^^^^^^^

Assert, assume, and restrict
"""""""""""""""""""""""""""""""


The following directives correspond to the respective assertion statements in SVA.
The ``assert`` directive is used to verify that a property is satisfied,
with the solver either showing that it is always true in the given design,
for all valid inputs, or finding a counterexample.
The directive ``assume`` is used to constrain the environment
to specific inputs to the design.
With ``restrict``, the search state can be constrained, for example to verify
only certain cases, but it is not expected that these restrictions are
necessarily always satisfied in the design.



.. code-block:: sexpr

    (assert-property <clk_prop> [:disable-iff <bool1>] [:enable <bool2>])

    (assume-property <clk_prop> [:disable-iff <bool1>] [:enable <bool2>])

    (restrict-property <clk_prop> [:disable-iff <bool1>] [:enable <bool2>])

There are two optional keyword parameters that may follow after the clocked
property in any order.



:sexpr:`:disable-iff`
    If the *disable condition* is true anytime during the
    evaluation attempt of the assertion, the assertion is disabled
    asynchronously and the evaluation attempt yields no result.

:sexpr:`:enable`
    The *enabling condition* states whether a procedural concurrent assertion is active.
    For example, a procedural concurrent assertion that is located inside an
    ``if`` block is only evaluated if the ``if`` condition is true
    (see Table :ref:`Assertions <Assertions>`).


While the disable condition controls whether an evaluation attempt yields a result,
the enabling condition controls whether an evaluation attempt is performed.

.. note::

    According to the SystemVerilog standard, the disable condition must not
    reference local variables or the ``matched``
    function (``triggered`` is allowed). Except for ``$sampled``,
    if a sample value function is used, an explicit clock must be provided to
    the function.
    Note that these functions need to be handled outside of Property IR.

Cover
"""""""

The ``cover`` directive checks whether the property is satisfiable.
In other words, it succeeds if there exists a combination of inputs
that has a trace fulfilling the specified
property (or matching the sequence)
at least once.

A property passes *vacuously* if the reason that it is satisfied is that
the precondition is not fulfilled. For example, the implication ``a |-> b``
is vacuously satisfied when ``a`` is false.  In order to activate
nonvacuous satisfaction, where the cover statement only succeeds if
is passes nonvacuously, the :sexpr:`cover-property` and :sexpr:`cover-sequence`
statements have an additional keyword parameter :sexpr:`:mode` with three
different options (see explanation below).

.. code-block:: sexpr

    <mode> ::= satisfied | nonvacuously-satisfied | nonvacuous

As defined by the SystemVerilog standard, there exist two cover statements:
While :sexpr:`cover-sequence` counts all matches per evaluation attempt,
:sexpr:`cover-property` counts only one match per evaluation attempt.
Since we do not count matches internally, the result of these two directives
will be the same, with the only difference being the provided type.

.. code-block:: sexpr

    (cover-property  <clk_prop> [:disable-iff <bool1>] [:enable <bool2>] [:mode <mode>])

    (cover-sequence  <clk_prop> [:disable-iff <bool1>] [:enable <bool2>] [:mode <mode>])


:sexpr:`:mode`
    :sexpr:`satisfied`
        Default mode. Succeeds also when vacuously satisfied.
    :sexpr:`nonvacuously-satisfied`
        Succeeds only when nonvacuously satisfied.
    :sexpr:`nonvacuous`
        Checks if the evaluation is vacuous, regardless of failure or success.

The option :sexpr:`nonvacuous` can be used to define a precondition cover
of an asserted property as follows.

.. code-block:: sexpr

    (assert-property <clk_prop>) ; finds non-satisfying traces
    (cover-property <clk_prop> :mode nonvacuous) ; ensures there are some nonvacuous traces


.. note::

    Note that the default ``cover`` settings for many simulators correspond to
    :sexpr:`(cover-property <clk_prop> :mode nonvacuously-satisfied)`.
    We choose a different approach by using the possibly vacuous satisfaction
    :sexpr:`(cover-property  <clk_prop> :mode satisfied)` as a default.



Trigger sequence
""""""""""""""""""

The additional directive :sexpr:`trigger-sequence` does not have a corresponding
SVA statement, and is used to declare an output bit that is high in each time step
that the sequence matches, and low otherwise.

.. code-block:: sexpr

    (trigger-sequence <clk_seq> [:disable-iff <bool1>] [:enable <bool2>])


.. note::

    The directive :sexpr:`trigger-sequence` should
    not be confused with the extended Boolean ``triggered`` function, that
    evaluates to true when the provided sequence matches. However, the
    :sexpr:`trigger-sequence` directive can be used to implement the
    ``triggered`` and ``matched`` function.

Notes
""""""

* In order to use an assertion inside an ``initial`` block,
  use the :sexpr:`initial` Boolean expression primitive that is high only in the
  first time step.

* Assertion statements in SVA may contain a clocking event.
  Property IR does not provide this option because it is semantically equivalent
  to adding the clock directly to the property.

* In order to apply assertions to simple sequences or simple properties,
  use the primitives :sexpr:`clk-seq-seq` and :sexpr:`clk-prop-prop`, respectively,
  to convert them to the clocked variants first.



