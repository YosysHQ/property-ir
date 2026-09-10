import logging
from pathlib import Path

from hypothesis import Verbosity, example, given, settings
from sexpr.base import AssertProperty, CoverProperty, IrContainer, RawSExprList
from sexpr.parsing import parse_document, parse_raw_sexpr
from sexpr.primitives import ClkPropClocked
from sexpr.rewriting import (
    add_weak_strong,
    clocked_to_simple_pass,
    nnf,
    reduce_primitives,
    remove_empty_matches,
    rewrite_clocks,
    rewrite_nexttime_primitives,
)

from tests.strategies import random_ir_clocked

logger = logging.getLogger(__name__)



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
@given(random_ir_clocked(final_node_type=ClkPropClocked, directive=CoverProperty))
@example("""(document (declare-input l) (declare-input K) (declare-input k)
    (cover-property (let-rec
        (step0 (constant false))
        (step1 (constant true))
        (step2 (clk-prop-clocked step0 (clk-prop-strong-bool l)))
        step2)))""")
def test_add_weak_strong_random_no_error_cover(doc):
    check_add_weak_strong_no_error(doc)

@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_clocked(final_node_type=ClkPropClocked, directive=AssertProperty))
def test_add_weak_strong_random_no_error(doc):
    check_add_weak_strong_no_error(doc)





# TEST MAIN CLOCKED TO SIMPLE PASS




def check_clocked_to_simple(input_document_str: str, expected_output_document_str: str, visualize: bool = False) -> IrContainer:

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)
    parse_document(expected_output_document, container2)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_clocked_to_simple_input.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_clocked_to_simple_expected_output.png')

    container3 = clocked_to_simple_pass(container1)

    if visualize:
        container3.show_graph(output_directory / 'check_clocked_to_simple_output_before_renaming.png')

    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container3.show_graph(output_directory / 'check_clocked_to_simple_output_after_renaming.png')

    assert container3 == container2

    return container3




def test_clocked_to_simple_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-clocked (true) (clk-prop-weak (clk-seq-bool (and a (not b))) ) )) )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (assert-property (clk-prop-prop (prop-weak (seq-bool (and a (not b))) ) ) ))"""

    check_clocked_to_simple(input_document, output_document)


def test_clocked_to_simple_with_cycle():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec (declare p
            (clk-prop-not (clk-prop-overlapped-implication
                (clk-seq-concat (clk-seq-bool a) (clk-seq-bool (constant true)) )
                (clk-prop-not (clk-prop-and (clk-prop-weak-bool b) p))
            ))
        ))
        (assert-property (clk-prop-clocked (true) p))
        )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec (declare p
            (prop-not (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)))
                (prop-not (prop-and (prop-weak-bool b) p))
            ))
        ))
        (assert-property (clk-prop-prop p))
        )"""

    check_clocked_to_simple(input_document, output_document, visualize=False)


def test_clocked_to_simple_multiple_clocked():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec (declare p
            (clk-prop-not (clk-prop-clocked (true) (clk-prop-overlapped-implication
                (clk-seq-clocked (true) (clk-seq-clocked (true) (clk-seq-concat (clk-seq-bool a) (clk-seq-bool (constant true)) )))
                (clk-prop-not (clk-prop-and (clk-prop-weak-bool b) p))
            )))
        ))
        (assert-property (clk-prop-clocked (true) p))
        )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec (declare p
            (prop-not (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)))
                (prop-not (prop-and (prop-weak-bool b) p))
            ))
        ))
        (assert-property (clk-prop-prop p))
        )"""

    check_clocked_to_simple(input_document, output_document, visualize=False)



def check_clocked_to_simple_no_error(doc):
    doc_raw_sexpr: RawSExprList = parse_raw_sexpr(doc)
    container1: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container1)

    logger.info(doc)
    logger.info(doc_raw_sexpr)

    rewrite_nexttime_primitives(container1)
    reduce_primitives(container1)
    container2 = rewrite_clocks(container1)
    container3 = remove_empty_matches(container2)
    container4 = add_weak_strong(container3)
    container5 = clocked_to_simple_pass(container4)
    container6 = nnf(container5)
    container6.canonical_id_renaming(remove_unreachable_declared_nodes=True)



@example("""(document (declare-input G)
    (declare-input n)
    (declare-input hoh)
    (assert-property
        (let-rec (step0 (xor (true) (true)))
        (step1 (xor step0 (false)))
        (step2 (clk-seq-clocked step0 (clk-seq-bool n)))
        (step3 (clk-prop-strong-eventually-ranged (range 1 7) (clk-prop-weak-bool G)))
        (step4 (clk-seq-within step2 (clk-seq-bool G)))
        (step5 (clk-prop-implies step3 (clk-prop-weak-bool n)))
        (step6 (clk-seq-seq (seq-bool n)))
        (step7 (clk-seq-first-match step6))
        (step8 (clk-prop-strong-always (bounded-range 2 6) step5))
        (step9 (clk-seq-nonconsecutive-repeat (range 2 6) step1))
        (step10 (clk-seq-delay (range 2 $) step4))
        (step11 (clk-prop-sync-reject-on n step8))
        (step12 (xor step1 n))
        (step13 (clk-seq-seq (seq-bool n)))
        (step14 (clk-prop-clocked (true) step11))
        step14)))""")
@example("""(document (declare-input 0)
    (cover-property
        (let-rec
            (step0 (clk-prop-strong-eventually (clk-prop-weak-bool 0)))
            (step1 (clk-prop-clocked (true) step0))
            step1)))""")
@settings(verbosity=Verbosity.verbose, max_examples=30, deadline=1000)
@given(random_ir_clocked(final_node_type=ClkPropClocked, directive=CoverProperty))
def test_clocked_to_simple_random_no_error_cover(doc):
    check_clocked_to_simple_no_error(doc)

@example("""(document
    (declare-input gM) (declare-input V)
    (assert-property (let-rec
        (step0 (clk-prop-strong-until-with (clk-prop-strong-bool V) (clk-prop-weak-bool gM)))
        (step1 (clk-prop-clocked (true) step0))
        step1)))""")
@settings(verbosity=Verbosity.verbose, max_examples=30, deadline=1000)
@given(random_ir_clocked(final_node_type=ClkPropClocked, directive=AssertProperty))
def test_clocked_to_simple_random_no_error(doc):
    check_clocked_to_simple_no_error(doc)
