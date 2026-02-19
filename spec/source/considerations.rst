Design Considerations
-----------------------------


Clocking
~~~~~~~~~~

Clocks are handled by applying a rewriting pass to an expression to let it use
the global clock.
For sequences and properties, there are two expression types, respectively:
A clocked version and a *simple* version, which uses the global clock and does
not contain sequences admitting empty matches.
Different types are necessary because else rewriting of the clock would lead
to inconsistencies.


Empty Matches
~~~~~~~~~~~~~~~~

A separate rewriting pass removes the empty part of sequences in order
to exclude special cases.
This is possible because on the level of
properties, empty matches only play a role insofar that they
have an influence on non-empty sequences via concatenation.
In an overlapped implication, an empty match of the antecedent sequence does not
cause it to trigger.
According to the SV standard, the sequence expression of a sequential
property shall not admit an empty match.


(fewer primitives for simple sequences / simple properties?)



Recursion
~~~~~~~~~~~

SVA allows recursion only for properties, and
several restrictions apply to them
(that are expected to be checked by the frontend that reads Verilog):

* ``prop-not`` cannot be applied to a recursive property
* no ``disable-iff`` in recursive property
* advance in time before reinstantiation
* restrictions on arguments of recursive properties

On the level of syntax, Property IR allows the use of recursive expressions
(``let-rec``) and recursive declarations (``declare-rec``) regardless of the type.
However, there might not exist a useful or unambiguous fixpoint, and these
cases are rejected later,
keeping all restrictions of the SV standard.



Rewriting Passes
~~~~~~~~~~~~~~~~~~~

Rewriting passes are transformations of Property IR expressions.
They are defined outside of Property IR. It will be
possible to define them using a LHS in the form of a Property IR expression
to apply pattern matching, but their RHS may contain any logic that is not
necessarily expressible inside Property IR.

Macros/functions that perform some computation outside of Property IR are
written with ``#`` in the beginning, e.g. ``#admits-empty``.

At the moment it is not planned to provide a way inside Property IR to define
additional primitives.



Identifiers
~~~~~~~~~~~~~

Any UTF-16 string may be used as an identifier, including the empty string and
primitive symbols. This facilitates integration with other tools.
Since the first element of each list is a primitive and all other elements are
arguments, expressions can be parsed unambiguously.

Globally declared identifiers may not redeclared, and also not used as local
identifiers later. Nested ``let-rec`` may not reuse identifiers, i.e.,
*shadowig* is forbidden.

(is this really what we want?)




External Input
~~~~~~~~~~~~~~~~