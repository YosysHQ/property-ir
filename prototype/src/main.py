from __future__ import annotations
from pathlib import Path

from sexpr import parse_expression, parse_raw_sexpr, IrContainer, Signal, RawSExpr


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


    expr_list1: RawSExpr = parse_raw_sexpr(test_expr1)
    print()
    expr_list2: RawSExpr = parse_raw_sexpr(test_expr2)
    print()
    expr_list3: RawSExpr = parse_raw_sexpr(test_expr3)
    print()
    expr_list4: RawSExpr = parse_raw_sexpr(test_expr4)
    print()
    expr_list5: RawSExpr = parse_raw_sexpr(test_expr5)
    print()
    expr_list6: RawSExpr = parse_raw_sexpr(test_expr6)
    print()
    expr_list7: RawSExpr = parse_raw_sexpr(test_expr7)
    print()
    expr_list8: RawSExpr = parse_raw_sexpr(test_expr8)
    print()
    expr_list9: RawSExpr = parse_raw_sexpr(test_expr9)
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


    #parse_expression(expr_list1, None, ir_container1.global_nodes, ir_container1)
    print()
    #parse_expression(expr_list2, None, signal_dict, ir_container2)
    #print()
    #parse_expression(expr_list3, None, signal_dict, ir_container3)
    #print()
    #parse_expression(expr_list4, None, signal_dict, ir_container4)
    #print()
    #parse_expression(expr_list5, None, signal_dict, ir_container5)
    #print()
    parse_expression(expr_list6, None, ir_container1.global_nodes, ir_container1)
    #print()
    #parse_expression(expr_list7, None, signal_dict, ir_container7)
    #print()
    #parse_expression(expr_list8, None, signal_dict, ir_container8)
    #print()
    #parse_expression(expr_list9, None, signal_dict, ir_container9)

    #print()
    #print(ir_container7.nodes)
    #print()
    #print(ir_container7.node_names)
    #print()
    #print(ir_container7.merged_nodes.parents)
    #print()

    #ir_container1.show_graph(output_directory / 'container1.png')
    ir_container1.bypass_placeholders()

    #print()
    #print(ir_container7.nodes)
    #print()
    #print(ir_container7.node_names)
    #print()
    #print(ir_container7.merged_nodes.parents)
    #print()

    #ir_container1.show_graph(output_directory / 'container1_no_placeholders.png')


if __name__ == "__main__":

    main()
