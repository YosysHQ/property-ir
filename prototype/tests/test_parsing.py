import pytest

from sexpr import parse_expression, tokenize, RawSExpr, IrContainer, Signal
from input_data import signals
from input_data import tokenized1, tokenized2, tokenized3, tokenized4, tokenized5, tokenized6, tokenized7, tokenized8
from sexpr.base import NodeId



def test_parse_expr1(container):
    root_node = parse_expression(expr=tokenized1, expected_type=None, signals=signals, ir_container=container)
    assert isinstance(root_node, NodeId)