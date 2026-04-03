import pytest
import logging
from pathlib import Path

from sexpr.parsing import parse_document
from tests.helpers import wrap_multiple_statements_in_document, wrap_statement_in_document
from sexpr import IrContainer, nnf
from sexpr.base import RawSExprList


logger = logging.getLogger(__name__)



def check_nnf_equivalence(input_document: RawSExprList, expected_output_document: RawSExprList):
    container = IrContainer()
    parse_document(input_document, container)


    output_container = nnf(container)

    expected_output_container = IrContainer()
    parse_document(expected_output_document, expected_output_container)

    output_container.canonical_id_renaming()
    expected_output_container.canonical_id_renaming()

    output_directory: Path = Path('./output')
    container.show_graph(output_directory / 'check_nnf_equ_input.png')
    output_container.show_graph(output_directory / 'check_nnf_equ_output.png')
    expected_output_container.show_graph(output_directory / 'check_nnf_equ_expected_output.png')


    assert output_container == expected_output_container



def test_nnf_boolean_no_cycle():
    input_statement1: RawSExprList = ['declare', 'h', ['and', 'a', 'b']]
    input_statement2: RawSExprList = ['declare', 'q', ['or', 'b', 'c']]
    input_statement3: RawSExprList = ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], 'q']]
    expected_output_statement3: RawSExprList = ['declare-rec', ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], ['or', 'c', 'p']]]]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'h']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, expected_output_statement3, root_node_statement1, root_node_statement2])
    check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_boolean_even_cycle():
    input_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'p', ['not', ['and', ['or', 'a', 'b'], ['not', ['or', 'c', 'p']]]]]]
    expected_output_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], ['or', 'c', 'p']]]]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']

    input_document: RawSExprList = wrap_multiple_statements_in_document([input_raw_sexpr, root_node_statement1])
    expected_output_document = wrap_multiple_statements_in_document([expected_output_raw_sexpr, root_node_statement1])
    check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_boolean_odd_cycle():
    with pytest.raises(ValueError, match='odd number of negations'):
        input_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'q', ['not', ['and', ['or', ['not', 'a'], 'b'], 'q']]]]
        expected_output_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'q', ['or', 'c', 'q']]] # arbitrary, since never tested
        root_node_statement1: RawSExprList = ['parse-sexpr', 'q']

        input_document: RawSExprList = wrap_multiple_statements_in_document([input_raw_sexpr, root_node_statement1])
        expected_output_document: RawSExprList = wrap_statement_in_document(expected_output_raw_sexpr)
        check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_boolean_shared_subgraph():
    input_statement1: RawSExprList = ['declare', 'p', ['or', 'a', 'b']]
    input_statement2: RawSExprList = ['declare', 'h', ['not', 'p']]
    input_statement3: RawSExprList = ['declare', 'q', ['and', 'c', 'p']]
    expected_output_statement2: RawSExprList = ['declare', 'q', ['and', 'c', 'p']]
    expected_output_statement3: RawSExprList = ['declare', 'h', ['and', ['not', 'a'], ['not', 'b']]]

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, expected_output_statement2, expected_output_statement3])
    check_nnf_equivalence(input_document, expected_output_document)