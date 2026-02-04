import pytest
from pathlib import Path

from sexpr import parse_expression, parse_literal, parse_raw_sexpr, RawSExpr, IrContainer, Signal, parse_document
from input_data import raw_sexpr1, raw_sexpr2, raw_sexpr3, raw_sexpr4, raw_sexpr5, raw_sexpr6, raw_sexpr7, raw_sexpr8
from input_data import raw_sexpr6_declare, raw_sexpr6_declare_rec, raw_sexpr5_declare_rec
from sexpr.base import Bool, BoundedRange, IntOrUnbounded, NodeId, Property, PropertyIrNode, Range, Sequence, UnnamedExpressionDeclaration
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




def wrap_in_document(expr: RawSExpr) -> RawSExpr:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
        ['parse-sexpr', expr]
    ]

def wrap_multiple_expr_in_document(expr_list: list[RawSExpr]) -> RawSExpr:
    parse_expr_list = [['parse-sexpr', expr] for expr in expr_list]
    return ['document', ['add-signals', 'a', 'b', 'c', 'd']] + parse_expr_list


def wrap_statement_in_document(expr: RawSExpr) -> RawSExpr:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
        expr
    ]

def wrap_multiple_statements_in_document(expr_list: list[RawSExpr]) -> RawSExpr:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
    ] + expr_list



@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_doc_no_error(empty_container, expr):
    parse_document(wrap_in_document(expr), ir_container=empty_container)
    assert len(empty_container.declarations) == 5

def test_parse_document_multiple_expressions(empty_container):
    parse_document(wrap_multiple_expr_in_document(expr_valid_list), ir_container=empty_container)
    assert len(empty_container.declarations) == 9


def test_parse_document_expr1(empty_container):
    parse_document(wrap_in_document(raw_sexpr1), ir_container=empty_container)
    declaration = empty_container.declarations[4]
    assert isinstance(declaration, UnnamedExpressionDeclaration)
    root_node_id = declaration.node_id
    root_node: PropertyIrNode = empty_container[root_node_id]
    assert isinstance(root_node, Or)
    children_ids = root_node.children
    child1 = empty_container[children_ids[0]]
    child2 = empty_container[children_ids[1]]
    child3 = empty_container[children_ids[2]]
    assert isinstance(child1, And)
    assert isinstance(child2, Not)
    assert isinstance(child3, Signal)
    child1_child1 = empty_container[child1.children[0]]
    child1_child2 = empty_container[child1.children[1]]
    assert isinstance(child1_child1, Signal)
    assert isinstance(child1_child2, Signal)
    child2_child = empty_container[child2.child]
    assert isinstance(child2_child, And)
    child2_child_children_ids = child2_child.children
    child2_child_child1 = empty_container[child2_child_children_ids[0]]
    assert isinstance(child2_child_child1, Not)
    assert isinstance(empty_container[child2_child_children_ids[1]], Signal)
    assert isinstance(empty_container[child2_child_child1.child], Signal)



@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_document_roundtrip_no_error(empty_container, expr):
    parse_document(wrap_in_document(expr), ir_container=empty_container)
    declared_nodes = {
        empty_container.declarations[0].node_id: empty_container.declarations[0].node_name,
        empty_container.declarations[1].node_id: empty_container.declarations[1].node_name,
        empty_container.declarations[2].node_id: empty_container.declarations[2].node_name,
        empty_container.declarations[3].node_id: empty_container.declarations[3].node_name
    }
    declaration = empty_container.declarations[4]
    assert isinstance(declaration, UnnamedExpressionDeclaration)
    output_expr: RawSExpr = empty_container.generate_raw_sexpr(node_id=declaration.node_id, declared_nodes=declared_nodes)
    parse_document(wrap_in_document(output_expr), ir_container=IrContainer())




def test_expr6_declare(empty_container):
    container = empty_container
    parse_document(wrap_statement_in_document(raw_sexpr6_declare), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_expr6.png')
    assert 'global-node-name1' in container.global_nodes
    assert len(container.global_nodes) == 5 # 4 signal nodes + 1 declared node
    assert len(container.declarations) == 5 # 4 signal declarations + 1 declare-rec
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 1 # 1 declared node
    assert len(container.sink_nodes) == 0

def test_expr6_declare_rec(empty_container):
    container = empty_container
    parse_document(wrap_statement_in_document(raw_sexpr6_declare_rec), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.declarations) == 5 # 4 signal declarations + 1 declare-rec
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.sink_nodes) == 0

def test_expr6_1_declare_rec(empty_container):
    container = empty_container
    parse_document(wrap_multiple_statements_in_document([['parse-sexpr', raw_sexpr1], raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_1.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.declarations) == 6 # 4 signal declarations + 1 declare-rec + 1 unnamed root
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.sink_nodes) == 1 # 1 unnamed root


def test_expr5_6_declare_rec(empty_container):
    container = empty_container
    parse_document(wrap_multiple_statements_in_document([raw_sexpr5_declare_rec, raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert 'foo' in container.global_nodes
    assert 'bar' in container.global_nodes
    assert len(container.global_nodes) == 8 # 4 signal nodes + 4 declared nodes
    assert len(container.declarations) == 6 # 4 signal declarations + 2 declare-rec
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 4 # 4 declared nodes
    assert len(container.sink_nodes) == 0 # 0 unnamed roots
    assert len(container.node_names) == 8 # 8 global names


def test_expr6_6_declare_rec(empty_container):
    container = empty_container
    parse_document(wrap_multiple_statements_in_document([['parse-sexpr', raw_sexpr6], raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.declarations) == 6 # 4 signal declarations + 1 declare-rec + 1 unnamed root
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.sink_nodes) == 1 # 1 unnamed root
    # the global nodes get new local names because they are already in use after the let-rec expr, then later the local names of let-rec
    # get renamed when the global node names are set in add_declaration
    #assert len(container.node_names) == 8 # 6 global names + 2 local names + 2 local names because of renaming = 10


def test_expr6_6_declare_rec_illegal_name_resuse(empty_container):
    # attempting the reuse of a global node name in a let-rec as a local name results in an error
    # because of the ambiguity which node should be used (like in nested let-rec expressions, where this case is excluded as well)
    # is this the desired behavior?
    container = empty_container
    with pytest.raises(ValueError, match='already in use'):
        parse_document(wrap_multiple_statements_in_document([raw_sexpr6_declare_rec, ['parse-sexpr', raw_sexpr6]]), ir_container=container)