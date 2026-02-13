from __future__ import annotations
from pathlib import Path

from sexpr import parse_expression, parse_raw_sexpr, IrContainer, Signal, RawSExprList, unparse_raw_sexpr
from sexpr.base import SignalDeclaration


output_directory: Path = Path('prototype/output')



def main():

    test_expr1 = '(or (and a b) (not (and (not a) c)) d)'

    test_expr2 = """(seq-concat
                        (seq-repeat (range 5 5) (seq-bool a))
                        (seq-concat (seq-bool b) (seq-bool c)))"""

    test_expr3 = """(prop-always-ranged
                        (range 4 $)
                        (prop-seq (seq-bool (not b))))"""

    test_expr4 = """(prop-always (prop-and
                        (prop-seq (seq-bool (not b)))
                        (prop-seq (seq-bool a))
                    ))"""


    test_expr5 = """(let-rec
        (foo (and a bar))
        (bar (or b c))
        foo
    )"""

    test_expr6 = """(let-rec
                        (prop1 (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool (constant true)) prop2)))
                        (prop2 (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool (constant true)) prop1)))
                        prop1)"""

    test_expr7 = """(let-rec
        (q1 (seq-concat (seq-bool a) q3))
        (q2 (seq-concat (seq-bool b) q4))
        (q3 q4)
        (q4 (seq-bool c))
        (q5 q3)
        (seq-concat (seq-bool d) q5)
    )"""

    # nested let-rec
    test_expr8 = """(let-rec
        (q1 (and a b))
        (q2 (let-rec
                (p1 (not q1))
                (p2 q1)
                (p3 (or q2 c))
                p3))
        q2)"""

    # this should cause a type error
    test_expr9 = """(let-rec
        (foo2 (and a bar2))
        (bar2 (seq-concat (seq-bool a) (seq-bool b)))
        foo2)"""

    #signal_dict = {'a': Signal('a'), 'b': Signal('b'), 'c': Signal('c'), 'd': Signal('d')}


    expr_list1: RawSExprList = parse_raw_sexpr(test_expr1)
    print()
    expr_list2: RawSExprList = parse_raw_sexpr(test_expr2)
    print()
    expr_list3: RawSExprList = parse_raw_sexpr(test_expr3)
    print()
    expr_list4: RawSExprList = parse_raw_sexpr(test_expr4)
    print()
    expr_list5: RawSExprList = parse_raw_sexpr(test_expr5)
    print()
    expr_list6: RawSExprList = parse_raw_sexpr(test_expr6)
    print()
    expr_list7: RawSExprList = parse_raw_sexpr(test_expr7)
    print()
    expr_list8: RawSExprList = parse_raw_sexpr(test_expr8)
    print()
    expr_list9: RawSExprList = parse_raw_sexpr(test_expr9)
    print()

    ir_container1 = IrContainer()
    ir_container2 = IrContainer()
    ir_container3 = IrContainer()
    ir_container4 = IrContainer()
    ir_container5 = IrContainer()
    ir_container6 = IrContainer()
    ir_container7 = IrContainer()
    ir_container8 = IrContainer()
    ir_container9 = IrContainer()

    signal_node1 = ir_container1.add_signal_node('a')
    signal_node2 = ir_container1.add_signal_node('b')
    signal_node3 = ir_container1.add_signal_node('c')
    signal_node4 = ir_container1.add_signal_node('d')

    signal_dict = {signal_node1.node_id: 'a', signal_node2.node_id: 'b', signal_node3.node_id: 'c', signal_node4.node_id: 'd'}

    print()

    unparsed_expr1 = unparse_raw_sexpr(expr_list1)
    print(unparsed_expr1)

    unparsed_expr2 = unparse_raw_sexpr(expr_list2)
    print(unparsed_expr2)

    ir_container1.add_declaration(SignalDeclaration('a', signal_node1.node_id))
    ir_container1.add_declaration(SignalDeclaration('b', signal_node2.node_id))
    ir_container1.add_declaration(SignalDeclaration('c', signal_node3.node_id))
    ir_container1.add_declaration(SignalDeclaration('d', signal_node4.node_id))

    root_node_id1 = parse_expression(expr_list6, None, ir_container1.global_nodes, ir_container1)
    print()
    #parse_expression(expr_list2, None, signal_dict, ir_container2)
    #print()
    #parse_expression(expr_list3, None, signal_dict, ir_container3)
    #print()
    #parse_expression(expr_list4, None, signal_dict, ir_container4)
    #print()
    #parse_expression(expr_list5, None, signal_dict, ir_container5)
    #print()
    #parse_expression(expr_list6, None, ir_container1.global_nodes, ir_container1)
    #print()
    #parse_expression(expr_list7, None, signal_dict, ir_container7)
    #print()
    #parse_expression(expr_list8, None, signal_dict, ir_container8)
    #print()
    #parse_expression(expr_list9, None, signal_dict, ir_container9)

    #ir_container1.show_graph(output_directory / 'container1.png')

    #ir_container1.make_top_level_node(root_node_id1)
    #print(ir_container1.root_nodes)
    #print(ir_container1.generate_raw_sexpr(root_node_id1, declared_nodes=signal_dict))

    #print()
    #print(ir_container7.nodes)
    #print()
    #print(ir_container7.node_names)
    #print()
    #print(ir_container7.merged_nodes.parents)
    #print()

    ir_container1.bypass_placeholders()

    #print()
    #print(ir_container7.nodes)
    #print()
    #print(ir_container7.node_names)
    #print()
    #print(ir_container7.merged_nodes.parents)
    #print()

    #ir_container1.show_graph(output_directory / 'container1.png')


if __name__ == "__main__":

    main()
