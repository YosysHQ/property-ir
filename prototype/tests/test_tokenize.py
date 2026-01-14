import pytest

from sexpr import tokenize

from input_data import expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8
from input_data import tokenized1, tokenized2, tokenized3, tokenized4, tokenized5, tokenized6, tokenized7, tokenized8



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

