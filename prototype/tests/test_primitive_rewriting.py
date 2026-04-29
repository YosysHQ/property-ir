import pytest
from sexpr import IrContainer, parse_document
from sexpr.base import RawSExprList
from sexpr.parsing import parse_raw_sexpr
from sexpr.rewriting import replace_single_node, goto_repeat_rule




@pytest.mark.xfail(reason='not implemented yet')
def test_replace_single_node():
    input_document_str: str = """(document (declare-input a) (declare p (clk-seq-goto-repeat (range 3 5) a )) (declare q (clk-prop-seq p)) (parse-sexpr q))"""
    input_document: RawSExprList = parse_raw_sexpr(input_document_str)

    expected_output_document_str: str = """(document (declare-input a)
        (declare p
            (clk-seq-repeat (range 3 5) (clk-seq-concat
                (clk-seq-repeat (range 0 $) (clk-seq-bool (not a)))
                (clk-seq-bool a) )))
        (declare q (clk-prop-seq p))
        (parse-sexpr q) )"""

    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer()
    container2: IrContainer = IrContainer()
    parse_document(input_document, container1)

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, goto_repeat_rule)

    parse_document(expected_output_document, container2)

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    assert container1 == container2