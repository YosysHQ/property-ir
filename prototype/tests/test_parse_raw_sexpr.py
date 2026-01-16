import pytest

from sexpr import parse_raw_sexpr

from input_data import expr1, expr2, expr3, expr4, expr5, expr6, expr7, expr8
from input_data import raw_sexpr1, raw_sexpr2, raw_sexpr3, raw_sexpr4, raw_sexpr5, raw_sexpr6, raw_sexpr7, raw_sexpr8



str_raw_sexpr_pairs = [(expr1, raw_sexpr1),
    (expr2, raw_sexpr2),
    (expr3, raw_sexpr3),
    (expr4, raw_sexpr4),
    (expr5, raw_sexpr5),
    (expr6, raw_sexpr6),
    (expr7, raw_sexpr7),
    (expr8, raw_sexpr8),
]



@pytest.mark.parametrize('str_input,raw_sexpr_expected', str_raw_sexpr_pairs)
def test_tokenize_examples(str_input, raw_sexpr_expected):
    assert parse_raw_sexpr(str_input) == raw_sexpr_expected



expr_missing_open_bracket1 =  '(or (and a b) not (and (not a) c)) d)'
expr_missing_open_bracket2 =  '(or (and a b) (not (and not a) c)) d)'

expr_missing_starting_bracket =  'or (and a b) (not (and (not a c)) d)'
expr_missing_ending_bracket =  '(or (and a b) (not (and (not a) c) d'

expr_missing_close_bracket1 =  '(or (and a b) (not (and (not a) c) d)'
expr_missing_close_bracket2 =  '(or (and a b (not (and (not a) c)) d)'

expr_additional_brackets1 =  '(or ((and a b)) (not (and (not a) c)) d)'
expr_additional_brackets2 =  '(or (and a (b)) (not (and (not a) c)) d)'
expr_additional_brackets3 =  '(or (and a b ()) (not (and (not a) c)) d)'
expr_additional_brackets4 =  '(or (and a b (  )) (not (and (not a) c)) d)'



@pytest.mark.parametrize('str_input',
    [expr_missing_open_bracket1,
     expr_missing_open_bracket2])
def test_parse_raw_sexpr_error_missing_opening_bracket(str_input):
    with pytest.raises(ValueError, match='pop from empty'):
        parse_raw_sexpr(str_input)

def test_parse_raw_sexpr_error_no_starting_bracket():
    with pytest.raises(ValueError, match='not starting'):
        parse_raw_sexpr(expr_missing_starting_bracket)

def test_parse_raw_sexpr_error_no_ending_bracket():
    with pytest.raises(ValueError, match='not ending'):
        parse_raw_sexpr(expr_missing_ending_bracket)

@pytest.mark.parametrize('str_input',
    [expr_missing_close_bracket1,
     expr_missing_close_bracket2])
def test_tokenize_error_missing_close_bracket(str_input):
    with pytest.raises(ValueError, match='end of expression'):
        parse_raw_sexpr(str_input)

# TODO: this is not handled by parse_raw_sexpr, but the error is detected in parse_expression
@pytest.mark.xfail(reason='unnecessary brackets not handled yet')
@pytest.mark.parametrize('str_input',
    [expr_additional_brackets1, expr_additional_brackets2, expr_additional_brackets3, expr_additional_brackets4])
def test_tokenize_error_additional_brackets(str_input):
    with pytest.raises(ValueError, match='Unexpected token'):
        parse_raw_sexpr(str_input)

