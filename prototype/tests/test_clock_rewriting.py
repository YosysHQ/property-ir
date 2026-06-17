import pytest
from pathlib import Path

from sexpr.base import RawSExprList, IrContainer
from sexpr.parsing import parse_raw_sexpr, parse_document
from sexpr.rewriting import rewrite_clocks


def check_clock_rewriting(input_document_str: str, expected_output_document_str: str):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input and output (rewrite in-place)
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'check_clock_rewriting_input.png')

    container3: IrContainer = rewrite_clocks(container1)

    parse_document(expected_output_document, container2)

    #container3.show_graph(output_directory / 'check_clock_rewriting_output_before_renaming.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)
    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    #container2.show_graph(output_directory / 'check_clock_rewriting_expected_output.png')
    #container3.show_graph(output_directory / 'check_clock_rewriting_output_after_renaming.png')

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



def test_clock_rewriting_no_change():
    input_document: str = """(document
        (declare-input a)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-bool a))))"""
    output_document: str = input_document
    check_clock_rewriting(input_document, output_document)


@pytest.mark.xfail(reason='writing test not finished yet')
def test_clock_rewriting_clock_change():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        (parse-sexpr (clk-prop-clocked c1 (clk-prop-seq (clk-seq-concat (clk-seq-bool a) (clk-seq-clocked c2 (clk-seq-bool b)) )))))"""

    # TODO write expected output
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2)
        )"""

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

@pytest.mark.xfail(reason='writing test not finished yet')
def test_clock_rewriting_with_cycle():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (declare-rec (declare p (clk-prop-clocked c (clk-prop-non-overlapped-implication (clk-seq-bool a) (clk-prop-and (clk-prop-bool b) p) ))))
        (parse-sexpr p))"""

    # TODO write expected output
    output_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c1)
        (declare-input c2))"""

    check_clock_rewriting(input_document, output_document)


# TODO
@pytest.mark.xfail(reason='writing test not finished yet')
def test_clock_rewriting_nexttime():
    pass