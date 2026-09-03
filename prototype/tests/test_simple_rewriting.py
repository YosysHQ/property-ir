from hypothesis import settings, Verbosity, given, example
import pytest
from pathlib import Path

from sexpr.rewriting import add_weak_strong
from sexpr.base import AssertProperty, CoverProperty, IrContainer, RawSExprList
from sexpr.parsing import parse_raw_sexpr, parse_document
from sexpr.rewriting import rewrite_clocks, remove_empty_matches, reduce_primitives, rewrite_nexttime_primitives
from sexpr.primitives import ClkPropClocked
from tests.strategies import random_ir_clocked





def check_add_weak_strong(input_document_str: str, expected_output_document_str: str, visualize: bool = False) -> IrContainer:

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_add_weak_strong_input.png')

    container3: IrContainer = add_weak_strong(container1) # for output

    parse_document(expected_output_document, container2)

    if visualize:
        container3.show_graph(output_directory / 'check_add_weak_strong_output_before_renaming.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_add_weak_strong_expected_output.png')

    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container3.show_graph(output_directory / 'check_add_weak_strong_output_after_renaming.png')

    assert container3.weakly_equivalent(container2)

    return container3



def test_add_weak_strong_no_change_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-weak (clk-seq-bool (and a (not b))) ) )) )"""
    output_document: str = input_document
    check_add_weak_strong(input_document, output_document, visualize=False)

def test_add_weak_strong_no_change_2():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (cover-sequence (clk-seq-bool (and a (not b))) ) )"""
    output_document: str = input_document
    check_add_weak_strong(input_document, output_document, visualize=False)

def test_add_weak_strong_only_weak_seq():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-clk-seq (clk-seq-bool (and a (not b))) ) )) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-weak (clk-seq-bool (and a (not b))) ) )) )"""
    check_add_weak_strong(input_document, output_document, visualize=False)

def test_add_weak_strong_only_strong_seq():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (cover-property (clk-prop-clocked (true) (clk-prop-clk-seq (clk-seq-bool (and a (not b))) ) )) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (cover-property (clk-prop-clocked (true) (clk-prop-strong (clk-seq-bool (and a (not b))) ) )) )"""
    check_add_weak_strong(input_document, output_document, visualize=False)

def test_add_weak_strong_only_weak_bool():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-bool (and a (not b))) )) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-weak-bool (and a (not b))) )) )"""
    check_add_weak_strong(input_document, output_document, visualize=False)

def test_add_weak_strong_only_strong_bool():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (cover-property (clk-prop-clocked (true) (clk-prop-bool (and a (not b))) )) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (cover-property (clk-prop-clocked (true) (clk-prop-strong-bool (and a (not b))) )) )"""
    check_add_weak_strong(input_document, output_document, visualize=False)


def test_add_weak_strong_copy_graph():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare p (clk-prop-clocked (true) (clk-prop-bool (and a (not b))) ))
        (cover-property p)
        (assert-property p))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare gclk (true))
        (declare bool_expr (and a (not b)))
        (declare p (clk-prop-clocked gclk (clk-prop-weak-bool bool_expr) ))
        (declare p_strong (clk-prop-clocked gclk (clk-prop-strong-bool bool_expr) ))
        (cover-property p_strong)
        (assert-property p))"""
    check_add_weak_strong(input_document, output_document, visualize=False)


def test_add_weak_strong_with_cycle_no_change():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare-rec (declare p (clk-prop-clocked c (clk-prop-non-overlapped-implication (clk-seq-bool a) (clk-prop-and (clk-prop-strong-bool b) p) ))))
        (assert-property p))"""
    check_add_weak_strong(input_document, input_document)

def test_add_weak_strong_copy_graph_with_cycle():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare lhs_seq (clk-seq-bool a))
        (declare-rec (declare p (clk-prop-clocked c
            (clk-prop-non-overlapped-implication lhs_seq
            (clk-prop-and (clk-prop-bool b) p) ))))
        (assert-property p)
        (cover-property p)
        )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare lhs_seq (clk-seq-bool a))
        (declare-rec (declare p (clk-prop-clocked c
            (clk-prop-non-overlapped-implication lhs_seq
            (clk-prop-and (clk-prop-weak-bool b) p) ))))
        (declare-rec (declare p_strong (clk-prop-clocked c
            (clk-prop-non-overlapped-implication lhs_seq
            (clk-prop-and (clk-prop-strong-bool b) p_strong) ))))
        (assert-property p)
        (cover-property p_strong)
        )"""
    check_add_weak_strong(input_document, output_document, visualize=False)


def check_add_weak_strong_no_error(doc):
    doc_raw_sexpr: RawSExprList = parse_raw_sexpr(doc)
    container1: IrContainer = IrContainer()
    container3: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'weak_strong_input1.png')

    rewrite_nexttime_primitives(container1)
    #container1.show_graph(output_directory / 'weak_strong_input2.png')
    reduce_primitives(container1)
    #container1.show_graph(output_directory / 'weak_strong_input3.png')
    container3 = rewrite_clocks(container1)
    #container3.show_graph(output_directory / 'weak_strong_input4.png')

    container2: IrContainer = remove_empty_matches(container3)

    container4 = add_weak_strong(container2)
    container4.canonical_id_renaming(remove_unreachable_declared_nodes=True)
    #container4.show_graph(output_directory / 'weak_strong_output.png')


@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given((random_ir_clocked(final_node_type=ClkPropClocked, directive=CoverProperty)))
@example("""(document (declare-input l) (declare-input K) (declare-input k)
    (cover-property (let-rec
        (step0 (constant false))
        (step1 (constant true))
        (step2 (clk-prop-clocked step0 (clk-prop-strong-bool l)))
        step2)))""")
def test_add_weak_strong_random_no_error_cover(doc):
    check_add_weak_strong_no_error(doc)

@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given((random_ir_clocked(final_node_type=ClkPropClocked, directive=AssertProperty)))
def test_add_weak_strong_random_no_error(doc):
    check_add_weak_strong_no_error(doc)