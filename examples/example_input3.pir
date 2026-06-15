(document
    (declare-input a)
    (declare-input b)
    (declare-rec
        (declare prop1 (prop-and
            (prop-weak-bool a)
            (prop-non-overlapped-implication (seq-bool (true)) prop2)))
        (declare prop2 (prop-and
            (prop-weak-bool b)
            (prop-non-overlapped-implication (seq-bool (true)) prop1)))))