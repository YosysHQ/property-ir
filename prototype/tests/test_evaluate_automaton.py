from ir.base import IrContainer, NodeId
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.automata_primitives import AutAcc, AutConsume, AutRead

from tests.evaluate import FencepostPosition, Trace
from tests.evaluate_automaton import evaluate_finite_automaton_primitive


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
        (declare aut11 (aut-consume a (aut-consume b (aut-acc (aut-false)) (aut-false)) (aut-false)))


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

    #aut8: NodeId = container.get_node_id_by_name('aut8')
    #aut9: NodeId = container.get_node_id_by_name('aut9')
    #aut10: NodeId = container.get_node_id_by_name('aut10')
    #aut11: NodeId = container.get_node_id_by_name('aut11')

    trace1 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')


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


def test_automaton_aut_or():
    pass


def test_automaton_aut_and():
    pass
