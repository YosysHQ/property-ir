import logging
from pathlib import Path

from hypothesis import Verbosity, given, settings
from ir.automata import prepare_container_for_automaton_translation, simple_to_automaton
from ir.base import AssertProperty, IrContainer, Property, RawSExprList
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.simple_primitives import PropNot

from tests.strategies import random_ir_simple

logger = logging.getLogger(__name__)


def check_simple_to_automaton(input_document_str: str, expected_output_document_str: str, only_preprocessing: bool = False, visualize: bool = False) -> IrContainer:

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)
    parse_document(expected_output_document, container2)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_simple_to_automaton_input.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_simple_to_automaton_expected_output.png')

    prepare_container_for_automaton_translation(container1)

    if only_preprocessing:
        container1.canonical_id_renaming(remove_unreachable_declared_nodes=True)
        if visualize:
            container1.show_graph(output_directory / 'check_simple_to_automaton_preprocessed_input.png')
        assert container1 == container2
        return container1

    container3: IrContainer = simple_to_automaton(container1) # for output


    if visualize:
        container3.show_graph(output_directory / 'check_simple_to_automaton_output_before_renaming.png')


    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container3.show_graph(output_directory / 'check_simple_to_automaton_output_after_renaming.png')

    assert container2 == container3

    return container3



def test_simple_to_automaton_concat():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare s (seq-concat (seq-bool a) (seq-bool b)))
        (cover-sequence (clk-seq-seq s)) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare s
            (aut-call-ex
                (aut-read a (aut-acc (aut-false)) (aut-false))
                (aut-consume (true)
                    (aut-read b (aut-acc (aut-false)) (aut-false))
                    (aut-false))
            )
        )
        (cover-sequence (clk-seq-aut s)) )"""
    check_simple_to_automaton(input_document, output_document)


def test_simple_to_automaton_fusion():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare s (seq-fusion (seq-bool a) (seq-bool b)))
        (cover-sequence (clk-seq-seq s)) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare s
            (aut-call-ex
                (aut-read a (aut-acc (aut-false)) (aut-false))
                (aut-read b (aut-acc (aut-false)) (aut-false))
            )
        )
        (cover-sequence (clk-seq-aut s)) )"""
    check_simple_to_automaton(input_document, output_document)


def test_simple_to_automaton_preprocessing_repeat():
    input_document: str = """(document
        (declare-input a)
        (declare s (seq-repeat (range 3 5) (seq-bool a)))
        (cover-sequence (clk-seq-seq s)) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-rec
            (bool_a (seq-bool a))
            (declare s (seq-concat
                (seq-repeat (range 2 2) bool_a)
                (seq-repeat (range 1 3) bool_a)
            )))
        (cover-sequence (clk-seq-seq s)) )"""

    check_simple_to_automaton(input_document, output_document, only_preprocessing=True, visualize=False)


def test_simple_to_automaton_repeat():
    input_document: str = """(document
        (declare-input a)
        (declare s (seq-repeat (range 3 5) (seq-bool a)))
        (cover-sequence (clk-seq-seq s)) )"""
    output_document: str = """(document
        (declare-input a)
        (declare-rec
            (bool_a (aut-read a (aut-acc (aut-false)) (aut-false)))
            (declare s
                (aut-call-ex
                    (aut-repeat 2
                        bool_a
                    )
                    (aut-consume (true)
                        (aut-repeat-up-to 3
                            bool_a
                        )
                        (aut-false)
                    )
                )
            ))
        (cover-sequence (clk-seq-aut s)) )"""
    check_simple_to_automaton(input_document, output_document, visualize=False)


def test_simple_to_automaton_cycle():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec (declare p
            (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)) )
                (prop-and (prop-weak-bool b) p)
            )
        ))
        (assert-property (clk-prop-prop p))
        )"""
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-rec
            (lhs
                (aut-call-ex
                    (aut-read a (aut-acc (aut-false)) (aut-false))
                    (aut-consume (true)
                        (aut-read (true) (aut-acc (aut-false)) (aut-false))
                        (aut-false))
                )
            )
            (rhs
                (omega-and
                    (omega-call-ex-weak
                        (aut-read b (aut-acc (aut-false)) (aut-false))
                        (omega-true))
                    p
                )
            )
            (declare p
                (omega-call-all lhs rhs)
            )
        )
        (assert-property (clk-prop-omega p))
        )"""

    check_simple_to_automaton(input_document, output_document, visualize=False)




def check_simple_to_automaton_no_error(doc):
    doc_raw_sexpr: RawSExprList = parse_raw_sexpr(doc)
    container1: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container1)

    logger.info(doc)
    logger.info(doc_raw_sexpr)

    prepare_container_for_automaton_translation(container1)

    container2 = simple_to_automaton(container1)

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)


@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_simple(
    final_node_type=Property,
    directive=AssertProperty,
    primitive_filter = lambda node_type: not issubclass(node_type, PropNot)))
def test_simple_to_automaton_random_no_error(doc):
    check_simple_to_automaton_no_error(doc)
