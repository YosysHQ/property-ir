(document
    (add-signals a b c)
    (declare p (let-rec
            (q1 (and a b))
            (q2 (let-rec
                    (p1 (not q1))
                    (p2 q1)
                    (p3 (or q2 c))
                    p3))
            q2)
    )
)