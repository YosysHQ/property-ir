Abstract Syntax
-----------------

**Keywords:** ``declare``, ``declare-input``, ``let-rec``

``assert-property``, ``cover-property``, ``assume-property``, ``restrict-property``

Function Symbols: all SVA operators, types of automata states, circuit primitives

Types:

* Boolean: true, false
* Integer: 0, 1, …
* Bounded Range: (n m) with n <= m
* Constant Range: (n m) with n <= m or m=$
* Boolean Expression
* Sequence
    * clocked or simple/unclocked
* Property
    * clocked or unclocked
* AutomataState


Each operation symbol has as a prefix the sort that it returns (except for ``bool``). Top-level statements do not return anything.

Top-level Statements
~~~~~~~~~~~~~~~~~~~~~~

Unlike other expressions, the following do not have a return value.

.. code-block:: sexpr

    (assert-property <property_expr>)
    (cover-property <property_expr>)
    (assume-property <property_expr>)
    (restrict-property <property_expr>)

Declare

.. code-block:: sexpr


    (declare <identifier> <sort> <expr>)

What is defined in declare can be accessed from everywhere inside the property IR “document”.
Recursion
Expression form (not top-level command, has a return value):

.. code-block:: sexpr

    (let-rec
    (<identifier1> <sort1> <expr1>)
    (<identifier2> <sort2> <expr2>)
    …
    <return_value>)

The identifiers in the let-rec expression can only be accessed inside the expression.

Statement form (can be accessed from everywhere, no return value):

.. code-block:: sexpr

    (declare-rec
    (<identifier1> <sort1> <expr1>)
    (<identifier2> <sort2> <expr2>)
    ...)



Declaring something external
This is used for expressions that are  handled outside of property IR.

.. code-block:: sexpr

    (declare-input <identifier> <sort>)

Example:

.. code-block:: sexpr

    (declare-input a bool) ; bool may be optional if we only use this for “atomic” propositions
    (declare-input addr (bitvec 8)) ; maybe not, unsure about local variables

