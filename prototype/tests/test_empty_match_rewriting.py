

from logging import root
from sexpr.base import NodeId, RawSExprList, IrContainer, ClockedProperty, ClockedSequence
from sexpr.parsing import parse_document, parse_raw_sexpr
from sexpr.rewriting import precompute_node_info

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