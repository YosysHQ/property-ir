from logging import getLogger
from pathlib import Path

from hypothesis import Verbosity, given, settings
from ir.base import Bool, FiniteAutomaton, IrContainer, NodeId, OmegaAutomaton
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.automata_primitives import (
    AutAcc,
    AutConsume,
    AutRead,
    AutRefuted,
    AutRepeat,
    AutRepeatUpTo,
    OmegaAcceptOn,
    OmegaCallAll,
    OmegaCallExStrong,
    OmegaCallExWeak,
    OmegaRejectOn,
)

from tests.evaluate import FencepostPosition, MaybeBool, Trace
from tests.evaluate_automaton import (
    Configuration,
    conf_and,
    conf_or,
    evaluate_finite_automaton,
    evaluate_finite_automaton_primitive,
    evaluate_omega_automaton,
    simplify_conf,
)
from tests.strategies import random_ir_with_trace

logger = getLogger(__name__)


def test_automaton_aut_consume():

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


    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    aut1: NodeId = container.get_node_id_by_name('aut1')
    aut2: NodeId = container.get_node_id_by_name('aut2')
    aut3: NodeId = container.get_node_id_by_name('aut3')
    aut4: NodeId = container.get_node_id_by_name('aut4')
    aut5: NodeId = container.get_node_id_by_name('aut5')
    aut6: NodeId = container.get_node_id_by_name('aut6')
    aut7: NodeId = container.get_node_id_by_name('aut7')

    aut8: NodeId = container.get_node_id_by_name('aut8')
    aut9: NodeId = container.get_node_id_by_name('aut9')
    aut10: NodeId = container.get_node_id_by_name('aut10')

    aut11: NodeId = container.get_node_id_by_name('aut11')
    aut12: NodeId = container.get_node_id_by_name('aut12')

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'b'}),
    ), suffix='end')

    trace1_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='top_omega')

    result1 = evaluate_finite_automaton_primitive(aut1, container, trace1, FencepostPosition(('at', 0)))
    assert result1[0] == frozenset([frozenset([aut1])])
    assert result1[1] == True

    result2 = evaluate_finite_automaton_primitive(aut2, container, trace1, FencepostPosition(('at', 0)))
    assert result2[0] == frozenset([frozenset([aut2])])
    assert result2[1] == False

    result3 = evaluate_finite_automaton_primitive(aut3, container, trace1, FencepostPosition(('at', 0)))
    aut3_node = container[aut3]
    assert(isinstance(aut3_node, AutConsume))
    assert result3[0] == frozenset([frozenset([aut3_node.child2])])
    assert result3[1] == False
    result3_2 = evaluate_finite_automaton_primitive(aut3_node.child2, container, trace1, FencepostPosition(('at', 1)))
    assert result3_2[0] == frozenset([frozenset([aut3_node.child2])])
    assert result3_2[1] == True

    result4 = evaluate_finite_automaton_primitive(aut4, container, trace1, FencepostPosition(('at', 0)))
    aut4_node = container[aut4]
    assert(isinstance(aut4_node, AutConsume))
    assert result4[0] == frozenset([frozenset([aut4_node.child3])])
    assert result4[1] == False

    result5 = evaluate_finite_automaton_primitive(aut5, container, trace1, FencepostPosition(('at', 0)))
    aut5_node = container[aut5]
    assert(isinstance(aut5_node, AutAcc))
    assert result5[0] == frozenset([frozenset([aut5_node.child])])
    assert result5[1] == True

    result6 = evaluate_finite_automaton_primitive(aut6, container, trace1, FencepostPosition(('at', 0)))
    aut6_node = container[aut6]
    assert(isinstance(aut6_node, AutRead))
    aut6_true_child = container[aut6_node.child2]
    assert(isinstance(aut6_true_child, AutAcc))
    assert result6[0] == frozenset([frozenset([aut6_true_child.child])])
    assert result6[1] == True

    result7 = evaluate_finite_automaton_primitive(aut7, container, trace1, FencepostPosition(('at', 0)))
    assert result7[1] == False

    assert evaluate_finite_automaton(aut1, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]
    assert evaluate_finite_automaton(aut1, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut2, container, trace1, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(aut2, container, trace1_top, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut3, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]
    assert evaluate_finite_automaton(aut3, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut4, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut5, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]


    assert evaluate_finite_automaton(aut6, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]

    assert evaluate_finite_automaton(aut7, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut8, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]
    assert evaluate_finite_automaton(aut8, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut9, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut10, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut10, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(aut11, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 3))]

    assert evaluate_finite_automaton(aut12, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(aut12, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]


def test_automaton_simplify_conf():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare-rec
            (declare n1 (aut-consume a n3 n7))
            (declare n2 (aut-or n1 n3))
            (declare n3 (aut-consume b n4 n5))
            (declare n4 (aut-acc n6))
            (declare n5 (aut-false))
            (declare n6 (aut-false))
            (declare n7 (aut-false))
            (declare n8 (aut-true))
        )

    )"""

    container: IrContainer = IrContainer()
    container.bypass_placeholders()
    parse_document(parse_raw_sexpr(doc_str), container)

    n1: NodeId = container.get_node_id_by_name('n1')
    n2: NodeId = container.get_node_id_by_name('n2')
    n3: NodeId = container.get_node_id_by_name('n3')
    n4: NodeId = container.get_node_id_by_name('n4')
    n5: NodeId = container.get_node_id_by_name('n5') # false
    n6: NodeId = container.get_node_id_by_name('n6') # false
    n8: NodeId = container.get_node_id_by_name('n8') # true

    conf1: Configuration = frozenset([
        frozenset([n1])
    ])

    conf2: Configuration = frozenset([
        frozenset([n1, n2, n3])
    ])

    conf3: Configuration = frozenset([
        frozenset([n1, n2, n3, n8])
    ])

    conf4: Configuration = frozenset([
        frozenset([n1, n2, n3, n5])
    ])

    conf5: Configuration = frozenset([
        frozenset()
    ])

    conf6: Configuration = frozenset([
        frozenset([n1, n3]),
        frozenset([n2]),
    ])

    conf7: Configuration = frozenset([
        frozenset([n1, n3]),
        frozenset([n4, n8]),
        frozenset([n6])
    ])

    empty_conf: Configuration = frozenset()

    assert conf1 == simplify_conf(conf1, container)
    assert conf2 == simplify_conf(conf2, container)
    assert empty_conf == simplify_conf(conf5, container)
    assert conf6 == simplify_conf(conf6, container)

    assert conf1 == conf_or({conf1}, container)
    assert conf2 == conf_or({conf2}, container)
    assert conf1 == conf_and({conf1}, container)
    assert conf2 == conf_and({conf2}, container)

    assert conf2 == simplify_conf(conf3, container)
    assert simplify_conf(conf4, container) == frozenset()

    assert conf_or({conf6, conf1}, container) == frozenset([frozenset([n1]), frozenset([n2])])
    assert conf_and({conf6, conf1}, container) == frozenset([frozenset([n1, n3]), frozenset([n2, n1])])
    assert conf_and({conf7, conf1}, container) == frozenset([frozenset([n1, n3]), frozenset([n4, n1])])





def test_automaton_aut_or():
    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare aut6 (aut-read a (aut-acc (aut-false)) (aut-false) ))
        (declare aut7 (aut-read b (aut-acc (aut-false)) (aut-false) ))

        (declare aut8 (aut-consume a (aut-consume b (aut-true) (aut-false)) (aut-false)))

        (declare aut_or_1 (aut-or aut6 aut7))
        (declare aut_or_2 (aut-or aut6 aut8))
        (declare aut_or_3 (aut-or aut7 aut8))

        (declare-rec (declare aut_or_4
            (aut-consume a
                (aut-or aut_or_4 (aut-consume b (aut-acc (aut-false)) (aut-false)))
                (aut-false)
            )
        ))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)
    container.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'aut_or.png')

    aut_or_1: NodeId = container.get_node_id_by_name('aut_or_1')
    aut_or_2: NodeId = container.get_node_id_by_name('aut_or_2')
    aut_or_3: NodeId = container.get_node_id_by_name('aut_or_3')
    aut_or_4: NodeId = container.get_node_id_by_name('aut_or_4')

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    trace1_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='top_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a', 'b'}),
        frozenset({'a', 'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    assert evaluate_finite_automaton(aut_or_1, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_or_1, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]

    assert evaluate_finite_automaton(aut_or_2, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]
    assert evaluate_finite_automaton(aut_or_2, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_or_3, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]
    assert evaluate_finite_automaton(aut_or_3, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_or_4, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_or_4, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]


def test_automaton_aut_and():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare aut3 (aut-consume a (aut-true) (aut-false)))

        (declare aut6 (aut-read a (aut-acc (aut-false)) (aut-false) ))
        (declare aut7 (aut-read b (aut-acc (aut-false)) (aut-false) ))

        (declare aut8 (aut-consume a (aut-consume b (aut-true) (aut-false)) (aut-false)))

        (declare aut10 (aut-consume a (aut-consume b (aut-acc (aut-false)) (aut-false)) (aut-false)))

        (declare aut_and_1 (aut-and aut6 aut7))
        (declare aut_and_2 (aut-and aut3 aut8))
        (declare aut_and_3 (aut-and aut3 aut10))

        (declare-rec (declare aut_or_4
            (aut-consume a
                (aut-or aut_or_4 (aut-consume b (aut-acc (aut-false)) (aut-false)))
                (aut-false)
            )
        ))

        (declare aut_and_4
            (aut-and
                aut10
                (aut-consume a
                    (aut-or aut_or_4 (aut-consume b (aut-acc (aut-false)) (aut-false)))
                    (aut-false)
                )
            )
        )

        (declare aut_and_5
            (aut-or
                aut_and_4
                aut_and_3
            )
        )

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)
    container.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'aut_or.png')

    aut_and_1: NodeId = container.get_node_id_by_name('aut_and_1')
    aut_and_2: NodeId = container.get_node_id_by_name('aut_and_2')
    aut_and_3: NodeId = container.get_node_id_by_name('aut_and_3')
    aut_and_4: NodeId = container.get_node_id_by_name('aut_and_4')
    aut_and_5: NodeId = container.get_node_id_by_name('aut_and_5')

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    trace1_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='top_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a', 'b'}),
        frozenset({'a', 'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    assert evaluate_finite_automaton(aut_and_1, container, trace1, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(aut_and_1, container, trace1_top, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_and_2, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]
    assert evaluate_finite_automaton(aut_and_2, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_and_3, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(aut_and_4, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(aut_and_5, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2))]



def test_automaton_aut_subcall():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare subcall_aut1 (aut-consume a (aut-true) (aut-false)))
        (declare subcall_aut2 (aut-consume a
            (aut-consume b (aut-acc (aut-false)) (aut-false))
            (aut-false))
        )
        (declare subcall_aut3 (aut-read a (aut-true) (aut-false)))

        (declare succ_aut1 (aut-acc (aut-false)) )
        (declare succ_aut2 (aut-consume b (aut-acc (aut-false)) (aut-false)))
        (declare succ_aut3 (aut-read a (aut-acc (aut-false)) (aut-false)))
        (declare succ_aut4 (aut-read b (aut-acc (aut-false)) (aut-false)))

        (declare aut_first1 (aut-call-first subcall_aut1 succ_aut1))
        (declare aut_first2 (aut-call-first subcall_aut1 succ_aut2))
        (declare aut_first3 (aut-call-first subcall_aut2 succ_aut1))
        (declare aut_first4 (aut-call-first subcall_aut3 succ_aut1))
        (declare aut_first5 (aut-call-first subcall_aut3 succ_aut3))
        (declare aut_first6 (aut-call-first subcall_aut3 succ_aut4))

        (declare aut_ex1 (aut-call-ex subcall_aut1 succ_aut1))
        (declare aut_ex2 (aut-call-ex subcall_aut1 succ_aut2))
        (declare aut_ex3 (aut-call-ex subcall_aut2 succ_aut1))
        (declare aut_ex4 (aut-call-ex subcall_aut3 succ_aut1))
        (declare aut_ex5 (aut-call-ex subcall_aut3 succ_aut3))
        (declare aut_ex6 (aut-call-ex subcall_aut3 succ_aut4))
        (declare aut_ex7 (aut-call-ex succ_aut3 succ_aut4))
        (declare aut_ex8 (aut-call-ex succ_aut4 succ_aut1))

        (declare nested_call1 (aut-call-ex aut_ex1 succ_aut4))
        (declare nested_call2 (aut-call-ex aut_ex1 succ_aut2))

        (declare-rec (declare other_aut
            (aut-consume c (aut-acc other_aut) other_aut)
        ))

        (declare call_in_or (aut-or
            aut_ex2
            other_aut
        ))

        (declare call_in_and (aut-and
            aut_ex2
            other_aut
        ))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)
    container.bypass_placeholders()

    visualize: bool = False
    if visualize:
        output_directory: Path = Path('./output')
        container.show_graph(output_directory / 'aut_or.png')

    aut_first1: NodeId = container.get_node_id_by_name('aut_first1')
    aut_first2: NodeId = container.get_node_id_by_name('aut_first2')
    aut_first3: NodeId = container.get_node_id_by_name('aut_first3')
    subcall_aut2: NodeId = container.get_node_id_by_name('subcall_aut2')
    aut_first4: NodeId = container.get_node_id_by_name('aut_first4')
    aut_first5: NodeId = container.get_node_id_by_name('aut_first5')
    aut_first6: NodeId = container.get_node_id_by_name('aut_first6')

    aut_ex1: NodeId = container.get_node_id_by_name('aut_ex1')
    aut_ex2: NodeId = container.get_node_id_by_name('aut_ex2')
    aut_ex3: NodeId = container.get_node_id_by_name('aut_ex3')
    aut_ex4: NodeId = container.get_node_id_by_name('aut_ex4')
    aut_ex5: NodeId = container.get_node_id_by_name('aut_ex5')
    aut_ex6: NodeId = container.get_node_id_by_name('aut_ex6')
    aut_ex7: NodeId = container.get_node_id_by_name('aut_ex7')
    aut_ex8: NodeId = container.get_node_id_by_name('aut_ex8')

    nested_call1: NodeId = container.get_node_id_by_name('nested_call1')
    nested_call2: NodeId = container.get_node_id_by_name('nested_call2')

    call_in_or: NodeId = container.get_node_id_by_name('call_in_or')
    call_in_and: NodeId = container.get_node_id_by_name('call_in_and')
    other_aut: NodeId = container.get_node_id_by_name('other_aut')

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'c'}),
    ), suffix='end')

    trace1_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'c'}),
    ), suffix='top_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'c'}),
        frozenset({}),
    ), suffix='end')

    trace2_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'c'}),
        frozenset({}),
    ), suffix='top_omega')

    trace3 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'b', 'c'}),
        frozenset({}),
        frozenset({'c'}),
        frozenset({}),
    ), suffix='end')

    trace3_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({}),
        frozenset({'b', 'c'}),
        frozenset({}),
        frozenset({'c'}),
        frozenset({}),
    ), suffix='top_omega')

    assert evaluate_finite_automaton(aut_first1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(aut_first2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(subcall_aut2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_first3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_first4, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_first5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_first6, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_ex1, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]
    assert evaluate_finite_automaton(aut_ex1, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('unknown')]

    assert evaluate_finite_automaton(aut_ex2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_ex2, container, trace1_top, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_ex3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_ex3, container, trace1_top, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(aut_ex4, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]
    assert evaluate_finite_automaton(aut_ex4, container, trace1_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4)), FencepostPosition('unknown')]

    assert evaluate_finite_automaton(aut_ex5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_ex5, container, trace1_top, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0)), FencepostPosition(('at', 4)), FencepostPosition('unknown')]

    assert evaluate_finite_automaton(aut_ex6, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(aut_ex6, container, trace1_top, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1)), FencepostPosition(('at', 4)), FencepostPosition('unknown')]

    assert evaluate_finite_automaton(aut_ex7, container, trace1, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(aut_ex7, container, trace1_top, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_ex8, container, trace1, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(aut_ex8, container, trace1_top, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(nested_call1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(nested_call2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(call_in_or, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 3)), FencepostPosition(('at', 5)), FencepostPosition(('at', 7))]
    assert evaluate_finite_automaton(call_in_or, container, trace2_top, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 3)), FencepostPosition(('at', 5)), FencepostPosition(('at', 7)), FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_ex2, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 3)), FencepostPosition(('at', 5))]
    assert evaluate_finite_automaton(aut_ex2, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 3)), FencepostPosition(('at', 5))]
    assert evaluate_finite_automaton(other_aut, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 7))]
    assert evaluate_finite_automaton(other_aut, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 5)), FencepostPosition(('at', 7))]

    assert evaluate_finite_automaton(call_in_and, container, trace2, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(call_in_and, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 5))]

    assert evaluate_finite_automaton(call_in_and, container, trace2_top, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(call_in_and, container, trace3_top, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 5)), FencepostPosition('within_infinite_suffix')]


def test_automaton_aut_suffix():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)

        (declare aut1 (aut-consume a (aut-true) (aut-false)))
        (declare aut2 (aut-consume a
            (aut-consume b (aut-acc (aut-false)) (aut-false))
            (aut-false))
        )
        (declare aut3 (aut-consume a
            (aut-consume b
                (aut-consume b (aut-acc (aut-false)) (aut-false))
                (aut-false))
            (aut-false))
        )

        (declare-rec (declare aut4
            (aut-consume c (aut-acc aut4) aut4)
        ))

        (declare aut_and_1 (aut-and aut1 aut2))
        (declare aut_and_2 (aut-and aut2 aut3))

        (declare aut_sub_1 (aut-call-ex
            aut1
            (aut-acc (aut-false))
        ))
        (declare aut_sub_2 (aut-call-ex
            aut2
            (aut-acc (aut-false))
        ))
        (declare aut_sub_3 (aut-call-ex
            aut3
            (aut-acc (aut-false))
        ))

        (declare aut_and_3 (aut-and aut_sub_1 aut_sub_2))
        (declare aut_and_4 (aut-and aut_sub_2 aut_sub_3))
        (declare aut_and_5 (aut-and aut1 aut_sub_3))
        (declare aut_and_6 (aut-and aut_sub_2 aut3))
        (declare aut_and_7 (aut-and aut_sub_2 aut4))
        (declare aut_and_8 (aut-and aut_sub_1 aut4))

        (declare aut_or_1 (aut-or aut1 aut2))
        (declare aut_or_2 (aut-or aut2 aut3))

        (declare aut_or_3 (aut-or aut_sub_1 aut_sub_2))
        (declare aut_or_4 (aut-or aut_sub_2 aut_sub_3))
        (declare aut_or_5 (aut-or aut1 aut_sub_3))
        (declare aut_or_6 (aut-or aut_sub_2 aut3))
        (declare aut_or_7 (aut-or aut_sub_2 aut4))
        (declare aut_or_8 (aut-or aut_sub_1 aut4))

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)
    container.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'aut_or.png')

    aut_and_1: NodeId = container.get_node_id_by_name('aut_and_1')
    aut_and_2: NodeId = container.get_node_id_by_name('aut_and_2')
    aut_and_3: NodeId = container.get_node_id_by_name('aut_and_3')
    aut_and_4: NodeId = container.get_node_id_by_name('aut_and_4')
    aut_and_5: NodeId = container.get_node_id_by_name('aut_and_5')
    aut_and_6: NodeId = container.get_node_id_by_name('aut_and_6')
    aut_and_7: NodeId = container.get_node_id_by_name('aut_and_7')
    aut_and_8: NodeId = container.get_node_id_by_name('aut_and_8')

    aut_or_1: NodeId = container.get_node_id_by_name('aut_or_1')
    aut_or_2: NodeId = container.get_node_id_by_name('aut_or_2')
    aut_or_3: NodeId = container.get_node_id_by_name('aut_or_3')
    aut_or_4: NodeId = container.get_node_id_by_name('aut_or_4')
    aut_or_5: NodeId = container.get_node_id_by_name('aut_or_5')
    aut_or_6: NodeId = container.get_node_id_by_name('aut_or_6')
    aut_or_7: NodeId = container.get_node_id_by_name('aut_or_7')
    aut_or_8: NodeId = container.get_node_id_by_name('aut_or_8')

    trace1 = Trace(finite_part=(
    ), suffix='top_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='top_omega')

    assert evaluate_finite_automaton(aut_and_1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_and_2, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_and_3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_4, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_6, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_7, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_8, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_and_8, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]

    assert evaluate_finite_automaton(aut_or_1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_or_2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]

    assert evaluate_finite_automaton(aut_or_3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_or_4, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('unknown')]
    assert evaluate_finite_automaton(aut_or_5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_or_6, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_or_7, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_or_8, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition('within_infinite_suffix')]
    assert evaluate_finite_automaton(aut_or_8, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1)), FencepostPosition('within_infinite_suffix')]



def test_automaton_omega_finite_part_linear():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare omega1 (omega-true))
        (declare omega2 (omega-false))
        (declare omega3 (omega-weak-consume a (omega-true) (omega-false)))
        (declare omega4 (omega-weak-consume b (omega-true) (omega-false)))
        (declare omega5 (omega-strong-consume a (omega-true) (omega-false)))
        (declare omega6 (omega-strong-consume b (omega-true) (omega-false)))

        (declare omega7 (omega-weak-consume a (omega-weak-consume b (omega-true) (omega-false)) (omega-false)))
        (declare omega8 (omega-weak-consume a (omega-weak-consume b (omega-false) (omega-false)) (omega-false)))

        (declare omega9 (omega-weak-consume a (omega-strong-consume b (omega-true) (omega-false)) (omega-false)))
        (declare omega10 (omega-strong-consume a (omega-weak-consume b (omega-true) (omega-false)) (omega-false)))

        (declare omega11 (omega-weak-consume a
            (omega-weak-consume b
                (omega-weak-consume b
                    (omega-true)
                    (omega-false))
                (omega-false))
            (omega-false))
        )

    )"""

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    omega1: NodeId = container.get_node_id_by_name('omega1')
    omega2: NodeId = container.get_node_id_by_name('omega2')
    omega3: NodeId = container.get_node_id_by_name('omega3')
    omega4: NodeId = container.get_node_id_by_name('omega4')
    omega5: NodeId = container.get_node_id_by_name('omega5')
    omega6: NodeId = container.get_node_id_by_name('omega6')
    omega7: NodeId = container.get_node_id_by_name('omega7')
    omega8: NodeId = container.get_node_id_by_name('omega8')
    omega9: NodeId = container.get_node_id_by_name('omega9')
    omega10: NodeId = container.get_node_id_by_name('omega10')
    omega11: NodeId = container.get_node_id_by_name('omega11')


    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')
    trace1_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='top_omega')
    trace1_bot = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='bot_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='end')
    trace2_top = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='top_omega')
    trace2_bot = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='bot_omega')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    #container.bypass_placeholders()
    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'aut_or.png')

    assert evaluate_omega_automaton(omega1, container, trace1) == True
    assert evaluate_omega_automaton(omega2, container, trace1) == False

    assert evaluate_omega_automaton(omega3, container, trace1) == True
    assert evaluate_omega_automaton(omega3, container, trace1_top) == True
    assert evaluate_omega_automaton(omega3, container, trace1_bot) == True

    assert evaluate_omega_automaton(omega4, container, trace1) == False
    assert evaluate_omega_automaton(omega5, container, trace1) == True
    assert evaluate_omega_automaton(omega6, container, trace1) == False
    assert evaluate_omega_automaton(omega7, container, trace1) == True

    assert evaluate_omega_automaton(omega8, container, trace1) == False
    assert evaluate_omega_automaton(omega8, container, trace1_top) == False
    assert evaluate_omega_automaton(omega8, container, trace1_bot) == False

    assert evaluate_omega_automaton(omega9, container, trace2) == False
    assert evaluate_omega_automaton(omega9, container, trace2_top) == True
    assert evaluate_omega_automaton(omega9, container, trace2_bot) == False

    assert evaluate_omega_automaton(omega10, container, trace2) == True
    assert evaluate_omega_automaton(omega10, container, trace2_top) == True
    assert evaluate_omega_automaton(omega10, container, trace2_bot) == False

    assert evaluate_omega_automaton(omega11, container, trace2) == True
    assert evaluate_omega_automaton(omega11, container, trace2_top) == True
    assert evaluate_omega_automaton(omega11, container, trace2_bot) == False


def test_automaton_omega_finite_part_alternation():

    doc_str: str = """(document
        (declare-input a)
        (declare-input b)

        (declare omega1 (omega-true))
        (declare omega2 (omega-false))
        (declare omega3 (omega-weak-consume a (omega-true) (omega-false)))
        (declare omega6 (omega-strong-consume b (omega-true) (omega-false)))
        (declare omega7 (omega-weak-consume a (omega-weak-consume b (omega-true) (omega-false)) (omega-false)))

        (declare or1 (omega-or omega1 omega2))
        (declare or2 (omega-or omega6 omega7))

        (declare and1 (omega-and omega1 omega2))
        (declare and2 (omega-and omega6 omega7))

        (declare both1 (omega-or
            (omega-and omega1 omega3)
            and2
        ))

        (declare both2 (omega-or and1 and2))
        (declare both3 (omega-and or1 or2))

        (declare both4 (omega-and
            (omega-or omega2 omega6)
            or2
        ))

    )"""

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    or1: NodeId = container.get_node_id_by_name('or1')
    or2: NodeId = container.get_node_id_by_name('or2')

    and1: NodeId = container.get_node_id_by_name('and1')
    and2: NodeId = container.get_node_id_by_name('and2')

    both1: NodeId = container.get_node_id_by_name('both1')
    both2: NodeId = container.get_node_id_by_name('both2')
    both3: NodeId = container.get_node_id_by_name('both3')
    both4: NodeId = container.get_node_id_by_name('both4')

    assert evaluate_omega_automaton(or1, container, trace1) == True
    assert evaluate_omega_automaton(or2, container, trace1) == True

    assert evaluate_omega_automaton(and1, container, trace1) == False
    assert evaluate_omega_automaton(and2, container, trace1) == False

    assert evaluate_omega_automaton(both1, container, trace1) == True
    assert evaluate_omega_automaton(both2, container, trace1) == False
    assert evaluate_omega_automaton(both3, container, trace1) == True
    assert evaluate_omega_automaton(both4, container, trace1) == False


def test_automaton_omega_infinite_suffix_cycle():

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

    )"""

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='end')

    trace2_bot = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='bot_omega')

    trace2_top = Trace(finite_part=(
        frozenset({'a'}),
    ), suffix='top_omega')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    omega1: NodeId = container.get_node_id_by_name('omega1')
    omega2: NodeId = container.get_node_id_by_name('omega2')
    or1: NodeId = container.get_node_id_by_name('or1')
    and1: NodeId = container.get_node_id_by_name('and1')

    assert evaluate_omega_automaton(omega1, container, trace1) == False
    assert evaluate_omega_automaton(omega1, container, trace2) == True
    assert evaluate_omega_automaton(omega1, container, trace2_bot) == False

    assert evaluate_omega_automaton(omega2, container, trace1) == False
    assert evaluate_omega_automaton(omega2, container, trace2) == False
    assert evaluate_omega_automaton(omega2, container, trace2_bot) == False
    assert evaluate_omega_automaton(omega2, container, trace2_top) == False

    assert evaluate_omega_automaton(or1, container, trace1) == False
    assert evaluate_omega_automaton(or1, container, trace2) == True
    assert evaluate_omega_automaton(and1, container, trace2) == False


def test_automaton_omega_cycle_and_or():

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

    )"""

    trace1 = Trace(finite_part=(
        frozenset({'a', 'c'}),
        frozenset({'b', 'c'}),
        frozenset({'b'}),
    ), suffix='end')

    trace1_bot = Trace(finite_part=(
        frozenset({'a', 'c'}),
        frozenset({'b', 'c'}),
        frozenset({'b'}),
    ), suffix='bot_omega')

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset(),
        frozenset({'b'}),
    ), suffix='end')

    trace2_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset(),
        frozenset({'b'}),
    ), suffix='top_omega')

    trace3 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='end')

    trace3_top = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='top_omega')

    trace3_bot = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a'}),
    ), suffix='bot_omega')

    trace4 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a'}),
        frozenset({'a', 'b'}),
    ), suffix='end')

    trace5 = Trace(finite_part=(
        frozenset({'b'}),
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    a_until_b: NodeId = container.get_node_id_by_name('a_until_b')
    a_strong_until_with_b: NodeId = container.get_node_id_by_name('a_strong_until_with_b')
    a_until_b_read: NodeId = container.get_node_id_by_name('a_until_b_read')
    a_until_b_read_2: NodeId = container.get_node_id_by_name('a_until_b_read_2')
    b_until_always_a: NodeId = container.get_node_id_by_name('b_until_always_a')

    assert evaluate_omega_automaton(a_until_b, container, trace1) == True
    assert evaluate_omega_automaton(a_until_b, container, trace1_bot) == True
    assert evaluate_omega_automaton(a_until_b, container, trace2) == False
    assert evaluate_omega_automaton(a_until_b, container, trace2_top) == False
    assert evaluate_omega_automaton(a_until_b, container, trace3) == True
    assert evaluate_omega_automaton(a_until_b, container, trace3_bot) == False

    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace1) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace1_bot) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace2) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace2_top) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace3) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace3_top) == True
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace3_bot) == False
    assert evaluate_omega_automaton(a_strong_until_with_b, container, trace4) == True

    assert evaluate_omega_automaton(a_until_b_read, container, trace1) == True
    assert evaluate_omega_automaton(a_until_b_read, container, trace1_bot) == True
    assert evaluate_omega_automaton(a_until_b_read, container, trace3) == False

    assert evaluate_omega_automaton(a_until_b_read_2, container, trace1) == True
    assert evaluate_omega_automaton(a_until_b_read_2, container, trace1_bot) == True
    assert evaluate_omega_automaton(a_until_b_read_2, container, trace3) == False

    assert evaluate_omega_automaton(b_until_always_a, container, trace1) == False
    assert evaluate_omega_automaton(b_until_always_a, container, trace3) == True
    assert evaluate_omega_automaton(b_until_always_a, container, trace3_top) == True
    assert evaluate_omega_automaton(b_until_always_a, container, trace3_bot) == False
    assert evaluate_omega_automaton(b_until_always_a, container, trace5) == False




def test_automaton_omega_conflicting_obligations():

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
            (declare start2 (omega-or and1 and2))
            (and1 (omega-and path1 path2))
            (and2 (omega-and path3 path4))
            (path1 (omega-weak-consume-acc a branch1 (omega-false)))
            (path2 (omega-weak-consume-acc b branch2 (omega-false)))
            (path3 (omega-weak-consume-acc c branch1 (omega-false)))
            (path4 (omega-weak-consume-acc d branch2 (omega-false)))
            (branch1 (omega-weak-consume a start2 (omega-false)))
            (branch2 (omega-weak-consume b start2 (omega-false)))
        )

        (declare-rec
            (declare start3 (omega-and path1 path2))
            (path1 (omega-weak-consume a start3 (omega-false)))
            (path2 (omega-weak-consume b start3 (omega-false)))
        )

        (declare-rec
            (declare start4 (omega-weak-consume a start4 (omega-false)))
        )

        (declare-rec
            (declare start5 (omega-and path1 path2))
            (path1 (omega-weak-consume a start5 (omega-false)))
            (path2 (omega-weak-consume b start5 (omega-false)))
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

        (declare-rec
            (declare start7 (omega-or and1 and2))
            (and1 (omega-and path1 path2))
            (and2 (omega-and path3 path4))
            (path1 (omega-weak-consume-acc a start7 (omega-false)))
            (path2 (omega-weak-consume-acc b start7 (omega-false)))
            (path3 (omega-weak-consume-acc c start7 (omega-false)))
            (path4 (omega-weak-consume d start7 (omega-false)))
        )

    )"""

    trace1 = Trace(finite_part=(
    ), suffix='top_omega')

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc_str), container)

    start1: NodeId = container.get_node_id_by_name('start1')
    start2: NodeId = container.get_node_id_by_name('start2')
    start3: NodeId = container.get_node_id_by_name('start3')
    start4: NodeId = container.get_node_id_by_name('start4')
    start5: NodeId = container.get_node_id_by_name('start5')
    start6: NodeId = container.get_node_id_by_name('start6')
    start7: NodeId = container.get_node_id_by_name('start7')

    container.bypass_placeholders()

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'omega_conflicting.png')

    assert evaluate_omega_automaton(start1, container, trace1) == False
    assert evaluate_omega_automaton(start2, container, trace1) == True
    assert evaluate_omega_automaton(start3, container, trace1) == False
    assert evaluate_omega_automaton(start4, container, trace1) == False
    assert evaluate_omega_automaton(start5, container, trace1) == False
    assert evaluate_omega_automaton(start6, container, trace1) == True
    assert evaluate_omega_automaton(start7, container, trace1) == True



@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_with_trace(
    final_node_type=FiniteAutomaton,
    primitive_filter=lambda node_type:
        issubclass(node_type, (FiniteAutomaton, Bool)) and
        not issubclass(node_type, (AutRepeat, AutRepeatUpTo, AutRefuted))))
def test_automaton_aut_random_no_error(doc_and_trace):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), container)

    root_node_id: NodeId = container.get_sink_nodes()[0]

    result: list[FencepostPosition] = evaluate_finite_automaton(root_node_id,
        container, trace, FencepostPosition(('at', 0)))

    logger.debug('doc: %s', doc)
    logger.debug('trace: %s', trace)
    logger.debug('result: %s', result)


@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_with_trace(
    final_node_type=OmegaAutomaton,
    primitive_filter=lambda node_type:
        issubclass(node_type, (OmegaAutomaton, FiniteAutomaton, Bool)) and
        not issubclass(node_type, (OmegaAcceptOn, OmegaRejectOn, OmegaCallAll, OmegaCallExStrong, OmegaCallExWeak))))
def test_automaton_omega_random_no_error(doc_and_trace):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), container)

    root_node_id: NodeId = container.get_sink_nodes()[0]

    result: MaybeBool = evaluate_omega_automaton(root_node_id, container, trace)

    logger.debug('doc: %s', doc)
    logger.debug('trace: %s', trace)
    logger.debug('result: %s', result)
