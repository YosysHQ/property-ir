(document
    (declare-input a)
    (declare-input b)
    (declare-input c)
    (declare p
        (prop-overlapped-implication
            (seq-concat (seq-bool a) (seq-bool b))
            (prop-always (prop-bool c)))))