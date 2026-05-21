(document
    (declare-input a)
    (declare-input b)
    (declare-input c)
    (declare-input d)
    (declare p
        (prop-not (prop-and
        (prop-or (prop-weak-bool a) (prop-weak-bool b))
        (prop-and (prop-weak-bool c) (prop-weak-bool d)) )))
    (parse-sexpr p)
)