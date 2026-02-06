



from sexpr.base import RawSExpr


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







raw_sexpr1 =  ['or', ['and', 'a', 'b'], ['not', ['and', ['not', 'a'], 'c']], 'd']

raw_sexpr2 = ['seq-concat',
                        ['seq-repeat', ['range', '5', '5'], ['seq-bool', 'a']],
                        ['seq-concat', ['seq-bool', 'b'], ['seq-bool', 'c']]]

raw_sexpr3 = ['prop-always-ranged',
                        ['range', '4', '$'],
                        ['prop-seq', ['seq-bool', ['not', 'b']]]]

raw_sexpr4 = ['prop-always', ['prop-and',
                        ['prop-seq', ['seq-bool', ['not', 'b']]],
                        ['prop-seq', ['seq-bool', 'a']]
                    ]]

raw_sexpr5 = ['let-rec',
        ['foo', ['and', 'a', 'bar']],
        ['bar', ['or', 'b', 'c']],
        'foo'
    ]

raw_sexpr6 = ['let-rec',
                ['prop1', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop2']]],
                ['prop2', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop1']]],
                'prop1']

raw_sexpr7 = ['let-rec',
        ['q1', ['seq-concat', ['seq-bool', 'a'], 'q3']],
        ['q2', ['seq-concat', ['seq-bool', 'b'], 'q4']],
        ['q3', 'q4'],
        ['q4', ['seq-bool', 'c']],
        ['q5', 'q3'],
        ['seq-concat', ['seq-bool', 'd'], 'q5']
    ]

raw_sexpr8 = ['let-rec',
        ['q1', ['and', 'a', 'b']],
        ['q2', ['let-rec',
                ['p1', ['not', 'q1']],
                ['p2', 'q1'],
                ['p3', ['or', 'q2', 'c']],
                'p3']],
        'q2']




raw_sexpr6_declare = ['declare', 'global-node-name1', raw_sexpr6]

raw_sexpr6_declare_rec = ['declare-rec',
                ['declare', 'prop1', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop2']]],
                ['declare', 'prop2', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop1']]],
                ]


raw_sexpr5_declare_rec = ['declare-rec',
        ['declare', 'foo', ['and', 'a', 'bar']],
        ['declare', 'bar', ['or', 'b', 'c']],
    ]


raw_sexpr7_declare_rec = ['declare-rec',
        ['declare', 'q1', ['seq-concat', ['seq-bool', 'a'], 'q3']],
        ['q2', ['seq-concat', ['seq-bool', 'b'], 'q4']],
        ['q3', 'q4'],
        ['declare', 'q4', ['seq-bool', 'c']],
        ['q5', 'q3'],
        ['declare', 'p', ['seq-concat', ['seq-bool', 'd'], 'q5']]
    ]

raw_sexpr_signal_redeclaration_local = ['let-rec',
    ['q1', 'a'],
    'q1'
    ]

raw_sexpr_signal_redeclaration_global1: RawSExpr = ['declare', 'q1', 'a']

raw_sexpr_signal_redeclaration_global2 = ['declare-rec',
    ['declare', 'q1', 'a'],
    ]

