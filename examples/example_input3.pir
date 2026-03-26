(document
    (add-signals a b)
    (declare-rec
        (declare prop1 (prop-and
            (prop-bool a)
            (prop-non-overlapped-implication (seq-bool (true)) prop2)))
        (declare prop2 (prop-and
            (prop-bool b)
            (prop-non-overlapped-implication (seq-bool (true)) prop1)))))