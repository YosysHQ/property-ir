import pytest

from sexpr import parse_expression, tokenize, RawSExpr






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
                            (prop-non-overlapped-implication (seq-bool true) prop2)))
                        (prop2 (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool true) prop1)))
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
                    ['prop-non-overlapped-implication', ['seq-bool', 'true'], 'prop2']]],
                ['prop2', ['prop-and',
                    ['prop-seq', ['seq-bool', 'a']],
                    ['prop-non-overlapped-implication', ['seq-bool', 'true'], 'prop1']]],
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





tokenize_pairs = [(expr1, tokenized1),
    (expr2, tokenized2),
    (expr3, tokenized3),
    (expr4, tokenized4),
    (expr5, tokenized5),
    (expr6, tokenized6),
    (expr7, tokenized7),
    (expr8, tokenized8),
]



@pytest.mark.parametrize('tokenize_input,tokenize_expected', tokenize_pairs)
def test_tokenize_examples(tokenize_input, tokenize_expected):
    assert tokenize(tokenize_input) == tokenize_expected



expr_missing_open_bracket1 =  '(or (and a b) not (and (not a) c)) d)'
expr_missing_open_bracket2 =  '(or (and a b) (not (and not a) c)) d)'

expr_missing_starting_bracket =  'or (and a b) (not (and (not a c)) d)'
expr_missing_ending_bracket =  '(or (and a b) (not (and (not a) c) d'

expr_missing_close_bracket1 =  '(or (and a b) (not (and (not a) c) d)'
expr_missing_close_bracket2 =  '(or (and a b (not (and (not a) c)) d)'

expr_additional_brackets1 =  '(or ((and a b)) (not (and (not a) c)) d)'



@pytest.mark.parametrize('tokenize_input',
    [expr_missing_open_bracket1,
     expr_missing_open_bracket2])
def test_tokenize_error_missing_opening_bracket(tokenize_input):
    with pytest.raises(ValueError, match='pop from empty'):
        tokenize(tokenize_input)

def test_tokenize_error_no_starting_bracket():
    with pytest.raises(ValueError, match='not starting'):
        tokenize(expr_missing_starting_bracket)

def test_tokenize_error_no_ending_bracket():
    with pytest.raises(ValueError, match='not ending'):
        tokenize(expr_missing_ending_bracket)

@pytest.mark.parametrize('tokenize_input',
    [expr_missing_close_bracket1,
     expr_missing_close_bracket2])
def test_tokenize_error_missing_close_bracket(tokenize_input):
    with pytest.raises(ValueError, match='end of expression'):
        tokenize(tokenize_input)

# TODO: where should unnecessary brackets be handled or removed?
@pytest.mark.xfail(reason='unnecessary brackets not handled yet')
@pytest.mark.parametrize('tokenize_input',
    [expr_additional_brackets1])
def test_tokenize_error_additional_brackets(tokenize_input):
    with pytest.raises(ValueError, match='Unexpected token'):
        tokenize(tokenize_input)


