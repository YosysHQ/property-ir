(document
    (declare-input a)
    (declare-input b)
    (declare-input c)
    (declare q (prop-not (prop-weak-bool c)))
    (declare p
            (prop-not (prop-overlapped-implication
                (seq-bool a)
                (prop-until (prop-weak-bool b) q)
            )))
    (parse-sexpr q)
    (parse-sexpr p)
)