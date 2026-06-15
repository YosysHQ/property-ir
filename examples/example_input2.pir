(document
    (declare-input a)
    (declare-rec
        (declare always_a
            (prop-and
                (prop-weak-bool a)
                (prop-non-overlapped-implication
                    (seq-bool (constant true))
                    always_a)))))