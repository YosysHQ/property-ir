import pytest
from pathlib import Path
from hypothesis import given, settings, Verbosity, example

from sexpr.base import RawSExprList, IrContainer, ClockedProperty, ClockedSequence
from sexpr.parsing import parse_raw_sexpr, parse_document
from sexpr.primitives import ClkPropSeq, ClkSeqClocked, ClkPropClocked
from sexpr.rewriting import rewrite_clocks, rewrite_nexttime_primitives
from tests.strategies import random_ir_clocked


def check_clock_rewriting(input_document_str: str, expected_output_document_str: str, visualize: bool = False):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_clock_rewriting_input.png')

    rewrite_nexttime_primitives(container1)
    container3: IrContainer = rewrite_clocks(container1) # for output

    parse_document(expected_output_document, container2)

    if visualize:
        container3.show_graph(output_directory / 'check_clock_rewriting_output_before_renaming.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_clock_rewriting_expected_output.png')

    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container3.show_graph(output_directory / 'check_clock_rewriting_output_after_renaming.png')

    assert container3.weakly_equivalent(container2)



def test_clock_rewriting_base_case():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked c (clk-prop-bool a))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c))) (clk-seq-bool (and c a))) ))))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_no_change_bool():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-weak-bool (and a (not b) (or b c))))))"""
    output_document: str = input_document
    check_clock_rewriting(input_document, output_document)

def test_clock_rewriting_no_change_seq():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (parse-sexpr (clk-seq-clocked (true) (clk-seq-concat (clk-seq-repeat (range 4 8) (clk-seq-bool b)) (clk-seq-bool a)))))"""
    output_document: str = input_document
    check_clock_rewriting(input_document, output_document)

def test_clock_rewriting_no_change_prop():
    input_document: str = """(document
        (declare-input a)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-bool a))))"""
    output_document: str = input_document
    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_clock_change():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        (parse-sexpr (clk-prop-clocked c1 (clk-prop-seq (clk-seq-concat (clk-seq-bool a) (clk-seq-clocked c2 (clk-seq-bool b)) )))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        (declare gclk (true))
        (declare p1 (clk-seq-clocked gclk (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c2)) ) (clk-seq-bool (and c2 b) ) )))
        (declare p2 (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c1)) ) (clk-seq-bool (and c1 a) ) ))
        (declare p3 (clk-prop-clocked gclk (clk-prop-seq (clk-seq-concat p2 p1) ) ))
        (parse-sexpr p3))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_copy_subgraph():
    input_document: str = """(document
        (declare-input a)
        (declare-input c1)
        (declare-input c2)
        (declare p  (clk-prop-bool a))
        (parse-sexpr (clk-prop-clocked c1 p))
        (parse-sexpr (clk-prop-clocked c2 p))
        )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input c1)
        (declare-input c2)
        (declare gclk (true))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c1))) (clk-seq-bool (and c1 a)) ) )))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c2))) (clk-seq-bool (and c2 a)) ) )))
        )"""

    check_clock_rewriting(input_document, output_document)

def test_clock_rewriting_with_cycle():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare-rec (declare p (clk-prop-clocked c (clk-prop-non-overlapped-implication (clk-seq-bool a) (clk-prop-and (clk-prop-bool b) p) ))))
        (parse-sexpr p))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare gclk (true))
        (declare seq_a (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c)) ) (clk-seq-bool (and c a) ) ))
        (declare seq_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c)) ) (clk-seq-bool (and c b) ) ))
        (declare-rec (declare p (clk-prop-clocked gclk (clk-prop-non-overlapped-implication seq_a (clk-prop-and (clk-prop-seq seq_b) p)))))
        (parse-sexpr p))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_with_cycle_and_clock_change():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        (declare-rec (declare p (clk-prop-clocked c1 (clk-prop-non-overlapped-implication (clk-seq-bool a) (clk-prop-clocked c2 (clk-prop-and (clk-prop-bool b) p)) ))))
        (parse-sexpr p))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        (declare gclk (true))
        (declare seq_a (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c1)) ) (clk-seq-bool (and c1 a) ) ))
        (declare seq_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c2)) ) (clk-seq-bool (and c2 b) ) ))
        (declare-rec (declare p (clk-prop-clocked gclk (clk-prop-non-overlapped-implication seq_a (clk-prop-clocked gclk (clk-prop-and (clk-prop-seq seq_b) p))))))
        (parse-sexpr p))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_unspecified_clock_error():
    with pytest.raises(ValueError, match='unspecified clock'):
        input_document: str = """(document
            (declare-input a)
            (declare-input c)
            (parse-sexpr (clk-prop-bool a)))"""
        output_document: str = """(document (declare-input a) (declare-input c))"""
        check_clock_rewriting(input_document, output_document)



def test_clock_rewriting_accept_on():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-sync-accept-on a (clk-prop-bool b)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk b) ) ))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-accept-on (and a clk) (clk-prop-seq seq_b)))))"""

    check_clock_rewriting(input_document, output_document)

def test_clock_rewriting_reject_on():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-sync-reject-on a (clk-prop-bool b)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk b) ) ))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-reject-on (and a clk) (clk-prop-seq seq_b)))))"""

    check_clock_rewriting(input_document, output_document)



def test_clock_rewriting_until():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-until (clk-prop-bool a) (clk-prop-bool b)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_a (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) ))
        (declare seq_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk b) ) ))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-until
            (clk-prop-not (clk-prop-and (clk-prop-bool clk)  (clk-prop-not  (clk-prop-seq seq_a)  )   ))
            (clk-prop-and (clk-prop-bool clk) (clk-prop-seq seq_b) ) ))))"""

    check_clock_rewriting(input_document, output_document)



def test_clock_rewriting_nexttime_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-nexttime 1 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk
            (clk-prop-until (clk-prop-bool (not clk))
                (clk-prop-and (clk-prop-bool clk)
                (clk-prop-nexttime 1
                    (clk-prop-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk) prop_a)    ))))
        )))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_nexttime_0():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-nexttime 0 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_true (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk (true)) ) ))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-overlapped-implication seq_true prop_a) ) ))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_nexttime_2():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-nexttime 2 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk

            (clk-prop-until (clk-prop-bool (not clk))
                (clk-prop-and (clk-prop-bool clk)
                (clk-prop-nexttime 1
                    (clk-prop-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk)

                        (clk-prop-until (clk-prop-bool (not clk))
                            (clk-prop-and (clk-prop-bool clk)
                            (clk-prop-nexttime 1
                                (clk-prop-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk) prop_a

                        )))))

            )))))

        )))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_strong_nexttime_0():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-strong-nexttime 0 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_true (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk (true)) ) ))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-overlapped-followed-by seq_true prop_a) ) ))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_strong_nexttime_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-strong-nexttime 1 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk
            (clk-prop-strong-until (clk-prop-bool (not clk))
                (clk-prop-and (clk-prop-bool clk)
                (clk-prop-strong-nexttime 1
                    (clk-prop-strong-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk) prop_a)    ))))
        )))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_strong_nexttime_2():
    input_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (parse-sexpr (clk-prop-clocked clk (clk-prop-strong-nexttime 2 (clk-prop-bool a)))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input clk)
        (declare gclk (true))
        (declare prop_a (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk a) ) )))
        (parse-sexpr (clk-prop-clocked gclk

            (clk-prop-strong-until (clk-prop-bool (not clk))
                (clk-prop-and (clk-prop-bool clk)
                (clk-prop-strong-nexttime 1
                    (clk-prop-strong-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk)

                        (clk-prop-strong-until (clk-prop-bool (not clk))
                            (clk-prop-and (clk-prop-bool clk)
                            (clk-prop-strong-nexttime 1
                                (clk-prop-strong-until  (clk-prop-bool (not clk))  (clk-prop-and (clk-prop-bool clk) prop_a

                        )))))

            )))))

        )))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_same_child_twice():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare a_and_b (clk-seq-bool (and a b)))
        (parse-sexpr (clk-seq-clocked clk (clk-seq-concat a_and_b a_and_b) )))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_a_and_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk (and a b)) ) ))
        (parse-sexpr (clk-seq-clocked gclk (clk-seq-concat seq_a_and_b seq_a_and_b)))
    ) """

    check_clock_rewriting(input_document, output_document)


def test_clock_changes_behind_one_another():
    input_document: str = """(document
      (declare-input 0)
      (parse-sexpr
        (let-rec
          (step0 (constant false))
          (step1 (clk-seq-clocked step0 (clk-seq-bool 0)))
          (step2 (clk-seq-clocked step0 step1))
          step2)))"""

    output_document: str = """(document
        (declare-input 0)
        (declare gclk (true))
        (declare clk (constant false))
        (declare seq_0 (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk 0) ) ))
        (parse-sexpr (clk-seq-clocked gclk (clk-seq-clocked gclk seq_0))))"""

    check_clock_rewriting(input_document, output_document)


def test_clock_rewriting_node_labels():
    input_document: str = """(document
        (declare-input a)
        (declare-input c1)
        (declare-input c2)
        (declare p  (clk-prop-bool a))
        (declare clocked_1 (clk-prop-clocked c1 p))
        (declare clocked_2 (clk-prop-clocked c2 p))
        (parse-sexpr clocked_1)
        (parse-sexpr clocked_2)
        )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input c1)
        (declare-input c2)
        (declare gclk (true))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c1))) (clk-seq-bool (and c1 a)) ) )))
        (parse-sexpr (clk-prop-clocked gclk (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c2))) (clk-seq-bool (and c2 a)) ) )))
        )"""

    check_clock_rewriting(input_document, output_document, visualize=False)

    container1: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(input_document), container1)
    container2: IrContainer = rewrite_clocks(container1)

    clocked_1_id = container2.global_nodes['clocked_1']
    clocked_2_id = container2.global_nodes['clocked_2']
    assert isinstance(container2[clocked_1_id], ClkPropClocked)
    assert isinstance(container2[clocked_2_id], ClkPropClocked)
    found_p_clk_labels: int = 0
    for name, node_id in container2.global_nodes.items():
        if name.startswith('p_clk_'):
            found_p_clk_labels += 1
            assert isinstance(container2[node_id], ClkPropSeq)
    assert found_p_clk_labels == 2



def test_clock_rewriting_root_node_already_finished():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare a_and_b (clk-seq-bool (and a b)))
        (declare inner (clk-seq-clocked clk (clk-seq-concat a_and_b a_and_b) ))
        (declare outer (clk-seq-clocked clk inner))
        (parse-sexpr outer)
        (parse-sexpr inner)
        )"""

    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input clk)
        (declare gclk (true))
        (declare seq_a_and_b (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not clk)) ) (clk-seq-bool (and clk (and a b)) ) ))
        (declare inner (clk-seq-clocked gclk (clk-seq-concat seq_a_and_b seq_a_and_b)))
        (declare outer (clk-seq-clocked gclk inner))
        (parse-sexpr outer)
        (parse-sexpr inner)
    ) """

    check_clock_rewriting(input_document, output_document)



def check_clock_rewriting_no_error(doc):
    doc_raw_sexpr: RawSExprList = parse_raw_sexpr(doc)
    container1: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container1)
    container2: IrContainer = rewrite_clocks(container1)
    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'check_clock_rewriting_input.png')
    #container2.show_graph(output_directory / 'check_clock_rewriting_output.png')
    container2.canonical_id_renaming(remove_unreachable_declared_nodes=False)

@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given((random_ir_clocked(final_node_type=ClkSeqClocked, primitive_filter=lambda node_type: False if issubclass(node_type, ClockedProperty) else True)))
def test_clock_rewriting_random_seq_no_error(doc):
    check_clock_rewriting_no_error(doc)

@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given((random_ir_clocked(final_node_type=ClkPropClocked)))
def test_clock_rewriting_prop_no_error(doc):
    check_clock_rewriting_no_error(doc)