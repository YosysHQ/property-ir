from pathlib import Path
import pytest

from sexpr.base import NodeId, RawSExprList, IrContainer, ClockedProperty, ClockedSequence
from sexpr.parsing import parse_document, parse_raw_sexpr
from sexpr.rewriting import precompute_node_info, remove_empty_matches


def test_precompute_node_info_1():

    input_document_str: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare s2 (clk-seq-repeat (range 1 5) (clk-seq-or s1 (clk-seq-concat (clk-seq-bool a) s1 ) )) )
        (declare p (clk-prop-clocked c (clk-prop-seq s2)) )
        (parse-sexpr p))"""
    input_document: RawSExprList = parse_raw_sexpr(input_document_str)

    container: IrContainer = IrContainer()
    parse_document(input_document, container)

    admits_empty, admits_only_empty, no_match = precompute_node_info(container)

    empty_seq_node_id: NodeId = container.get_node_id_by_name('s1')
    empty_seq_node_repr = container.merged_nodes.find(empty_seq_node_id)

    assert(admits_empty[empty_seq_node_repr] == True)
    assert(admits_only_empty[empty_seq_node_repr] == True)
    assert(no_match[empty_seq_node_repr] == False)

    seq2_node_id: NodeId = container.get_node_id_by_name('s2')
    seq2_node_repr = container.merged_nodes.find(seq2_node_id)

    assert(admits_empty[seq2_node_repr] == True)
    assert(admits_only_empty[seq2_node_repr] == False)
    assert(no_match[seq2_node_repr] == False)



def check_empty_match_removal(input_document_str: str, expected_output_document_str: str, visualize: bool = False):

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_empty_match_removal_input.png')

    container3: IrContainer = remove_empty_matches(container1) # for output

    parse_document(expected_output_document, container2)

    if visualize:
        container3.show_graph(output_directory / 'check_empty_match_removal_output_before_renaming.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_empty_match_removal_expected_output.png')

    container3.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container3.show_graph(output_directory / 'check_empty_match_removal_output_after_renaming.png')

    assert container3.weakly_equivalent(container2)



def test_empty_match_removal_no_change_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input b)
        (declare-input c)
        (parse-sexpr (clk-prop-clocked (true) (clk-prop-weak (clk-seq-bool (and a (not b) (or b c))) ) )) )"""
    output_document: str = input_document
    check_empty_match_removal(input_document, output_document, visualize=False)


def test_empty_match_removal_no_change_2():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool c))
        (declare s2 (clk-seq-repeat (range 1 5) (clk-seq-or s1 (clk-seq-concat (clk-seq-bool a) s1 ) )) )
        (declare p (clk-prop-clocked c (clk-prop-seq s2)) )
        (parse-sexpr p))"""
    output_document: str = input_document
    check_empty_match_removal(input_document, output_document, visualize=False)

def test_empty_match_removal_no_change_3():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool c))
        (declare s2 (clk-seq-repeat (range 1 5) (clk-seq-or s1 (clk-seq-concat (clk-seq-bool a) s1 ) )) )
        (declare p (clk-prop-clocked c (clk-prop-overlapped-implication s1 (clk-prop-seq s2)) ))
        (parse-sexpr p))"""
    output_document: str = input_document
    check_empty_match_removal(input_document, output_document, visualize=False)

def test_empty_match_removal_no_change_4():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool c))
        (declare s2 (clk-seq-repeat (range 1 5) (clk-seq-or s1 (clk-seq-concat (clk-seq-bool a) s1 ) )) )
        (declare-rec (declare p (clk-prop-clocked c (clk-prop-overlapped-implication s2 (clk-prop-or p (clk-prop-weak s1))) )))
        (parse-sexpr p))"""
    output_document: str = input_document
    check_empty_match_removal(input_document, output_document, visualize=False)



def test_empty_match_removal_or():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare no_match (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare maybe_match (clk-seq-repeat (range 0 5) (clk-seq-bool a)) )
        (declare s3 (clk-seq-or s1 s2 no_match maybe_match))
        (parse-sexpr s3))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare has_match (clk-seq-repeat (range 1 5) (clk-seq-bool a)) )
        (declare s3 (clk-seq-or s1 s2 has_match))
        (parse-sexpr s3))"""
    check_empty_match_removal(input_document, output_document, visualize=False)


def test_empty_match_removal_concat_1():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare no_match (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare maybe_match (clk-seq-repeat (range 0 5) (clk-seq-bool a)) )
        (declare s3 (clk-seq-concat s1 s2 no_match maybe_match))
        (parse-sexpr s3))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare has_match (clk-seq-repeat (range 1 5) (clk-seq-bool a)) )
        (declare s3 (clk-seq-or
            (clk-seq-concat s1 s2 has_match)
            (clk-seq-concat s1 s2) ))
        (parse-sexpr s3))"""
    # note: the sequences in clk-seq-or would also be correct in a different order, but this is the one generated
    check_empty_match_removal(input_document, output_document, visualize=False)

def test_empty_match_removal_concat_2():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare no_match (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare maybe_match1 (clk-seq-repeat (range 0 5) (clk-seq-bool a)) )
        (declare maybe_match2 (clk-seq-repeat (range 0 3) (clk-seq-bool a)) )
        (declare s3 (clk-seq-concat s1 maybe_match1 s2 no_match maybe_match2))
        (parse-sexpr s3))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare s1 (clk-seq-bool a))
        (declare s2 (clk-seq-bool c))
        (declare has_match1 (clk-seq-repeat (range 1 5) (clk-seq-bool a)) )
        (declare has_match2 (clk-seq-repeat (range 1 3) (clk-seq-bool a)) )
        (declare s3 (clk-seq-or
            (clk-seq-concat s1 has_match1 s2 has_match2)
            (clk-seq-concat s1 s2 has_match2)
            (clk-seq-concat s1 has_match1 s2)
            (clk-seq-concat s1 s2) ))
        (parse-sexpr s3))"""
    # note: the sequences in clk-seq-or would also be correct in a different order, but this is the one generated
    check_empty_match_removal(input_document, output_document, visualize=False)


# TODO
@pytest.mark.xfail(reason='no-match sequence only handled correctly when inside property')
def test_empty_match_removal_no_match_seq():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare no_match1 (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare no_match2 (clk-seq-repeat (range 0 0) (clk-seq-bool c)) )
        (declare s3 (clk-seq-concat no_match1 no_match2))
        (parse-sexpr s3))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-seq-no-match)))"""
    check_empty_match_removal(input_document, output_document, visualize=False)


def test_empty_match_removal_no_match_prop():
    input_document: str = """(document
        (declare-input a)
        (declare-input c)
        (declare no_match1 (clk-seq-repeat (range 0 0) (clk-seq-bool a)) )
        (declare no_match2 (clk-seq-repeat (range 0 0) (clk-seq-bool c)) )
        (declare s3 (clk-seq-concat no_match1 no_match2))
        (parse-sexpr (clk-prop-weak s3)))"""
    output_document: str = """(document
        (declare-input a)
        (declare-input c)
        (parse-sexpr (clk-prop-weak (clk-seq-no-match))))"""
    check_empty_match_removal(input_document, output_document, visualize=False)





# TODO
#def test_empty_match_removal_random():
#    pass