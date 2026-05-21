(document
    (declare-input a)
    (declare-input b)
    (declare-rec (declare p
            (prop-not (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)))
                (prop-not (prop-and (prop-weak-bool b) p))))))
    (parse-sexpr p)
)