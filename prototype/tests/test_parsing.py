import pytest

from sexpr import parse_expression, tokenize, RawSExpr






@pytest.fixture
def expr1():
    return '(or (and a b) (not (and (not a) c)) d)'

def test_parse(expr1):
    assert tokenize(expr1) is not None