Examples
==========

Boolean Expression Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (and c a)

    (or (and a b) (not (and (not a) c)) d)

    (not (and (not a) c))



Simple Sequence Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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






Simple Property Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sexpr

    (prop-until
        (prop-not (prop-seq (seq-concat (seq-bool a) (seq-bool b))))
        (prop-seq (seq-and (seq-bool c) (seq-bool a))))

    (prop-always-ranged
        (range 4 $)
        (prop-seq (seq-bool (not b))))



.. Recursive property:
..
.. .. code-block:: sexpr
..
..     (let-rec (prop1
..         (prop-and
..             (prop-bool a)
..             (prop-non-overlapped-implication (seq-bool (true)) prop1)))
..         prop1)
..
.. Mutually recursive properties:
..
.. .. code-block:: sexpr
..
..     (let-rec
..         (prop1 (prop-and
..             (prop-bool a)
..             (prop-non-overlapped-implication (seq-bool (true)) prop2)))
..         (prop2 (prop-and
..             (prop-bool b)
..             (prop-non-overlapped-implication (seq-bool (true)) prop1)))
..     prop1)
..
..
.. Declaration form:
..
.. .. code-block:: sexpr
..
..     (declare-rec
..         (declare prop1 (prop-and
..             (prop-bool a)
..             (prop-non-overlapped-implication (seq-bool (true)) prop2)))
..         (declare prop2 (prop-and
..             (prop-bool b)
..             (prop-non-overlapped-implication (seq-bool (true)) prop1))))


