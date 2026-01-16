import pytest

from sexpr import parse_expression, parse_literal, parse_raw_sexpr, RawSExpr, IrContainer, Signal
from input_data import raw_sexpr1, raw_sexpr2, raw_sexpr3, raw_sexpr4, raw_sexpr5, raw_sexpr6, raw_sexpr7, raw_sexpr8
from sexpr.base import Bool, BoundedRange, IntOrUnbounded, NodeId, Property, PropertyIrNode, Range, Sequence
from sexpr.primitives import And, Not, Or, PropAlwaysRanged, PropSeq, SeqBool, SeqConcat, SeqRepeat, Constant




literal_valid_list = [
    ('5', int, 5),
    (['bounded-range', '3', '9'], BoundedRange, BoundedRange(3,9)),
    (['range', '3', '9'], Range, Range(3, IntOrUnbounded(9))),
    (['range', '3', '$'], Range, Range(3, IntOrUnbounded('$'))),
    ('true', bool, True),
    ('false', bool, False),
]

wrong_type_literal_list = [
    ('5', Bool),
    (['bounded-range', '3', '9'], Range),
    (['range', '3', '9'], BoundedRange),
    (['range', '3', '$'], BoundedRange),
    (['range', '3', '$'], Sequence),
    ('true', Sequence),
    ('false', int),
    ('a', Property),
    ('f', bool),
    ('test', int),
    ('$', Range),
    ('-5', int)
]

literal_invalid_expected_types = [
    ('f', bool),
    ('test', Property),
    ('$', IntOrUnbounded)
]

literal_invalid_range = [
    (['bounded-range', '4', '2'], BoundedRange),
    (['range', '5', '0'], Range),
]



@pytest.mark.parametrize('literal_expr,expec_type,expected', literal_valid_list)
def test_parse_literals_valid(literal_expr, expec_type, expected):
    result = parse_literal(literal_expr=literal_expr, expected_type=expec_type)
    assert result == expected

@pytest.mark.parametrize('literal_expr,expec_type', wrong_type_literal_list)
def test_parse_literals_wrong_type(literal_expr, expec_type):
    with pytest.raises(TypeError, match='Mismatch of expected type'):
        parse_literal(literal_expr=literal_expr, expected_type=expec_type)

@pytest.mark.parametrize('literal_expr,expec_type', literal_invalid_range)
def test_parse_literals_invalid_range(container, literal_expr, expec_type):
    with pytest.raises(ValueError, match='...'):
        parse_literal(literal_expr=literal_expr, expected_type=expec_type)





def test_parse_expr1(container):
    root_node_id = parse_expression(expr=raw_sexpr1, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
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
    root_node_id = parse_expression(expr=raw_sexpr2, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
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
    root_node_id = parse_expression(expr=raw_sexpr3, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
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



expr_valid_list = [raw_sexpr4, raw_sexpr5, raw_sexpr6, raw_sexpr7, raw_sexpr8]

@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_expr_no_error(container, expr):
    root_node_id = parse_expression(expr=expr, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert root_node_id is not None