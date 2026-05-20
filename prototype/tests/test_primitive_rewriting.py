import pytest
from pathlib import Path
from sexpr.base import IrContainer
from sexpr.parsing import parse_document
from sexpr.base import RawSExprList
from sexpr.parsing import parse_raw_sexpr
from sexpr.rewriting import replace_single_node, RewriteRule




def check_replace_single_node(input_document_str: str, expected_output_document_str: str, rule: RewriteRule):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input and output (rewrite in-place)
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'check_replace_node_input.png')

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, rule)

    parse_document(expected_output_document, container2)

    #container1.show_graph(output_directory / 'check_replace_node_output_before_renaming.png')

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    #container2.show_graph(output_directory / 'check_replace_node_expected_output.png')
    #container1.show_graph(output_directory / 'check_replace_node_output_after_renaming.png')

    assert container1 == container2


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


def test_replace_single_node_and_or():

    and_or_rule: RewriteRule = (['and', '<bool_list>'], ['or', '<bool_list>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (and (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (or (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, and_or_rule)


def test_replace_single_node_not():

    not_rule: RewriteRule = (['not', '<bool>'], ['not', ['not', '<bool>']]) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not b)) (declare q (or p (true))) (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not (not b))) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, not_rule)


def test_replace_single_node_gclk():

    gclk_rule: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""

    output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (falling-gclk a b)) (parse-sexpr p))"""

    check_replace_single_node(input_document_str, output_document_str, gclk_rule)


def test_replace_single_node_error_lhs_name_collision():

    gclk_rule: RewriteRule = (['rising-gclk', '<bool>', '<bool>'], ['falling-gclk', '<bool>', '<bool>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""
    input_document: RawSExprList = parse_raw_sexpr(input_document_str)

    container1: IrContainer = IrContainer()
    parse_document(input_document, container1)
    node_id_to_replace = container1.global_nodes['p']

    with pytest.raises(AssertionError, match='Duplicate identifier'):
        replace_single_node(container1, node_id_to_replace, gclk_rule)


def test_replace_single_node_twice_gclk():

    gclk_rule1: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    gclk_rule2: RewriteRule = (['falling-gclk', '<bool1>', '<bool2>'], ['rising-gclk', '<bool1>', '<bool2>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""

    #expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (falling-gclk a b)) (parse-sexpr p))"""

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    #expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input and output (rewrite in-place)
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'check_replace_node_input.png')

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, gclk_rule1)

    #container1.show_graph(output_directory / 'check_replace_node_output1.png')

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, gclk_rule2)

    #container1.show_graph(output_directory / 'check_replace_node_output2.png')

    parse_document(input_document, container2)

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    #container2.show_graph(output_directory / 'check_replace_node_expected_output.png')
    #container1.show_graph(output_directory / 'check_replace_node_output_after_renaming.png')

    assert container1 == container2
