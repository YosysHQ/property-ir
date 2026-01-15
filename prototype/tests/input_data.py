



expr1 =  '(or (and a b) (not (and (not a) c)) d)'

expr2 = """(seq-concat
                        (seq-repeat (range 5 5) (seq-bool a))
                        (seq-concat (seq-bool b) (seq-bool c)))"""

expr3 = """(prop-always-ranged
                        (range 4 $)
                        (prop-seq (seq-bool (not b))))"""

expr4 = """(prop-always (prop-and
                        (prop-seq (seq-bool (not b)))
                        (prop-seq (seq-bool a))
                    ))"""

expr5 = """(let-rec
        (foo (and a bar))
        (bar (or b c))
        foo
    )"""

expr6 = """(let-rec
                (prop1 (prop-and
                    (prop-seq (seq-bool a))
                    (prop-non-overlapped-implication (seq-bool (constant true)) prop2)))
                (prop2 (prop-and
                    (prop-seq (seq-bool a))
                    (prop-non-overlapped-implication (seq-bool (constant true)) prop1)))
                prop1)"""



expr7 = """(let-rec
        (q1 (seq-concat (seq-bool a) q3))
        (q2 (seq-concat (seq-bool b) q4))
        (q3 q4)
        (q4 (seq-bool c))
        (q5 q3)
        (seq-concat (seq-bool d) q5)
    )"""

expr8 = """(let-rec
        (q1 (and a b))
        (q2 (let-rec
                (p1 (not q1))
                (p2 q1)
                (p3 (or q2 c))
                p3))
        q2)"""

expr9 = """(let-rec
        (foo2 (and a bar2))
        (bar2 (seq-concat (seq-bool a) (seq-bool b)))
        foo2)"""







tokenized1 =  ['or', ['and', 'a', 'b'], ['not', ['and', ['not', 'a'], 'c']], 'd']

tokenized2 = ['seq-concat',
                        ['seq-repeat', ['range', 5, 5], ['seq-bool', 'a']],
                        ['seq-concat', ['seq-bool', 'b'], ['seq-bool', 'c']]]

tokenized3 = ['prop-always-ranged',
                        ['range', 4, '$'],
                        ['prop-seq', ['seq-bool', ['not', 'b']]]]

tokenized4 = ['prop-always', ['prop-and',
                        ['prop-seq', ['seq-bool', ['not', 'b']]],
                        ['prop-seq', ['seq-bool', 'a']]
                    ]]

tokenized5 = ['let-rec',
        ['foo', ['and', 'a', 'bar']],
        ['bar', ['or', 'b', 'c']],
        'foo'
    ]

tokenized6 = ['let-rec',
                ['prop1', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop2']]],
                ['prop2', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop1']]],
                'prop1']

tokenized7 = ['let-rec',
        ['q1', ['seq-concat', ['seq-bool', 'a'], 'q3']],
        ['q2', ['seq-concat', ['seq-bool', 'b'], 'q4']],
        ['q3', 'q4'],
        ['q4', ['seq-bool', 'c']],
        ['q5', 'q3'],
        ['seq-concat', ['seq-bool', 'd'], 'q5']
    ]

tokenized8 = ['let-rec',
        ['q1', ['and', 'a', 'b']],
        ['q2', ['let-rec',
                ['p1', ['not', 'q1']],
                ['p2', 'q1'],
                ['p3', ['or', 'q2', 'c']],
                'p3']],
        'q2']

