
Introduction
-------------

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


.. The goal is to represent the following in a unified representation:

.. * SVA assertions (including recursive properties)
.. * Automata (can contain cycles)
.. * Circuits (can contain cycles)

.. Idea:
..
.. * use the syntax of s-expressions
.. * naming and referencing nodes for expressing cycles
.. * fixpoint semantics for recursive properties
..
.. Each operation or primitive is then defined based on its signature (argument types and return type)

General Concept
^^^^^^^^^^^^^^^^

The syntax of the Property IR expressions is based on s-expressions (*symbolic expressions*).
This is a notation for expressions in the form of nested lists, with
the first element of a list representing an operation, and the subsequent
elements representing its arguments (each being either atomic or a list again).
We can also regard operation and arguments as parent and children in a
tree-like structure.
For mathematical terms, this is also known as *Polish notation* or *prefix
notation*, and it is the principle that the Lisp programming language is based on.

.. code-block:: sexpr

    (mul 5 (add 2 3))

*Note: Example for illustrative purposes only. These operations are
not part of Property IR.*

The operations of Property IR are called *primitives*. Each primitive has
a *signature*, consisting of its *argument types*
and its *return type* (or simply *type*).
Consider overlapped implication (``seq |-> prop`` in SVA) as an example primitive.
It expects two arguments having the types sequence (``seq``) and property (``prop``),
and returns a property (indicated by the prefix ``prop-`` of the primitive).

.. code-block:: sexpr

    (prop-overlapped-implication <seq> <prop>)

Property IR expressions are *well-typed*, having distinct types for example
for boolean expressions, sequences, and temporal properties.
When describing primitives, we write parameters enclosed in angle brackets
(e.g., ``<seq>``), which needs to be replaced by an expression with the correct
type to yield a valid expression.
The (return) type of the first element (or *root*) of an expression is also the
(return) type of the whole expression.

.. meaning that the types of provided arguments need
.. to match with the type expected by the signature of the parent primitive at that
.. position, and that each expression with the correct type is acceptable as a
.. parameter.

Property IR provides primitives that closely match the operators of SVA,
which allows for a direct syntactic translation.
Consider for example the following SystemVerilog property.

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
Concatenation (``seq-concat``) expects arguments of type ``seq``, therefore
``seq-bool`` is used to convert the signals to sequences of length 1.
Similarly, ``prop-bool`` converts signal ``c`` to a sequence property of length 1,
because ``prop-always`` requires an argument of type ``prop``.
With ``declare`` we can bind expressions to identifiers to reference them later.

Expressions can be regarded as an expression graph, and this is also how they
are stored and processed internally.
In this graph, the *nodes* are primitives (or external signals, or literals)
and the *edges* are connections between nodes, pointing from primitives as
parents to their arguments as children.

TODO: image

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
                    (constant true)
                    always_a))))


TODO: image

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
            (prop-non-overlapped-implication (seq-bool (true)) prop2)))
        (declare prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool (true)) prop1))))

TODO: image


Application in Yosys
^^^^^^^^^^^^^^^^^^^^^^

external input

``$property`` cell






