import logging

import pytest
from ir import (
    IrContainer,
    RawSExprList,
    Signal,
    parse_document,
    parse_expression,
    parse_literal,
)
from ir.base import (
    Bool,
    BoundedRange,
    IntOrUnbounded,
    NodeId,
    Property,
    PropertyIrNode,
    Range,
    RootTestDirective,
    Sequence,
)
from ir.parsing import parse_raw_sexpr
from ir.primitives.bool_primitives import (
    And,
    Not,
    Or,
)
from ir.primitives.clocked_primitives import (
    ClkPropAlwaysRanged,
    ClkPropWeak,
    ClkSeqBool,
)
from ir.primitives.simple_primitives import (
    SeqBool,
    SeqConcat,
    SeqRepeat,
)

from tests.helpers import (
    apply_roundtrip,
    wrap_in_document,
    wrap_multiple_expr_in_document,
    wrap_multiple_statements_in_document,
    wrap_statement_in_document,
)
from tests.input_data import (
    merge_with_type_conflict,
    merge_without_type_conflict,
    raw_sexpr1,
    raw_sexpr2,
    raw_sexpr3,
    raw_sexpr4,
    raw_sexpr5,
    raw_sexpr5_declare_rec,
    raw_sexpr6,
    raw_sexpr6_declare,
    raw_sexpr6_declare_rec,
    raw_sexpr7,
    raw_sexpr7_declare_rec,
    raw_sexpr8,
    raw_sexpr_signal_redeclaration_global1,
    raw_sexpr_signal_redeclaration_global2,
    raw_sexpr_signal_redeclaration_local,
    uninst_node_exprs,
)

logger = logging.getLogger(__name__)


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


expr_valid_list = [raw_sexpr1, raw_sexpr2, raw_sexpr3, raw_sexpr4, raw_sexpr5, raw_sexpr6, raw_sexpr7, raw_sexpr8,
    raw_sexpr_signal_redeclaration_local]

named_expr_valid_list = [raw_sexpr6_declare, raw_sexpr6_declare_rec, raw_sexpr5_declare_rec, raw_sexpr7_declare_rec,
        raw_sexpr_signal_redeclaration_global1, raw_sexpr_signal_redeclaration_global2]



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
    assert isinstance(root_node, ClkPropAlwaysRanged)
    assert root_node.child1 == Range(4, IntOrUnbounded('$'))
    child2 = container[root_node.child2]
    assert isinstance(child2, ClkPropWeak)
    child2_child = container[child2.child]
    assert isinstance(child2_child, ClkSeqBool)
    child2_child_child = container[child2_child.child]
    assert isinstance(child2_child_child, Not)
    assert isinstance(container[child2_child_child.child], Signal)



@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_expr_no_error(container, expr):
    root_node_id = parse_expression(expr=expr, expected_type=None, local_nodes=container.global_nodes, ir_container=container)
    assert root_node_id is not None


@pytest.mark.parametrize('expr', expr_valid_list)
def test_parse_doc_no_error(empty_container, expr):
    parse_document(wrap_in_document(expr), ir_container=empty_container)
    assert len(empty_container.directives) == 1

def test_parse_document_multiple_expressions():
    container = IrContainer()
    parse_document(wrap_multiple_expr_in_document(expr_valid_list), ir_container=container)
    assert len(container.directives) != 0


def test_parse_document_expr1():
    container = IrContainer()
    parse_document(wrap_in_document(raw_sexpr1), ir_container=container)
    directive = container.directives[0]
    assert isinstance(directive, RootTestDirective)
    root_node_id = directive.node_id
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


@pytest.mark.parametrize('expr', expr_valid_list)
def test_generate_raw_sexpr_node_defs_no_error(expr):
    container1 = IrContainer()
    parse_document(wrap_in_document(expr), ir_container=container1)
    declared_nodes = {
         container1.global_nodes['a']: 'a',
         container1.global_nodes['b']: 'b',
         container1.global_nodes['c']: 'c',
         container1.global_nodes['d']: 'd',
    }
    directive = container1.directives[0]
    assert isinstance(directive, RootTestDirective)
    output_expr_list = container1.generate_raw_sexpr_node_defs(node_list=[directive.node_id], declared_nodes=declared_nodes, node_names_to_use={})
    output_expr2: RawSExprList | str = container1.generate_raw_sexpr_unnamed_root(node_id=container1.directives[0].node_id, declared_nodes=declared_nodes)
    logger.debug(output_expr_list)
    logger.debug(output_expr2)
    output_document = container1.output_container()
    logger.debug(output_document)
    parse_document(output_document, ir_container=IrContainer())


@pytest.mark.parametrize('expr', expr_valid_list)
def test_roundtrip_unnamed_expr(expr):
    apply_roundtrip(wrap_in_document(expr))

@pytest.mark.parametrize('expr', named_expr_valid_list)
def test_roundtrip_named_expr(expr):
    apply_roundtrip(wrap_statement_in_document(expr))


def test_expr6_declare():
    container = IrContainer()
    parse_document(wrap_statement_in_document(raw_sexpr6_declare), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_expr6.png')
    assert 'global-node-name1' in container.global_nodes
    assert len(container.global_nodes) == 5 # 4 signal nodes + 1 declared node
    assert len(container.directives) == 0
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 1 # 1 declared node
    assert len(container.get_sink_nodes()) == 0

def test_expr6_declare_rec():
    container = IrContainer()
    parse_document(wrap_statement_in_document(raw_sexpr6_declare_rec), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.directives) == 0
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.get_sink_nodes()) == 0

def test_expr6_1_declare_rec():
    container = IrContainer()
    parse_document(wrap_multiple_statements_in_document([['parse-sexpr', raw_sexpr1], raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_1.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.directives) == 1
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.get_sink_nodes()) == 1 # 1 unnamed root


def test_expr5_6_declare_rec():
    container = IrContainer()
    parse_document(wrap_multiple_statements_in_document([raw_sexpr5_declare_rec, raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert 'foo' in container.global_nodes
    assert 'bar' in container.global_nodes
    assert len(container.global_nodes) == 8 # 4 signal nodes + 4 declared nodes
    assert len(container.directives) == 0
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 4 # 4 declared nodes
    assert len(container.get_sink_nodes()) == 0 # 0 unnamed roots
    #assert len(container.node_names) == 8 # 8 global names


def test_expr6_6_declare_rec():
    container = IrContainer()
    parse_document(wrap_multiple_statements_in_document([['parse-sexpr', raw_sexpr6], raw_sexpr6_declare_rec]), ir_container=container)
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'dec_rec_expr6_6.png')
    assert 'prop1' in container.global_nodes
    assert 'prop2' in container.global_nodes
    assert len(container.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container.directives) == 1
    assert len(container.source_nodes) == 4 # 4 signal nodes
    assert len(container.inner_nodes) == 2 # 2 declared nodes
    assert len(container.get_sink_nodes()) == 1 # 1 unnamed root
    # the global nodes get new local names because they are already in use after the let-rec expr, then later the local names of let-rec
    # get renamed when the global node names are set in add_declaration
    #assert len(container.node_names) == 8 # 6 global names + 2 local names + 2 local names because of renaming = 10



def test_expr5_6_declare_rec_output():
    container1 = IrContainer()
    parse_document(wrap_multiple_statements_in_document([raw_sexpr5_declare_rec, raw_sexpr6_declare_rec]), ir_container=container1)

    doc_output = container1.output_container()
    container1.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'dec_rec_expr5_6_before.png')

    container2 = IrContainer()
    parse_document(doc_output, container2)
    container2.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container2.show_graph(output_directory / 'dec_rec_expr5_6_after.png')

    assert 'prop1' in container2.global_nodes
    assert 'prop2' in container2.global_nodes
    assert 'foo' in container2.global_nodes
    assert 'bar' in container2.global_nodes
    assert len(container2.global_nodes) == 8 # 4 signal nodes + 4 declared nodes
    assert len(container2.directives) == 0
    assert len(container2.source_nodes) == 4 # 4 signal nodes
    assert len(container2.inner_nodes) == 4 # 4 declared nodes
    assert len(container2.get_sink_nodes()) == 0 # 0 unnamed roots


def test_expr6_6_declare_rec_output():
    container1 = IrContainer()
    parse_document(wrap_multiple_statements_in_document([['parse-sexpr', raw_sexpr6], raw_sexpr6_declare_rec]), ir_container=container1)

    doc_output = container1.output_container()
    container1.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'dec_rec_expr6_6_before.png')

    container2 = IrContainer()
    parse_document(doc_output, container2)
    container2.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container2.show_graph(output_directory / 'dec_rec_expr6_6_after.png')

    assert 'prop1' in container2.global_nodes
    assert 'prop2' in container2.global_nodes
    assert len(container2.global_nodes) == 6 # 4 signal nodes + 2 declared nodes
    assert len(container2.directives) == 1
    assert len(container2.source_nodes) == 4 # 4 signal nodes
    assert len(container2.inner_nodes) == 2 # 2 declared nodes
    assert len(container2.get_sink_nodes()) == 1 # 1 unnamed root


def test_expr7_declare_rec_output():
    container1 = IrContainer()
    parse_document(wrap_statement_in_document(raw_sexpr7_declare_rec), ir_container=container1)

    doc_output = container1.output_container()
    container1.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'dec_rec_expr7_before.png')

    container2 = IrContainer()
    parse_document(doc_output, container2)
    container2.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container2.show_graph(output_directory / 'dec_rec_expr7_after.png')

    assert 'q1' in container2.global_nodes
    assert 'q4' in container2.global_nodes
    assert 'p' in container2.global_nodes
    assert len(container2.global_nodes) == 7 # 4 signal nodes + 3 declared nodes
    assert len(container2.directives) == 0
    assert len(container2.source_nodes) == 4 # 4 signal nodes
    assert len(container2.inner_nodes) == 3 # 3 declared nodes
    assert len(container2.get_sink_nodes()) == 0 # no unnamed roots


def test_expr6_6_declare_rec_illegal_name_resuse():
    # attempting the reuse of a global node name in a let-rec as a local name results in an error
    # because of the ambiguity which node should be used (like in nested let-rec expressions, where this case is excluded as well)
    # is this the desired behavior?
    container = IrContainer()
    with pytest.raises(ValueError, match='already in use'):
        parse_document(wrap_multiple_statements_in_document([raw_sexpr6_declare_rec, ['parse-sexpr', raw_sexpr6]]), ir_container=container)


def test_signal_redeclaration():
    container1 = IrContainer()
    parse_document(wrap_in_document(raw_sexpr_signal_redeclaration_local), container1)
    container2 = IrContainer()
    parse_document(wrap_statement_in_document(raw_sexpr_signal_redeclaration_global1), container2)
    container3 = IrContainer()
    parse_document(wrap_statement_in_document(raw_sexpr_signal_redeclaration_global2), container3)

    output2 = container2.output_container()
    output3 = container3.output_container()

    container2_2 = IrContainer()
    container3_2 = IrContainer()
    parse_document(output2, container2_2)
    parse_document(output3, container3_2)

    assert len(container2.global_nodes) == 5 # 4 signal nodes + 1 declared node
    assert len(container3.global_nodes) == 5 # 4 signal nodes + 1 declared node
    assert len(container2_2.global_nodes) == 5 # 4 signal nodes + 1 declared node
    assert len(container3_2.global_nodes) == 5 # 4 signal nodes + 1 declared node

    #output_directory: Path = Path('./output')
    #container3_2.show_graph(output_directory / 'signal_test.png')


@pytest.mark.parametrize('expr', uninst_node_exprs)
def test_uninstantiated_node(expr):
    with pytest.raises(ValueError, match='uninstantiated node'):
        container = IrContainer()
        parse_document(wrap_in_document(expr), ir_container=container)



@pytest.mark.parametrize('expr', [merge_with_type_conflict])
def test_merge_with_type_conflict(expr):
    with pytest.raises(TypeError, match='cannot be set to type'):
        container = IrContainer()
        parse_document(wrap_in_document(expr), ir_container=container)


@pytest.mark.parametrize('expr', [merge_without_type_conflict])
def test_merge_without_type_conflict(expr):
        apply_roundtrip(wrap_in_document(expr))


@pytest.mark.parametrize('expr', [['rising-gclk', 'a', 'b', 'c'], ['rising-gclk', 'a'], ['seq-repeat', ['range', '1', '2'], ['seq-bool', 'a'], 'b']])
def test_wrong_argument_count(expr):
    with pytest.raises(AssertionError, match='number of arguments'):
        container = IrContainer()
        parse_document(wrap_in_document(expr), ir_container=container)


# TEST DIRECTIVES

def test_directives_1():
    document_str: str = """(document
    (declare-input a)
    (declare-input b)
    (declare p (clk-prop-strong (clk-seq-bool a)))
    (declare q (clk-prop-weak (clk-seq-bool b)))
    (declare s (clk-seq-bool b))
    (assert-property p)
    (assert-property p)
    (assume-property q)
    (restrict-property p)
    (cover-property p)
    (cover-sequence s)
    (trigger-sequence s)
    (parse-sexpr p) )
    """
    document = parse_raw_sexpr(document_str)
    logger.info('TESTING %s', document)
    container1 = IrContainer()
    parse_document(document, ir_container=container1)
    output_document = container1.output_container()
    logger.info(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2
    assert len(container1.directives) == 8

def test_directives_2():
    document_str: str = """(document
    (declare-input a)
    (declare-input b)
    (declare p (clk-prop-strong (clk-seq-bool a)))
    (declare q (clk-prop-weak (clk-seq-bool b)))
    (declare s (clk-seq-bool b))
    (assert-property p :disable-iff a :reset-iff b :enable a :negated false :evaluation-scope initial :property-type safety)
    (assume-property q  :disable-iff a :reset-iff b :enable a :negated true :evaluation-scope always :property-type liveness)
    (restrict-property p :disable-iff a :reset-iff b :enable a :negated true :evaluation-scope always :property-type liveness)
    (cover-property p :vacuity-mode nonvacuously-satisfied :disable-iff a :reset-iff b :enable a :negated true :evaluation-scope always :property-type safety)
    (cover-sequence s :vacuity-mode nonvacuous :disable-iff a :reset-iff b :enable a :negated false :evaluation-scope initial :property-type safety)
    (trigger-sequence s :disable-iff a :reset-iff b :enable a :negated false :evaluation-scope initial :property-type safety)
    (parse-sexpr p) )
    """
    document = parse_raw_sexpr(document_str)
    apply_roundtrip(document)

def test_directives_wrong_parameter_error_1():
    with pytest.raises(TypeError):
        document_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (clk-prop-strong (clk-seq-bool a)))
        (declare q (clk-prop-weak (clk-seq-bool b)))
        (declare s (clk-seq-bool b))
        (assert-property p :vacuity-mode satisfied)
        )"""
        document = parse_raw_sexpr(document_str)
        apply_roundtrip(document)

def test_directives_wrong_parameter_error_2():
    with pytest.raises(ValueError):
        document_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (clk-prop-strong (clk-seq-bool a)))
        (declare q (clk-prop-weak (clk-seq-bool b)))
        (declare s (clk-seq-bool b))
        (assert-property p :property-tpe safety)
        )"""
        document = parse_raw_sexpr(document_str)
        apply_roundtrip(document)


def test_directives_type_error_1():
    with pytest.raises(TypeError):
        document_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (prop-strong (seq-bool a)))
        (assert-property p)
        (parse-sexpr p) )
        """
        document = parse_raw_sexpr(document_str)
        apply_roundtrip(document)

def test_directives_type_error_2():
    with pytest.raises(TypeError):
        document_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (prop-strong (seq-bool a)))
        (cover-sequence p)
        (parse-sexpr p) )
        """
        document = parse_raw_sexpr(document_str)
        apply_roundtrip(document)

def test_declared_node_removed():
        document_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (clk-prop-strong (clk-seq-bool a)))
        (declare q (clk-prop-strong (clk-seq-bool b)))
        (assert-property p)
        (parse-sexpr p) )
        """
        document = parse_raw_sexpr(document_str)
        container1 = IrContainer()
        parse_document(document, ir_container=container1)
        container1.canonical_id_renaming(remove_unreachable_declared_nodes=True)
        assert 'p' in container1.global_nodes
        assert 'q' not in container1.global_nodes
