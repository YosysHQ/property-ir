import pytest

from sexpr import parse_expression, tokenize, RawSExpr, IrContainer, Signal
from input_data import tokenized1, tokenized2, tokenized3, tokenized4, tokenized5, tokenized6, tokenized7, tokenized8
from sexpr.base import Bool, BoundedRange, Int, IntOrUnbounded, NodeId, Property, PropertyIrNode, Range, Sequence
from sexpr.primitives import And, Not, Or, PropAlwaysRanged, PropSeq, SeqBool, SeqConcat, SeqRepeat, Constant




# these do not occur on their own, only inside an expression
literal_valid_list = [
    #(5, Int, Int(5)),
    #(['bounded-range', 3, 9], BoundedRange, BoundedRange(3,9)),
    #(['range', 3, 9], Range, Range(3,IntOrUnbounded(9))),
    #(['range', 3, '$'], Range, Range(3,IntOrUnbounded('$'))),
    #('true', Bool, Constant(True)),
    #('false', Bool, Constant(False)),
]

wrong_type_literal_list = [
    (5, Bool),
    (['bounded-range', 3, 9], Range),
    (['range', 3, 9], BoundedRange),
    (['range', 3, '$'], BoundedRange),
    (['range', 3, '$'], Sequence),
    ('true', Sequence),
    ('false', Int),
    ('a', Property)
]

literal_invalid_symbols = [
    ('f', Bool),
    ('test', Property),
    #('$', IntOrUnbounded) # can only occur as part of range; expected_type invalid
]

literal_invalid_range = [
    #(['bounded-range', 4, 2], BoundedRange), # expected_type invalid
    #(['range', 5, 0], Range),
]


@pytest.mark.parametrize('literal_expr,expec_type,expected', literal_valid_list)
def test_parse_literals_valid(container, literal_expr, expec_type, expected):
    result = parse_expression(expr=literal_expr, expected_type=expec_type, local_nodes=container.global_nodes, ir_container=container)
    assert result == expected

@pytest.mark.xfail(reason='check expected type for range')
@pytest.mark.parametrize('literal_expr,expec_type', wrong_type_literal_list)
def test_parse_literals_wrong_type(container, literal_expr, expec_type):
    with pytest.raises(TypeError, match='Mismatch of expected type'):
        parse_expression(expr=literal_expr, expected_type=expec_type, local_nodes=container.global_nodes, ir_container=container)

# TODO: ints cannot occur on their own!
@pytest.mark.xfail(reason='negative values not treated yet')
def test_parse_int_negative(container):
    with pytest.raises(ValueError, match='...'):
        parse_expression(expr=-5, expected_type=None, local_nodes=container.global_nodes, ir_container=container)

@pytest.mark.parametrize('literal_expr,expec_type', literal_invalid_symbols)
def test_parse_invalid_symbols(container, literal_expr, expec_type):
    with pytest.raises(ValueError, match='Unexpected symbol'):
        parse_expression(expr=literal_expr, expected_type=expec_type, local_nodes=container.global_nodes, ir_container=container)

@pytest.mark.xfail(reason='check if upper bound higher or equal lower bound')
@pytest.mark.parametrize('literal_expr,expec_type', literal_invalid_range)
def test_parse_literals_invalid_range(container, literal_expr, expec_type):
    with pytest.raises(TypeError, match='...'):
        parse_expression(expr=literal_expr, expected_type=expec_type, local_nodes=container.global_nodes, ir_container=container)






def test_parse_expr1(container):
    root_node_id = parse_expression(expr=tokenized1, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert isinstance(root_node_id, NodeId)
    root_node: PropertyIrNode = container[root_node_id]
    assert isinstance(root_node, Or)
    children_ids = root_node.children
    child1 = container[children_ids[0]]
    child2 = container[children_ids[1]]
    child3 = container[children_ids[2]]
    assert isinstance(child1, And)
    assert isinstance(child2, Not)
    assert isinstance(child3, Signal)
    child1_child1 = container[child1.children[0]]
    child1_child2 = container[child1.children[1]]
    assert isinstance(child1_child1, Signal)
    assert isinstance(child1_child2, Signal)
    child2_child = container[child2.child]
    assert isinstance(child2_child, And)
    child2_child_children_ids = child2_child.children
    child2_child_child1 = container[child2_child_children_ids[0]]
    assert isinstance(child2_child_child1, Not)
    assert isinstance(container[child2_child_children_ids[1]], Signal)
    assert isinstance(container[child2_child_child1.child], Signal)


def test_parse_expr2(container):
    root_node_id = parse_expression(expr=tokenized2, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert isinstance(root_node_id, NodeId)
    root_node: PropertyIrNode = container[root_node_id]
    assert isinstance(root_node, SeqConcat)
    children_ids = root_node.children
    child1 = container[children_ids[0]]
    child2 = container[children_ids[1]]
    assert isinstance(child1, SeqRepeat)
    assert isinstance(child2, SeqConcat)
    assert child1.child1 == Range(5, IntOrUnbounded(5))
    child1_child2 = container[child1.child2]
    assert isinstance(child1_child2, SeqBool)
    assert isinstance(container[child1_child2.child], Signal)
    child2_child1 = container[child2.children[0]]
    child2_child2 = container[child2.children[1]]
    assert isinstance(child2_child1, SeqBool)
    assert isinstance(child2_child2, SeqBool)
    assert isinstance(container[child2_child1.child], Signal)
    assert isinstance(container[child2_child2.child], Signal)


def test_parse_expr3(container):
    root_node_id = parse_expression(expr=tokenized3, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert isinstance(root_node_id, NodeId)
    root_node: PropertyIrNode = container[root_node_id]
    assert isinstance(root_node, PropAlwaysRanged)
    assert root_node.child1 == Range(4, IntOrUnbounded('$'))
    child2 = container[root_node.child2]
    assert isinstance(child2, PropSeq)
    child2_child = container[child2.child]
    assert isinstance(child2_child, SeqBool)
    child2_child_child = container[child2_child.child]
    assert isinstance(child2_child_child, Not)
    assert isinstance(container[child2_child_child.child], Signal)



expr_valid_list = [tokenized4, tokenized5, tokenized6, tokenized7, tokenized8]

@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_expr_no_error(container, expr):
    root_node_id = parse_expression(expr=expr, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert root_node_id is not None