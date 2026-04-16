:orphan:

Internal Rewriting Passes
----------------------------

Rewriting passes are transformations of Property IR expressions.
They are defined outside of Property IR. It will be
possible to define them using a LHS in the form of a Property IR expression
to apply pattern matching, but their RHS may contain any logic that is not
necessarily expressible inside Property IR.

At the moment it is not planned to provide a way inside Property IR to define
additional primitives.


.. Macros
.. ~~~~~~~~~
..
.. Macros are functions that perform some computation outside of Property IR.
.. They are written with the prefix ``#``.
.. Macros can be rewriting passes, but there can also be macros that do not return
.. expressions, e.g. ``#admits-empty`` returns ``true`` if a sequence admits an
.. empty match, and ``false`` else.
..
.. (list more macros? should this be part of the specification?)