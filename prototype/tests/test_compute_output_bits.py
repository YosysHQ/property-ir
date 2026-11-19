from logging import getLogger

from hypothesis import Verbosity, given, settings
from ir.automata import EvaluationResult, compute_output_bits_omega
from ir.base import Bool, FiniteAutomaton, IrContainer, NodeId, OmegaAutomaton
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.automata_primitives import (
    OmegaCallAll,
    OmegaCallExStrong,
    OmegaCallExWeak,
)

from tests.strategies import random_ir

logger = getLogger(__name__)



def test_output_bits_finite():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare aut1 (aut-true))
        (declare aut2 (aut-false))
        (declare aut3 (aut-consume a (aut-true) (aut-false)))
        (declare aut4 (aut-consume b (aut-true) (aut-false)))
        (declare aut5 (aut-acc (aut-false)))
        (declare aut6 (aut-read a (aut-acc (aut-false)) (aut-false) ))
        (declare aut7 (aut-read b (aut-acc (aut-false)) (aut-false) ))

        (declare aut8 (aut-consume a (aut-consume b (aut-true) (aut-false)) (aut-false)))
        (declare aut9 (aut-consume a (aut-consume b (aut-false) (aut-false)) (aut-false)))
        (declare aut10 (aut-consume a (aut-consume b (aut-acc (aut-false)) (aut-false)) (aut-false)))

        (declare aut11 (aut-consume a
            (aut-consume b
                (aut-consume b
                    (aut-acc (aut-false))
                    (aut-false))
                (aut-false))
            (aut-false))
        )

        (declare-rec (declare aut12
            (aut-consume a
                (aut-acc aut12)
                (aut-false)
            )
        ))

        (declare aut13 (aut-read a (aut-true) (aut-false) ))

        (parse-sexpr aut1)
        (parse-sexpr aut2)
        (parse-sexpr aut3)
        (parse-sexpr aut4)
        (parse-sexpr aut5)
        (parse-sexpr aut6)
        (parse-sexpr aut7)
        (parse-sexpr aut8)
        (parse-sexpr aut9)
        (parse-sexpr aut10)
        (parse-sexpr aut11)
        (parse-sexpr aut12)
        (parse-sexpr aut13)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    #aut1: NodeId = container.get_node_id_by_name('aut1')
    #aut2: NodeId = container.get_node_id_by_name('aut2')
    #aut3: NodeId = container.get_node_id_by_name('aut3')
    #aut4: NodeId = container.get_node_id_by_name('aut4')
    #aut5: NodeId = container.get_node_id_by_name('aut5')
    #aut6: NodeId = container.get_node_id_by_name('aut6')
    #aut7: NodeId = container.get_node_id_by_name('aut7')

    #aut8: NodeId = container.get_node_id_by_name('aut8')
    #aut9: NodeId = container.get_node_id_by_name('aut9')
    #aut10: NodeId = container.get_node_id_by_name('aut10')

    #aut11: NodeId = container.get_node_id_by_name('aut11')
    #aut12: NodeId = container.get_node_id_by_name('aut12')

    #aut13: NodeId = container.get_node_id_by_name('aut13')

    #evaluation_results: dict[NodeId, bool] = compute_output_bits_finite(container)

    # TODO




def test_output_bits_omega_finite_part_linear():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare omega1 (omega-true))
        (declare omega2 (omega-false))
        (declare omega3 (omega-weak-consume a (omega-true) (omega-false)))
        (declare omega4 (omega-weak-consume a (omega-true) (omega-true)))
        (declare omega5 (omega-strong-consume a (omega-true) (omega-false)))

        (declare omega7 (omega-weak-consume a (omega-weak-consume b (omega-true) (omega-false)) (omega-false)))
        (declare omega8 (omega-weak-consume a (omega-weak-consume b (omega-false) (omega-false)) (omega-false)))

        (declare omega9 (omega-weak-consume a (omega-strong-consume b (omega-true) (omega-false)) (omega-false)))
        (declare omega10 (omega-strong-consume a (omega-weak-consume b (omega-true) (omega-false)) (omega-false)))

        (parse-sexpr omega1)
        (parse-sexpr omega2)
        (parse-sexpr omega3)
        (parse-sexpr omega4)
        (parse-sexpr omega5)
        (parse-sexpr omega7)
        (parse-sexpr omega8)
        (parse-sexpr omega9)
        (parse-sexpr omega10)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    omega1: NodeId = container.get_node_id_by_name('omega1')
    omega2: NodeId = container.get_node_id_by_name('omega2')
    omega3: NodeId = container.get_node_id_by_name('omega3')
    omega4: NodeId = container.get_node_id_by_name('omega4')
    omega5: NodeId = container.get_node_id_by_name('omega5')
    omega7: NodeId = container.get_node_id_by_name('omega7')
    omega8: NodeId = container.get_node_id_by_name('omega8')
    omega9: NodeId = container.get_node_id_by_name('omega9')
    omega10: NodeId = container.get_node_id_by_name('omega10')

    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)

    assert evaluation_results[omega1] == EvaluationResult.HOLDS_STRONGLY
    assert evaluation_results[omega2] == EvaluationResult.FAILS
    assert evaluation_results[omega3] == EvaluationResult.HOLDS
    assert evaluation_results[omega4] == EvaluationResult.HOLDS
    assert evaluation_results[omega5] == EvaluationResult.PENDING
    assert evaluation_results[omega7] == EvaluationResult.HOLDS
    assert evaluation_results[omega8] == EvaluationResult.FAILS
    assert evaluation_results[omega9] == EvaluationResult.PENDING
    assert evaluation_results[omega10] == EvaluationResult.PENDING



def test_output_bits_omega_infinite_suffix_cycle():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare-rec (declare omega1
            (omega-weak-consume-acc a
                omega1
                (omega-false)
            )
        ))

        (declare-rec (declare omega2
            (omega-weak-consume a
                omega2
                (omega-false)
            )
        ))

        (declare or1 (omega-or omega1 omega2))
        (declare and1 (omega-and omega1 omega2))

        (declare-rec (declare omega1_strong
            (omega-strong-consume-acc a
                omega1_strong
                (omega-false)
            )
        ))

        (declare-rec (declare omega2_strong
            (omega-strong-consume a
                omega2_strong
                (omega-false)
            )
        ))

        (declare or_strong1 (omega-or omega1 omega1_strong))
        (declare and_strong1 (omega-and omega1 omega1_strong))

        (parse-sexpr omega1)
        (parse-sexpr omega2)
        (parse-sexpr or1)
        (parse-sexpr and1)
        (parse-sexpr and1)
        (parse-sexpr omega1_strong)
        (parse-sexpr omega2_strong)
        (parse-sexpr or_strong1)
        (parse-sexpr and_strong1)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    omega1: NodeId = container.get_node_id_by_name('omega1')
    omega2: NodeId = container.get_node_id_by_name('omega2')
    or1: NodeId = container.get_node_id_by_name('or1')
    and1: NodeId = container.get_node_id_by_name('and1')
    omega1_strong: NodeId = container.get_node_id_by_name('omega1_strong')
    omega2_strong: NodeId = container.get_node_id_by_name('omega2_strong')
    or_strong1: NodeId = container.get_node_id_by_name('or_strong1')
    and_strong1: NodeId = container.get_node_id_by_name('and_strong1')

    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)

    assert evaluation_results[omega1] == EvaluationResult.HOLDS
    assert evaluation_results[omega2] == EvaluationResult.FAILS
    assert evaluation_results[or1] == EvaluationResult.HOLDS
    assert evaluation_results[and1] == EvaluationResult.FAILS
    assert evaluation_results[omega1_strong] == EvaluationResult.PENDING
    assert evaluation_results[omega2_strong] == EvaluationResult.FAILS
    assert evaluation_results[or_strong1] == EvaluationResult.HOLDS
    assert evaluation_results[and_strong1] == EvaluationResult.PENDING


def test_output_bits_omega_cycle_and_or():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare-rec (declare always_a
            (omega-weak-consume-acc a
                always_a
                (omega-false)
            )
        ))

        (declare omega_a (omega-weak-consume a (omega-true) (omega-false)))
        (declare omega_b (omega-weak-consume b (omega-true) (omega-false)))
        (declare omega_b_read (omega-weak-read b (omega-weak-consume (true) (omega-true) (omega-false)) (omega-false)))

        (declare omega_a_strong (omega-strong-consume a (omega-true) (omega-false)))
        (declare omega_b_strong (omega-strong-consume b (omega-true) (omega-false)))

        (declare-rec
            (declare a_until_b (omega-or omega_b
                (omega-and
                    omega_a
                    (omega-weak-consume-acc (true) a_until_b (omega-false))))))

        (declare-rec
            (declare a_strong_until_with_b (omega-and omega_a_strong
                (omega-or
                    omega_b_strong
                    (omega-strong-consume (true) a_strong_until_with_b (omega-false))))))

        (declare-rec
            (declare a_until_b_read (omega-or omega_b
                (omega-and
                    omega_a
                    (omega-weak-read c (omega-weak-consume-acc (true) a_until_b_read (omega-false)) (omega-false))
                )
            ))
        )

        (declare-rec
            (declare a_until_b_read_2 (omega-or omega_b
                (omega-weak-read c
                    (omega-and
                        omega_a
                        (omega-weak-consume-acc (true) a_until_b_read_2 (omega-false))
                    )
                (omega-false))
            ))
        )

        (declare-rec
            (declare b_until_always_a (omega-or always_a
                (omega-and
                    omega_b_read
                    (omega-weak-consume-acc (true) b_until_always_a (omega-false))))))

        (parse-sexpr a_until_b)
        (parse-sexpr a_strong_until_with_b)
        (parse-sexpr a_until_b_read)
        (parse-sexpr a_until_b_read_2)
        (parse-sexpr b_until_always_a)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    a_until_b: NodeId = container.get_node_id_by_name('a_until_b')
    a_strong_until_with_b: NodeId = container.get_node_id_by_name('a_strong_until_with_b')
    a_until_b_read: NodeId = container.get_node_id_by_name('a_until_b_read')
    a_until_b_read_2: NodeId = container.get_node_id_by_name('a_until_b_read_2')
    b_until_always_a: NodeId = container.get_node_id_by_name('b_until_always_a')

    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)

    assert evaluation_results[a_until_b] == EvaluationResult.HOLDS
    assert evaluation_results[a_strong_until_with_b] == EvaluationResult.PENDING
    assert evaluation_results[a_until_b_read] == EvaluationResult.HOLDS
    assert evaluation_results[a_until_b_read_2] == EvaluationResult.HOLDS
    assert evaluation_results[b_until_always_a] == EvaluationResult.HOLDS



def test_output_bits_omega_conflicting_obligations():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare-input d)

        (declare-rec
            (declare start1 (omega-or and1 and2))
            (and1 (omega-and path1 path2))
            (and2 (omega-and path3 path4))
            (path1 (omega-weak-consume a start1 (omega-false)))
            (path2 (omega-weak-consume-acc b start1 (omega-false)))
            (path3 (omega-weak-consume c start1 (omega-false)))
            (path4 (omega-weak-consume-acc d start1 (omega-false)))
        )

        (declare-rec
            (declare start6 (omega-or and1 and2))
            (and1 (omega-and path1 path2))
            (and2 (omega-and path3 path4))
            (path1 (omega-weak-consume-acc a branch1 (omega-false)))
            (path2 (omega-weak-consume-acc b branch2 (omega-false)))
            (path3 (omega-weak-consume c branch1 (omega-false)))
            (path4 (omega-weak-consume-acc d branch2 (omega-false)))
            (branch1 (omega-weak-consume a start6 (omega-false)))
            (branch2 (omega-weak-consume b start6 (omega-false)))
        )

        (parse-sexpr start1)
        (parse-sexpr start6)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    start1: NodeId = container.get_node_id_by_name('start1')
    start6: NodeId = container.get_node_id_by_name('start6')

    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)

    assert evaluation_results[start1] == EvaluationResult.FAILS
    assert evaluation_results[start6] == EvaluationResult.HOLDS



def test_output_bits_omega_accept_reject_on():

    doc_str: str = """(document

        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare omega_a (omega-weak-consume a (omega-true) (omega-false)))
        (declare omega_b (omega-weak-consume b (omega-true) (omega-false)))

        (declare-rec
            (declare a_until_b (omega-or omega_b
                (omega-and
                    omega_a
                    (omega-weak-consume-acc (true) a_until_b (omega-false))))))

        (declare omega_acc_until (omega-accept-on c a_until_b))
        (declare omega_rej_until (omega-reject-on c a_until_b))

        (declare omega_acc_until_nested (omega-accept-on c (omega-reject-on c a_until_b)))
        (declare omega_rej_until_nested (omega-reject-on c (omega-accept-on c a_until_b)))

        (declare-rec (declare omega_accept_cycle
            (omega-accept-on c
                (omega-strong-consume-acc a
                    omega_accept_cycle
                    (omega-false)
                )
            )
        ))

        (declare-rec (declare omega_reject_cycle
            (omega-reject-on c
                (omega-strong-consume-acc a
                    omega_reject_cycle
                    (omega-false)
                )
            )
        ))

        (parse-sexpr omega_acc_until)
        (parse-sexpr omega_rej_until)
        (parse-sexpr omega_acc_until_nested)
        (parse-sexpr omega_rej_until_nested)
        (parse-sexpr omega_accept_cycle)
        (parse-sexpr omega_reject_cycle)

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    omega_acc_until: NodeId = container.get_node_id_by_name('omega_acc_until')
    omega_rej_until: NodeId = container.get_node_id_by_name('omega_rej_until')
    omega_acc_until_nested: NodeId = container.get_node_id_by_name('omega_acc_until_nested')
    omega_rej_until_nested: NodeId = container.get_node_id_by_name('omega_rej_until_nested')
    omega_accept_cycle: NodeId = container.get_node_id_by_name('omega_accept_cycle')
    omega_reject_cycle: NodeId = container.get_node_id_by_name('omega_reject_cycle')

    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)

    assert evaluation_results[omega_acc_until] == EvaluationResult.HOLDS
    assert evaluation_results[omega_rej_until] == EvaluationResult.HOLDS
    assert evaluation_results[omega_acc_until_nested] == EvaluationResult.HOLDS
    assert evaluation_results[omega_rej_until_nested] == EvaluationResult.HOLDS
    assert evaluation_results[omega_accept_cycle] == EvaluationResult.PENDING
    assert evaluation_results[omega_reject_cycle] == EvaluationResult.PENDING


@settings(verbosity=Verbosity.verbose, max_examples=100, deadline=500)
@given(random_ir(
    final_node_type=OmegaAutomaton,
    primitive_filter=lambda node_type:
        issubclass(node_type, (OmegaAutomaton, FiniteAutomaton, Bool)) and
        not issubclass(node_type, (OmegaCallAll, OmegaCallExStrong, OmegaCallExWeak))))
def test_output_bits_omega_random_no_error(doc):

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), container)
    root_node_id: NodeId = container.get_sink_nodes()[0]
    root_node_repr: NodeId = container.merged_nodes.find(root_node_id)
    evaluation_results: dict[NodeId, EvaluationResult] = compute_output_bits_omega(container)
    assert root_node_repr in evaluation_results
