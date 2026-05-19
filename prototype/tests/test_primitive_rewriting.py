import pytest
from sexpr.base import IrContainer
from sexpr.parsing import parse_document
from sexpr.base import RawSExprList
from sexpr.parsing import parse_raw_sexpr
from sexpr.rewriting import replace_single_node, RewriteRule




def check_replace_single_node(input_document_str: str, expected_output_document_str: str, rule: RewriteRule):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer()
    container2: IrContainer = IrContainer()
    parse_document(input_document, container1)

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, rule)

    parse_document(expected_output_document, container2)

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    assert container1 == container2


@pytest.mark.xfail(reason='not implemented yet')
def test_replace_single_node_goto():

    goto_repeat_rule: RewriteRule = (['clk-seq-goto-repeat', '<range>', '<bool>'],
    ['clk-seq-repeat', '<range>', ['clk-seq-concat', ['clk-seq-repeat', ['range', '0', '$'], ['clk-seq-bool', ['not', '<bool>']]], ['clk-seq-bool', '<bool>']]])

    input_document_str: str = """(document (declare-input a) (declare p (clk-seq-goto-repeat (range 3 5) a )) (declare q (clk-prop-seq p)) (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a)
        (declare p
            (clk-seq-repeat (range 3 5) (clk-seq-concat
                (clk-seq-repeat (range 0 $) (clk-seq-bool (not a)))
                (clk-seq-bool a) )))
        (declare q (clk-prop-seq p))
        (parse-sexpr q) )"""

    check_replace_single_node(input_document_str, expected_output_document_str, goto_repeat_rule)


@pytest.mark.xfail(reason='not implemented yet')
def test_replace_single_node_and_or():

    and_or_rule: RewriteRule = (['and', '<bool_list>'], ['or', '<bool_list>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (and (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (or (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, and_or_rule)


@pytest.mark.xfail(reason='not implemented yet')
def test_replace_single_node_not():

    not_rule: RewriteRule = (['not', '<bool>'], ['not', ['not', '<bool>']]) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not b)) (declare q (or p (true))) (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not (not b))) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, not_rule)