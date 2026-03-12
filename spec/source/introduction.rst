
Introduction
-------------

.. role:: sexpr(code)
   :language: sexpr

Property IR is an intermediate representation for temporal properties as
specified by SystemVerilog Assertions (SVA).
The goal is to support formal verificaton flows, while decoupling front-end
tasks like parsing, name resolution, etc. from checker circuit synthesis and
optimization.
This is achieved by providing a unified representation for SVA assertions,
automata, and circuits.

This document focuses on the public interface of Property IR, that is, the part
relevant to someone who wants to construct Property IR expressions from SVA.
For more information on representations later in the verification flow
and other implementation details, see ...


General Concept
^^^^^^^^^^^^^^^^

The syntax of the Property IR expressions is based on s-expressions (*symbolic expressions*).
This is a notation for expressions in the form of nested lists, with
the first element of a list representing an operation, and the subsequent
elements representing its arguments (each being either atomic or a list again).

.. code-block:: sexpr

    (mul 5 (add 2 3))

*Note: Example for illustrative purposes only. These operations are
not part of Property IR.*

The operations of Property IR are called *primitives*. Each primitive has
a *signature*, consisting of its *argument types*
and its *return type* (or simply *type*).
Property IR expressions are *well-typed*, having distinct types for example
for boolean expressions, sequences, and temporal properties
(and internally used types for automata and circuits).
When specifying the signature of primitives in this document, we write
parameters enclosed in angle brackets
(e.g., :sexpr:`<seq>`), which needs to be replaced by an expression with the correct
type to yield a valid expression.
The (return) type of the first element (or *root*) of an expression is also the
(return) type of the whole expression.

Consider overlapped implication (``seq |-> prop`` in SVA) as an example primitive.
It expects two arguments having the types sequence (``seq``) and property (``prop``),
and returns a property (indicated by the prefix ``prop-`` of the primitive).

.. code-block:: sexpr

    (prop-overlapped-implication <seq> <prop>)

Property IR provides primitives that closely match the operators of SVA,
which allows for a direct syntactic translation of elaborated SVA.
Note that parameterized sequences and properties can not be represented, and
the frontend needs to instantiate them with concrete arguments before they can
be translated to Property IR expressions.
Let us consider for example the following SystemVerilog property.

.. code-block:: systemverilog

    property p;
        a ##1 b |-> always(c);
    endproperty

It corresponds to the following Property IR expression.

.. code-block:: sexpr

    (declare p
        (prop-overlapped-implication
            (seq-concat (seq-bool a) (seq-bool b))
            (prop-always (prop-bool c))))

The signals ``a``, ``b``, and ``c`` have type ``bool``.
Concatenation (:sexpr:`seq-concat`) expects arguments of type ``seq``, therefore
:sexpr:`seq-bool` is used to convert the signals to sequences of length 1.
Similarly, :sexpr:`prop-bool` converts signal ``c`` to a sequence property,
because :sexpr:`prop-always` requires an argument of type ``prop``.
With :sexpr:`declare` we can bind expressions to identifiers to reference them later.

Expressions can be regarded as an expression graph, and this is also how they
are stored and processed internally.
In this graph, the *nodes* are primitives in the case of internal nodes, and
external signals or literals (like integers or ranges) in the case of leaf nodes.
The *edges* are connections between nodes, pointing from primitives as
parents to their arguments as children.

.. figure:: /_images/spec_exp1.svg
    :class: width-helper invert-helper
    :name: spec_exp1

    expression graph of ``p``

Different from the classical s-expressions in the strict sense,
Property IR provides a syntax to represent cycles by naming
and referencing nodes.
Using this feature, recursive properties like the following
(which is equivalent to ``always(a)``) can be expressed.

.. code-block:: systemverilog

    property always_a;
        a and (1'b1 |=> always_a);
    endproperty


.. code-block:: sexpr

    (declare-rec
        (declare always_a
            (prop-and
                (prop-bool a)
                (prop-non-overlapped-implication
                    (seq-bool (constant true))
                    always_a))))


.. figure:: /_images/spec_exp2.svg
    :class: width-helper invert-helper
    :name: spec_exp1

    expression graph of ``always_a``


Similarly, mutually recursive properties can be expressed.

.. code-block:: systemverilog

    property prop1;
        a and (1'b1 |=> prop2);
    endproperty

    property prop2;
        b and (1'b1 |=> prop1);
    endproperty


.. code-block:: sexpr

    (declare-rec
        (declare prop1 (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool (constant true)) prop2)))
        (declare prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool (constant true)) prop1))))


.. figure:: /_images/spec_exp3.svg
    :class: width-helper invert-helper
    :name: spec_exp1

    expression graph of ``prop1`` and ``prop2``


The same syntax will also be used to represent cycles in the automata or
checker circuit representations of properties in later steps of the verification flow.


Embedding in Yosys
^^^^^^^^^^^^^^^^^^^^^^

Property IR embeds into RTLIL via a new ``$property`` cell that stores
the textual Property IR code in a parameter.
One ``$property`` cell may contain several assertions, which enables optimizations
that were else not possible. We call the contents of one ``$property`` cell
a Property IR *document*.
The ``$property`` cell takes a parametric number of input bits and produces a
parametric number of output bits.
The meaning of individual bits is declared as part of the embedded
Property IR code and can include:

* observed signals of the design as inputs
* checker status of properties as outputs
* sequence matches as outputs

Note that ``x`` and ``z`` do not exist inside Property IR, and
are interpreted as ``false`` (as usual in SystemVerilog in a purely
Boolean context, like ``if`` conditions).

There are certain SystemVerilog expressions that can be used in SystemVerilog
assertions but can not be represented in Property IR.
This concerns the *extended Booleans*, including sampled value functions like
``$past``, ``$rose`` etc. and
the ``matched`` and ``triggered`` functions.
The reason is that Property IR expects *time-variable Booleans* as input,
that is, functions from time to Boolean. Allowing ``$past`` and similar
operators would deviate from this stateless notion of input.


Extended Boolean expressions need to be synthesized outside of Property IR, and
the output signals of the synthesized circuits become input signals of the
``$property`` cell. Then they are treated like any other Boolean input inside Property IR.

.. note::

    TODO: a few notes on local variables

    * local variable assignments as inputs
    * local variable values as outputs (undefined if used outside of local
      variable assignments)

.. note::

    Future revisions of Property IR might include native support for some of these
    functions.


.. code-block:: systemverilog

    property prop;
        $rose(b) |-> always(a);
    endproperty

In this example, let signal ``rose_b`` be the output of the circuit that was
synthesized for ``$rose(b)`` and becomes an input for a ``$property`` cell.
(For simplicity, we omitted the declaration of inputs in previous examples.)

.. code-block:: sexpr

    (declare-input a)
    (declare-input rose_b)
    (declare prop (prop-overlapped-implication (seq-bool rose_b) (prop-bool a)))


Registering properties for FV continues to use the existing ``$check`` cell
(or the lower level ``$assert``, ``$assume``, etc. cells).
The synthesis of checker circuits will be done in multiple passes with
intermediate results representable as Property IR.

The MLIR dialect for RTLIL will be extended to represent Property IR in order
to ensure interoperability with CIRCT.

