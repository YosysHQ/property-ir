(document
    (add-signals a b c d)
    (declare p (let-rec
            (q1 (seq-concat (seq-bool a) q3))
            (q2 (seq-concat (seq-bool b) q4))
            (q3 q4)
            (q4 (seq-bool c))
            (q5 q3)
            (seq-concat (seq-bool d) q5)))
)