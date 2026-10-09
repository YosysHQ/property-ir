from ir.base import IrContainer, NodeId
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.automata_primitives import AutAcc, AutConsume, AutRead

from tests.evaluate import FencepostPosition, Trace
from tests.evaluate_automaton import (
    Configuration,
    conf_and,
    conf_or,
    evaluate_finite_automaton,
    evaluate_finite_automaton_primitive,
    simplify_conf,
)


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

    assert evaluate_finite_automaton(aut2, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut3, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]

    assert evaluate_finite_automaton(aut4, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut5, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]


    assert evaluate_finite_automaton(aut6, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]

    assert evaluate_finite_automaton(aut7, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut8, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]

    assert evaluate_finite_automaton(aut9, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut10, container, trace1, FencepostPosition(('at', 0))) == [
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

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a', 'b'}),
        frozenset({'a', 'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    assert evaluate_finite_automaton(aut_or_1, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0))]

    assert evaluate_finite_automaton(aut_or_2, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]

    assert evaluate_finite_automaton(aut_or_3, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3))]

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

    trace2 = Trace(finite_part=(
        frozenset({'a'}),
        frozenset({'a', 'b'}),
        frozenset({'a', 'b'}),
        frozenset({'b'}),
        frozenset({'b'}),
    ), suffix='end')

    assert evaluate_finite_automaton(aut_and_1, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_and_2, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]

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

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'aut_or.png')

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

    assert evaluate_finite_automaton(aut_first1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(aut_first2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(subcall_aut2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_first3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_first4, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_first5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_first6, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(aut_ex1, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]
    assert evaluate_finite_automaton(aut_ex2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_ex3, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]
    assert evaluate_finite_automaton(aut_ex4, container, trace1, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 0)), FencepostPosition(('at', 1)), FencepostPosition(('at', 2)), FencepostPosition(('at', 3)), FencepostPosition(('at', 4))]
    assert evaluate_finite_automaton(aut_ex5, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 0))]
    assert evaluate_finite_automaton(aut_ex6, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(aut_ex7, container, trace1, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(aut_ex8, container, trace1, FencepostPosition(('at', 0))) == []

    assert evaluate_finite_automaton(nested_call1, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 1))]
    assert evaluate_finite_automaton(nested_call2, container, trace1, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 2))]

    assert evaluate_finite_automaton(call_in_or, container, trace2, FencepostPosition(('at', 0))) == [
        FencepostPosition(('at', 3)), FencepostPosition(('at', 5)), FencepostPosition(('at', 7))]

    assert evaluate_finite_automaton(aut_ex2, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 3)), FencepostPosition(('at', 5))]
    assert evaluate_finite_automaton(aut_ex2, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 3)), FencepostPosition(('at', 5))]
    assert evaluate_finite_automaton(other_aut, container, trace2, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 7))]
    assert evaluate_finite_automaton(other_aut, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 5)), FencepostPosition(('at', 7))]

    assert evaluate_finite_automaton(call_in_and, container, trace2, FencepostPosition(('at', 0))) == []
    assert evaluate_finite_automaton(call_in_and, container, trace3, FencepostPosition(('at', 0))) == [FencepostPosition(('at', 5))]
