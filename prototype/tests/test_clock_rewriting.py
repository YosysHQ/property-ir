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

    container2.canonical_id_renaming()
    container3.canonical_id_renaming()

    #container2.show_graph(output_directory / 'check_clock_rewriting_expected_output.png')
    #container3.show_graph(output_directory / 'check_clock_rewriting_output_after_renaming.png')

    assert container3 == container2



def test_clock_rewriting1():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked c (clk-prop-bool a))))"""

    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-seq (clk-seq-concat (clk-seq-repeat (range 0 $) (clk-seq-bool (not c))) (clk-seq-bool (and c a))) ))))"""

    check_clock_rewriting(input_document, output_document)


@pytest.mark.xfail(reason='implementation not finished yet')
def test_clock_rewriting2():
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
        (declare-input c2))"""

    check_clock_rewriting(input_document, output_document)