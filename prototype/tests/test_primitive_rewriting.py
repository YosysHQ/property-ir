import pytest
from pathlib import Path
from sexpr.base import IrContainer, PropertyIrNode
from sexpr.parsing import parse_document
from sexpr.base import RawSExprList
from sexpr.parsing import parse_raw_sexpr
from sexpr.primitives import FallingGclk, RisingGclk, And
from sexpr.rewriting import replace_single_node, RewriteRule, apply_rules




def check_replace_single_node(input_document_str: str, expected_output_document_str: str, rule: RewriteRule, add_identifiers_to_container: bool = False):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input and output (rewrite in-place)
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'check_replace_node_input.png')

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, rule, add_identifiers_to_container)

    parse_document(expected_output_document, container2)

    #container1.show_graph(output_directory / 'check_replace_node_output_before_renaming.png')

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    #container2.show_graph(output_directory / 'check_replace_node_expected_output.png')
    #container1.show_graph(output_directory / 'check_replace_node_output_after_renaming.png')

    assert container1 == container2



def check_apply_rules(input_document_str: str, expected_output_document_str: str, rules: dict[type[PropertyIrNode], RewriteRule]):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer()
    container2: IrContainer = IrContainer()
    parse_document(input_document, container1)

    apply_rules(container1, rules)

    parse_document(expected_output_document, container2)

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    assert container1 == container2





@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_goto(add_identifiers_to_container):

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

    check_replace_single_node(input_document_str, expected_output_document_str, goto_repeat_rule, add_identifiers_to_container=add_identifiers_to_container)


@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_and_or(add_identifiers_to_container):

    and_or_rule: RewriteRule = (['and', '<bool_list>'], ['or', '<bool_list>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (and (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (or (false) b)) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, and_or_rule, add_identifiers_to_container)


@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_not(add_identifiers_to_container):

    not_rule: RewriteRule = (['not', '<bool>'], ['not', ['not', '<bool>']]) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not b)) (declare q (or p (true))) (parse-sexpr q))"""

    expected_output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (not (not b))) (declare q (or p (true)))  (parse-sexpr q))"""

    check_replace_single_node(input_document_str, expected_output_document_str, not_rule, add_identifiers_to_container)


@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_gclk(add_identifiers_to_container):

    gclk_rule: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""

    output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (falling-gclk a b)) (parse-sexpr p))"""

    check_replace_single_node(input_document_str, output_document_str, gclk_rule, add_identifiers_to_container)


@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_error_lhs_name_collision(add_identifiers_to_container):

    gclk_rule: RewriteRule = (['rising-gclk', '<bool>', '<bool>'], ['falling-gclk', '<bool>', '<bool>']) # made-up rule for testing

    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""
    input_document: RawSExprList = parse_raw_sexpr(input_document_str)

    container1: IrContainer = IrContainer()
    parse_document(input_document, container1)
    node_id_to_replace = container1.global_nodes['p']

    with pytest.raises(AssertionError, match='Duplicate identifier'):
        replace_single_node(container1, node_id_to_replace, gclk_rule, add_identifiers_to_container)


@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_twice_gclk(add_identifiers_to_container):

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
    replace_single_node(container1, node_id_to_replace, gclk_rule1, add_identifiers_to_container)

    #container1.show_graph(output_directory / 'check_replace_node_output1.png')

    node_id_to_replace = container1.global_nodes['p']
    replace_single_node(container1, node_id_to_replace, gclk_rule2, add_identifiers_to_container)

    #container1.show_graph(output_directory / 'check_replace_node_output2.png')

    parse_document(input_document, container2)

    container1.canonical_id_renaming()
    container2.canonical_id_renaming()

    #container2.show_graph(output_directory / 'check_replace_node_expected_output.png')
    #container1.show_graph(output_directory / 'check_replace_node_output_after_renaming.png')

    assert container1 == container2


 # using a RHS let-rec with the same identifiers as LHS child identifiers should cause an error
@pytest.mark.parametrize('add_identifiers_to_container', [True, False])
def test_replace_single_node_let_rec_error(add_identifiers_to_container):
    let_rec_rule: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', ['let-rec', ['<bool1>', ['true']], '<bool1>'], '<bool2>']) # made-up rule for testing
    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk a b)) (parse-sexpr p))"""
    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    container1: IrContainer = IrContainer()
    parse_document(input_document, container1)
    node_id_to_replace = container1.global_nodes['p']

    with pytest.raises(ValueError, match='already in use'):
        replace_single_node(container1, node_id_to_replace, let_rec_rule, add_identifiers_to_container)



def test_apply_rules_one_pass():

    gclk_rule1: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    rule_dict: dict[type[PropertyIrNode], RewriteRule] = { RisingGclk: gclk_rule1 }
    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk (and a (true)) (rising-gclk (or a b) (false)))) (parse-sexpr p))"""
    output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (falling-gclk (and a (true)) (falling-gclk (or a b) (false)))) (parse-sexpr p))"""
    check_apply_rules(input_document_str, output_document_str, rule_dict)

def test_apply_rules_two_passes():

    gclk_rule1: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    gclk_rule2: RewriteRule = (['falling-gclk', '<bool1>', '<bool2>'], ['changing-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    rule_dict: dict[type, RewriteRule] = { RisingGclk: gclk_rule1, FallingGclk: gclk_rule2 }
    input_document_str: str = """(document (declare-input a) (declare-input b) (declare p (rising-gclk (and a (true)) (rising-gclk (or a b) (false)))) (parse-sexpr p))"""
    output_document_str: str = """(document (declare-input a) (declare-input b) (declare p (changing-gclk (and a (true)) (changing-gclk (or a b) (false)))) (parse-sexpr p))"""
    check_apply_rules(input_document_str, output_document_str, rule_dict)

def test_apply_rules_two_passes_cycle():

    gclk_rule1: RewriteRule = (['rising-gclk', '<bool1>', '<bool2>'], ['falling-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    gclk_rule2: RewriteRule = (['falling-gclk', '<bool1>', '<bool2>'], ['changing-gclk', '<bool1>', '<bool2>']) # made-up rule for testing
    rule_dict: dict[type, RewriteRule] = { RisingGclk: gclk_rule1, FallingGclk: gclk_rule2 }
    input_document_str: str = """(document (declare-input a) (declare-input b) (declare-rec (declare p (rising-gclk (and a (true)) (rising-gclk (or a p) (false))))) (parse-sexpr p))"""
    output_document_str: str = """(document (declare-input a) (declare-input b) (declare-rec (declare p (changing-gclk (and a (true)) (changing-gclk (or a p) (false))))) (parse-sexpr p))"""
    check_apply_rules(input_document_str, output_document_str, rule_dict)

def test_apply_rules_child_list():

    and_rule1: RewriteRule = (['and', '<child_list>'], ['or', '<child_list>']) # made-up rule for testing
    rule_dict: dict[type, RewriteRule] = { And: and_rule1 }
    input_document_str: str = """(document (declare-input a) (declare-input b) (declare-rec (declare p (rising-gclk (and a (true)) (rising-gclk (and a p) (false))))) (parse-sexpr p))"""
    output_document_str: str = """(document (declare-input a) (declare-input b) (declare-rec (declare p (rising-gclk (or a (true)) (rising-gclk (or a p) (false))))) (parse-sexpr p))"""
    check_apply_rules(input_document_str, output_document_str, rule_dict)