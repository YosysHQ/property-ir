from logging import getLogger
from pathlib import Path

from hypothesis import example, given, settings
from ir.automata import (
    prepare_container_for_automaton_translation,
    remove_all_subcalls,
    remove_single_subcall,
    simple_to_automaton,
    unroll_aut_repeat_primitives,
)
from ir.base import (
    ClockedProperty,
    ClockedSequence,
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
from ir.primitives.clocked_primitives import ClkPropOmega, ClkSeqAut
from ir.primitives.simple_primitives import (
    PropFalse,
    PropNexttime,
    PropNot,
    PropOverlappedImplication,
    PropRefuted,
    PropStrongNexttime,
    PropTrue,
    SeqFirstMatch,
    SeqIntersect,
    SeqNoMatch,
    SeqOr,
    SeqRepeat,
)

from tests.evaluate import (
    BoolMemoDict,
    FencepostPosition,
    MaybeBool,
    PropertyMemoDict,
    SequenceMemoDict,
    Trace,
    evaluate_property,
    sequence_matches,
)
from tests.evaluate_automaton import evaluate_finite_automaton, evaluate_omega_automaton
from tests.strategies import random_ir_with_trace_simple

logger = getLogger(__name__)



def check_subcall_removal(
    input_document_str: str,
    expected_output_document_str: str,
    single: bool = False,
    visualize: bool = False) -> IrContainer:

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)
    parse_document(expected_output_document, container2)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_subcall_removal_input.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_subcall_removal_expected_output.png')

    if single:
        root_id: NodeId = container1.directives[0].node_id
        remove_single_subcall(root_id, container1)
    else:
        unroll_aut_repeat_primitives(container1)
        remove_all_subcalls(container1)

    container1.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container1.show_graph(output_directory / 'check_subcall_removal_output.png')

    assert container1 == container2

    return container1



def test_remove_subcall_omega_call_all():

    input_document: str = """(document
        (declare-input a)

        (parse-sexpr (omega-call-all
            (aut-read a (aut-acc (aut-false)) (aut-false) )
            (omega-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)

        (parse-sexpr
            (omega-weak-read a (omega-true) (omega-true))
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=True, visualize=False)
    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcall_omega_call_ex_weak():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr (omega-call-ex-weak
            (aut-consume a
                (aut-acc
                    (aut-consume b
                        (aut-acc (aut-false))
                        (aut-false)
                    )
                )
                (aut-false)
            )
            (omega-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr
            (let-rec
                (successor (omega-true))
                (main
                    (omega-weak-consume a
                        (omega-or
                            (omega-weak-consume b successor (omega-false))
                            successor
                        )
                        (omega-false)
                    )
                )
                main)
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=True, visualize=False)
    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcall_omega_call_ex_strong():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr (omega-call-ex-strong
            (aut-consume a
                (aut-acc
                    (aut-consume b
                        (aut-acc (aut-false))
                        (aut-false)
                    )
                )
                (aut-false)
            )
            (omega-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr
            (let-rec
                (successor (omega-true))
                (main
                    (omega-strong-consume a
                        (omega-or
                            (omega-strong-consume b successor (omega-false))
                            successor
                        )
                        (omega-false)
                    )
                )
                main)
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=True, visualize=False)
    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcall_aut_call_ex():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr (aut-call-ex
            (aut-consume a
                (aut-acc
                    (aut-consume b
                        (aut-acc (aut-false))
                        (aut-false)
                    )
                )
                (aut-false)
            )
            (aut-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr
            (let-rec
                (successor (aut-true))
                (main
                    (aut-consume a
                        (aut-or
                            (aut-consume b successor (aut-false))
                            successor
                        )
                        (aut-false)
                    )
                )
                main)
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=True, visualize=False)
    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcall_aut_call_first():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr (aut-call-first
            (aut-consume a
                (aut-acc
                    (aut-consume b
                        (aut-acc (aut-false))
                        (aut-false)
                    )
                )
                (aut-false)
            )
            (aut-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr
            (let-rec
                (successor (aut-true))
                (main
                    (aut-consume a
                        successor
                        (aut-false)
                    )
                )
                main)
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=True, visualize=False)
    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcalls_simple():

    input_document: str = """(document
        (declare-input a)

        (declare subcall (omega-call-all
            (aut-read a (aut-acc (aut-false)) (aut-false) )
            (omega-true)
        ))

        (parse-sexpr (omega-or subcall (omega-false)))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare subcall (omega-weak-read a (omega-true) (omega-true)))
        (parse-sexpr (omega-or subcall (omega-false)) )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcalls_nested():

    input_document: str = """(document
        (declare-input a)

        (declare subcall2
            (aut-call-ex
                (aut-read a (aut-acc (aut-false)) (aut-false) )
                (aut-acc (aut-false))
            )
        )

        (declare subcall1 (omega-call-all
            subcall2
            (omega-true)
        ))

        (parse-sexpr (omega-or subcall1 (omega-false)))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare subcall1 (omega-weak-read a (omega-true) (omega-true)))
        (parse-sexpr (omega-or subcall1 (omega-false)) )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcalls_doubly_nested():

    input_document: str = """(document
        (declare-input a)

        (declare subcall3
            (aut-call-ex
                (aut-read a (aut-acc (aut-false)) (aut-false) )
                (aut-acc (aut-false))
            )
        )

        (declare subcall2
            (aut-call-ex
                subcall3
                (aut-acc (aut-false))
            )
        )

        (declare subcall1 (omega-call-all
            subcall2
            (omega-true)
        ))

        (parse-sexpr (omega-or subcall1 (omega-false)))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare subcall1 (omega-weak-read a (omega-true) (omega-true)))
        (parse-sexpr (omega-or subcall1 (omega-false)) )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcalls_multiple_sinks():

    input_document: str = """(document
        (declare-input a)

        (declare subcall3
            (aut-call-ex
                (aut-read a (aut-acc (aut-false)) (aut-false) )
                (aut-acc (aut-false))
            )
        )

        (declare subcall2
            (aut-call-ex subcall3 (aut-acc (aut-false)) )
        )

        (declare subcall1 (omega-call-all
            subcall2
            (omega-true)
        ))

        (declare subcall4
            (aut-call-ex subcall3 (aut-acc (aut-false)) )
        )

        (parse-sexpr subcall2)
        (parse-sexpr subcall3)
        (parse-sexpr subcall4)
        (parse-sexpr (omega-or subcall1 (omega-false)))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare subcall1 (omega-weak-read a (omega-true) (omega-true)))
        (declare subcall2 (aut-read a (aut-acc (aut-false)) (aut-false)))
        (declare subcall3 (aut-read a (aut-acc (aut-false)) (aut-false)))
        (declare subcall4 (aut-read a (aut-acc (aut-false)) (aut-false)))
        (parse-sexpr subcall2)
        (parse-sexpr subcall3)
        (parse-sexpr subcall4)
        (parse-sexpr (omega-or subcall1 (omega-false)) )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)

def test_remove_subcalls_reused_automaton():

    input_document: str = """(document
        (declare-input a)

        (declare subcall
            (aut-read a (aut-acc (aut-false)) (aut-false) )
        )

        (parse-sexpr (omega-call-all
            subcall
            (omega-true)
        ))

        (parse-sexpr (omega-call-ex-strong
            (aut-consume a
                (aut-acc
                    subcall
                )
                (aut-false)
            )
            (omega-true)
        ))

    )"""

    expected_output: str = """(document
        (declare-input a)

        (parse-sexpr
            (omega-weak-read a (omega-true) (omega-true))
        )

        (parse-sexpr
            (let-rec
                (successor (omega-true))
                (main
                    (omega-strong-consume a
                        (omega-or
                            (omega-strong-read a successor (omega-false))
                            successor
                        )
                        (omega-false)
                    )
                )
                main)
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def test_remove_subcalls_graph_with_cycle():

    input_document: str = """(document
        (declare-input a)

        (declare-rec
            (subcall (omega-call-all
                (aut-read a (aut-acc (aut-false)) (aut-false) )
                succ)
            )
            (declare succ
                (omega-weak-consume (true)
                    subcall
                    (omega-false)
                )
            )
        )

        (parse-sexpr succ)
    )"""

    expected_output: str = """(document
        (declare-input a)

        (declare-rec
            (subcall (omega-weak-read a succ (omega-true)))
            (declare succ
                (omega-weak-consume (true)
                    subcall
                    (omega-false)
                )
            )
        )

        (parse-sexpr succ)
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)


def check_remove_subcalls_random_property_evaluation(doc_and_trace: tuple[str, Trace], visualize=False):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    bool_results1: BoolMemoDict = {}
    seq_results1: SequenceMemoDict = {}
    prop_results1: PropertyMemoDict = {}

    input_container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), input_container)


    output_directory: Path = Path('./output')
    if visualize:
        input_container.canonical_id_renaming(remove_unreachable_declared_nodes=True)
        input_container.show_graph(output_directory / 'simple_property_input.png')

    prepare_container_for_automaton_translation(input_container)
    output_container: IrContainer = simple_to_automaton(input_container)

    if visualize:
        output_container.canonical_id_renaming(remove_unreachable_declared_nodes=True)
        output_container.show_graph(output_directory / 'automaton_input.png')

    unroll_aut_repeat_primitives(output_container)
    remove_all_subcalls(output_container)

    logger.debug('input_doc: %s', doc)
    logger.debug('output_doc: %s', unparse_raw_sexpr(output_container.output_container()))

    if visualize:
        output_container.canonical_id_renaming(remove_unreachable_declared_nodes=True)
        output_container.show_graph(output_directory / 'automaton_output.png')

    root_node_id1: NodeId = input_container.get_sink_nodes()[0]

    root_node_id2: NodeId = output_container.get_sink_nodes()[0]
    root_node2: PropertyIrNode = output_container[root_node_id2]

    logger.debug('input_doc: %s', doc)
    logger.debug('output_doc: %s', unparse_raw_sexpr(output_container.output_container()))
    logger.debug('trace: %s', trace)

    if isinstance(root_node2, ClkPropOmega):
        omega_root_id: NodeId = root_node2.child
        prop_result1: MaybeBool = evaluate_property(root_node_id1, input_container, trace, FencepostPosition(('at', 0)), bool_results1, seq_results1, prop_results1)
        prop_result2: MaybeBool = evaluate_omega_automaton(omega_root_id, output_container, trace)

        logger.debug('result1: %s', prop_result1)
        logger.debug('result2: %s', prop_result2)

        assert prop_result1 == prop_result2 or prop_result1 == 'unknown' or prop_result2 == 'unknown'

    elif isinstance(root_node2, ClkSeqAut):
        omega_root_id: NodeId = root_node2.child
        seq_result1: frozenset[FencepostPosition] = sequence_matches(root_node_id1, input_container, trace, FencepostPosition(('at', 0)), bool_results1, seq_results1)
        seq_result2: list[FencepostPosition] = evaluate_finite_automaton(omega_root_id, output_container, trace, FencepostPosition(('at', 0)))
        seq_result2_adjusted: frozenset[FencepostPosition] = frozenset([match.next_pos(trace) for match in seq_result2])
        # the automaton accepts 1 step earlier than the sequence match - adjust matches for that

        logger.debug('result1: %s', seq_result1)
        logger.debug('result2: %s', seq_result2_adjusted)

        assert seq_result1 == seq_result2_adjusted or \
            FencepostPosition('unknown') in seq_result1 or \
            FencepostPosition('unknown') in seq_result2_adjusted
    else:
        raise ValueError('Cannot evaluate root node other than ClkPropOmega or ClkSeqAut')



forbidden_primitives = (
    Xor, Ite, Eq, ChangingGclk, RisingGclk, FallingGclk, # rewritten in earlier steps
    PropTrue, PropFalse, SeqNoMatch, # cannot occur in the input
    PropNot, # rewritten in nnf rewriting
    PropRefuted, # test this when aut-refuted is implemented
    PropNexttime, PropStrongNexttime, # rewritten in clocked properties
    SeqIntersect, # TODO: test this when alternation removal is implemented
    FiniteAutomaton, OmegaAutomaton, ClockedProperty, ClockedSequence)

# these are the primitives that could not be checked before, because they require subcalls:
# SeqConcat, SeqFusion, PropStrong, PropWeak, PropOverlappedFollowedBy,
# PropOverlappedImplication -> this still requires that there is no seq-or in the subcall automaton
# because it gets converted to aut-and
# TODO: test PropOverlappedImplication more when alternation removal is implemented
# TODO: test SeqFirstMatch more when determinization is implemented


@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-concat (seq-bool 0) (seq-bool 0)))
        (step1 (seq-concat step0 step0))
        (step2 (seq-concat step1 step0))
        (step3 (prop-strong step2)) step3)))""",
     Trace(finite_part=(), suffix='end')))
@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-concat (seq-bool 0) (seq-bool 0)))
        (step1 (seq-concat step0 step0 step0))
        (step2 (prop-strong step1)) step2)))""",
     Trace(finite_part=(), suffix='end')))
@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-fusion (seq-bool 0) (seq-bool 0) (seq-bool 0)))
        (step1 (prop-strong step0))
        step1)))""",
     Trace(finite_part=(frozenset({'0'}), frozenset()), suffix='end')))
@settings(max_examples=40, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=Property,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (PropOverlappedImplication, SeqFirstMatch)),
    trace_min_length=0))
def test_remove_subcalls_random_property_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (prop-accept-on (true) (prop-weak-bool 0)))
        (step1 (prop-and step0 step0)) step1)))""",
                Trace(finite_part=(frozenset(),
                  frozenset(),
                  frozenset(),
                  frozenset(),
                  frozenset()),
                 suffix='end')))
@settings(max_examples=40, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=Property,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (PropOverlappedImplication, SeqFirstMatch)),
    trace_min_length=5))
def test_remove_subcalls_random_property_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

@settings(max_examples=40, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=PropOverlappedImplication,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (SeqOr, SeqFirstMatch)),
    trace_min_length=5))
def test_remove_subcalls_random_property_implication_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

@settings(max_examples=40, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=PropOverlappedImplication,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (SeqOr, SeqFirstMatch)),
    trace_min_length=0))
def test_remove_subcalls_random_property_implication_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

# TODO test this when determinization has been implementetd
#@example(doc_and_trace = ("""(document (declare-input 0) (declare-input 1)
#    (parse-sexpr (let-rec
#        (step0 (seq-repeat (range 1 $) (seq-bool 0)))
#        (step1 (seq-first-match step0))
#        step1)))""",
#    Trace(finite_part=(frozenset({'0'}), frozenset({'0'})), suffix='end')))
@example(doc_and_trace = ("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-first-match (seq-bool 0))) step0)))""",
    Trace(finite_part=(frozenset({'0'}), frozenset(), frozenset(), frozenset(), frozenset()), suffix='end')))
@example(doc_and_trace = ("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-first-match (seq-bool 0))) step0)))""",
    Trace(finite_part=(frozenset({'0'}),), suffix='end')))
@settings(max_examples=40, deadline=4000)
@given(random_ir_with_trace_simple(final_node_type=SeqFirstMatch,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (SeqOr, SeqRepeat)),
    trace_min_length=5))
def test_remove_subcalls_random_sequence_first_match_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-concat (seq-bool 0) (seq-bool 0) (seq-bool 0) (seq-bool 0) (seq-bool 0)))
        (step1 (seq-concat step0 step0))
        (step2 (seq-concat step1 step1 step0 step1 step1))
        (step3 (seq-concat step2 step0 step0 step0))
        (step4 (seq-concat step3 step3 step0))
        (step5 (seq-first-match step4)) step5)))""",
     Trace(finite_part=(), suffix='end')))
@settings(max_examples=40, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=SeqFirstMatch,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (SeqOr, SeqRepeat)),
    trace_min_length=0))
def test_remove_subcalls_random_sequence_first_match_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)



#---------------------------+
# TEST REPEAT PRIMITIVES  |
#---------------------------+

def test_unroll_repeat():

    input_document: str = """(document
        (declare-input a)
        (declare subcall (aut-read a (aut-acc (aut-false)) (aut-false) ))
        (parse-sexpr (aut-repeat 2 subcall))
    )"""

    expected_output: str = """(document
        (declare-input a)

        (parse-sexpr
            (aut-read a
                (aut-consume (true)
                    (aut-read a
                        (aut-acc (aut-false))
                        (aut-false)
                    )
                    (aut-false)
                )
                (aut-false)
            )
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)

def test_unroll_repeat_up_to():

    input_document: str = """(document
        (declare-input a)
        (declare subcall (aut-read a (aut-acc (aut-false)) (aut-false) ) )
        (parse-sexpr (aut-repeat-up-to 2 subcall))
    )"""

    expected_output: str = """(document
        (declare-input a)

        (parse-sexpr
            (aut-read a
                (aut-or
                    (aut-acc (aut-false))
                    (aut-consume (true)
                        (aut-read a
                            (aut-acc (aut-false))
                            (aut-false)
                        )
                        (aut-false)
                    )
                )
                (aut-false)
            )
        )
    )"""

    check_subcall_removal(input_document, expected_output, single=False, visualize=False)

@settings(max_examples=50, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=SeqRepeat,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (PropOverlappedImplication, SeqFirstMatch)),
    trace_min_length=5))
def test_remove_subcalls_random_sequence_seq_repeat_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)

@example(doc_and_trace=("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (seq-repeat (range 1 5) (seq-bool 0)))
        step0)))""",
    Trace(finite_part=(frozenset({'0'}), frozenset({'0'})), suffix='top_omega')))
@settings(max_examples=50, deadline=10000)
@given(random_ir_with_trace_simple(final_node_type=SeqRepeat,
    primitive_filter=lambda node_type:
        not issubclass(node_type, forbidden_primitives + (PropOverlappedImplication, SeqFirstMatch)),
    trace_min_length=0))
def test_remove_subcalls_random_sequence_seq_repeat_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_remove_subcalls_random_property_evaluation(doc_and_trace, visualize=False)
