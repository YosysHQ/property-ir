from pathlib import Path

from ir.automata import remove_omega_call_all
from ir.base import IrContainer, NodeId, RawSExprList
from ir.parsing import parse_document, parse_raw_sexpr


def check_subcall_removal(input_document_str: str, expected_output_document_str: str, visualize: bool = False) -> IrContainer:

    input_document: RawSExprList = parse_raw_sexpr(input_document_str)
    expected_output_document: RawSExprList = parse_raw_sexpr(expected_output_document_str)

    container1: IrContainer = IrContainer() # for input
    container2: IrContainer = IrContainer() # for expected output
    parse_document(input_document, container1)
    parse_document(expected_output_document, container2)

    output_directory: Path = Path('./output')

    if visualize:
        container1.show_graph(output_directory / 'check_subcall_removal_input.png')

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container2.show_graph(output_directory / 'check_subcall_removal_expected_output.png')

    root_id: NodeId = container1.directives[0].node_id
    remove_omega_call_all(root_id, container1)

    container1.canonical_id_renaming(remove_unreachable_declared_nodes=True)

    if visualize:
        container1.show_graph(output_directory / 'check_subcall_removal_output.png')

    assert container1 == container2

    return container1



def test_remove_omega_call_all():

    input_document: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr (omega-call-all
            (aut-read a (aut-acc (aut-false)) (aut-false) )
            (omega-true)
        ))
    )"""

    expected_output: str = """(document
        (declare-input a)
        (declare-input b)

        (parse-sexpr
            (omega-weak-read a (omega-true) (omega-true))
        )
    )"""

    check_subcall_removal(input_document, expected_output, visualize=False)
