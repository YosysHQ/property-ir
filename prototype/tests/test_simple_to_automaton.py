import logging
from pathlib import Path

from hypothesis import Verbosity, example, given, settings
from ir.automata import prepare_container_for_automaton_translation, simple_to_automaton
from ir.base import (
    AssertProperty,
    FiniteAutomaton,
    IrContainer,
    NodeId,
    OmegaAutomaton,
    Property,
    PropertyIrNode,
    RawSExprList,
)
from ir.parsing import parse_document, parse_raw_sexpr, unparse_raw_sexpr
from ir.primitives.bool_primitives import (
    ChangingGclk,
    Eq,
    FallingGclk,
    Ite,
    RisingGclk,
    Xor,
)
from ir.primitives.clocked_primitives import ClkPropOmega
from ir.primitives.simple_primitives import (
    PropAcceptOn,
    PropNexttime,
    PropNot,
    PropOverlappedFollowedBy,
    PropOverlappedImplication,
    PropRefuted,
    PropRejectOn,
    PropStrong,
    PropStrongNexttime,
    PropWeak,
    SeqConcat,
    SeqFirstMatch,
    SeqFusion,
    SeqRepeat,
)
from pytest import mark

from tests.evaluate import (
    BoolMemoDict,
    MaybeBool,
    PropertyMemoDict,
    SequenceMemoDict,
    Trace,
    evaluate_property,
)
from tests.evaluate_automaton import evaluate_omega_automaton
from tests.strategies import random_ir_simple, random_ir_with_trace_simple

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
                    (omega-weak-read b (omega-true) (omega-false))
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



def check_automaton_random_property_evaluation(doc_and_trace: tuple[str, Trace], visualize=False):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    bool_results1: BoolMemoDict = {}
    seq_results1: SequenceMemoDict = {}
    prop_results1: PropertyMemoDict = {}

    input_container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), input_container)

    root_node_id1: NodeId = input_container.get_sink_nodes()[0]
    result1: MaybeBool = evaluate_property(root_node_id1, input_container, trace, bool_results1, seq_results1, prop_results1)

    prepare_container_for_automaton_translation(input_container)
    output_container: IrContainer = simple_to_automaton(input_container)

    logger.debug('input_doc: %s', doc)
    logger.debug('output_doc: %s', unparse_raw_sexpr(output_container.output_container()))

    if visualize:
        output_directory: Path = Path('./output')
        input_container.bypass_placeholders()
        output_container.bypass_placeholders()
        input_container.show_graph(output_directory / 'simple_property_input.png')
        output_container.show_graph(output_directory / 'automaton_output.png')

    root_node_id2: NodeId = output_container.get_sink_nodes()[0]
    root_node2: PropertyIrNode = output_container[root_node_id2]
    assert isinstance(root_node2, ClkPropOmega)
    omega_root_id: NodeId = root_node2.child
    result2: MaybeBool = evaluate_omega_automaton(omega_root_id, output_container, trace)

    logger.debug('input_doc: %s', doc)
    logger.debug('output_doc: %s', unparse_raw_sexpr(output_container.output_container()))
    logger.debug('trace: %s', trace)
    logger.debug('result1: %s', result1)
    logger.debug('result2: %s', result2)


    assert result1 == result2 or result1 == 'unknown' or result2 == 'unknown'

@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-until (prop-strong-bool 0) (prop-weak-bool 0))) step0)))',
     Trace(finite_part=(frozenset(),
       frozenset(),
       frozenset(),
       frozenset(),
       frozenset()),
      suffix='end')),
)
@settings(max_examples=100, deadline=500)
@given(random_ir_with_trace_simple(final_node_type=Property,
    primitive_filter=lambda node_type:
        not issubclass(node_type, (
            Xor, Ite, Eq, ChangingGclk, RisingGclk, FallingGclk,
            PropRefuted,
            PropNot,
            PropNexttime, PropStrongNexttime,
            PropAcceptOn, PropRejectOn,
            PropOverlappedImplication, PropOverlappedFollowedBy,
            SeqConcat, SeqFusion, PropStrong, PropWeak, SeqRepeat, SeqFirstMatch,
            FiniteAutomaton, OmegaAutomaton)),
    trace_min_length=5))
@mark.xfail(reason="working on this")
def test_automaton_random_property_evaluation_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_automaton_random_property_evaluation(doc_and_trace, visualize=False)

@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-until (prop-strong-bool 0) (prop-strong-bool 0))) step0)))',
     Trace(finite_part=(), suffix='end')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-strong-until-with (prop-weak-bool 0) (prop-weak-bool 0))) step0)))',
     Trace(finite_part=(), suffix='end')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-true )) (step1 (prop-until step0 step0)) step1)))',
     Trace(finite_part=(), suffix='bot_omega')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-true )) (step1 (prop-false )) (step2 (prop-until step0 step1)) step2)))',
     Trace(finite_part=(), suffix='bot_omega')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (future-gclk (true))) (step1 (prop-weak-bool step0)) step1)))',
     Trace(finite_part=(frozenset(),), suffix='end')))
@example(doc_and_trace=('(document (declare-input 0) (declare-input 1) (parse-sexpr (let-rec (step0 (prop-until (prop-strong-bool 1) (prop-weak-bool 0))) step0)))',
     Trace(finite_part=(frozenset({'1'}),), suffix='end')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-false )) (step1 (prop-until step0 step0)) step1)))',
     Trace(finite_part=(), suffix='top_omega')))
@example(doc_and_trace=('(document (declare-input 0) (parse-sexpr (let-rec (step0 (prop-weak-bool (true))) (step1 (initial )) (step2 (prop-weak-bool step1)) (step3 (prop-and step0 (prop-strong-bool 0))) (step4 (prop-until step2 step3)) step4)))',
     Trace(finite_part=(frozenset(), frozenset()), suffix='end')))
@settings(max_examples=1, deadline=500)
@given(random_ir_with_trace_simple(final_node_type=Property,
    primitive_filter=lambda node_type:
        not issubclass(node_type, (
            Xor, Ite, Eq, ChangingGclk, RisingGclk, FallingGclk,
            PropRefuted,
            PropNot,
            #PropTrue, PropFalse,
            PropNexttime, PropStrongNexttime,
            PropAcceptOn, PropRejectOn,
            PropOverlappedImplication, PropOverlappedFollowedBy,
            SeqConcat, SeqFusion, PropStrong, PropWeak, SeqRepeat, SeqFirstMatch,
            FiniteAutomaton, OmegaAutomaton)),
    trace_min_length=0))
@mark.xfail(reason="working on this")
def test_automaton_random_property_evaluation_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_automaton_random_property_evaluation(doc_and_trace, visualize=False)
