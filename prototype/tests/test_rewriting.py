import pytest
import logging
from pathlib import Path

from sexpr.parsing import parse_document, parse_raw_sexpr
from tests.helpers import wrap_multiple_statements_in_document, wrap_statement_in_document
from sexpr import IrContainer, nnf
from sexpr.base import RawSExprList
from tests.input_data import raw_sexpr6_declare_rec


logger = logging.getLogger(__name__)



def check_nnf_equivalence(input_document: RawSExprList, expected_output_document: RawSExprList):
    container = IrContainer()
    parse_document(input_document, container)

    expected_output_container = IrContainer()
    parse_document(expected_output_document, expected_output_container)

    container.bypass_placeholders()
    container.canonical_id_renaming()
    expected_output_container.bypass_placeholders()
    expected_output_container.canonical_id_renaming()

    #output_directory: Path = Path('./output')
    #container.show_graph(output_directory / 'check_nnf_equ_input.png')
    #expected_output_container.show_graph(output_directory / 'check_nnf_equ_expected_output.png')

    output_container = nnf(container)

    #output_container.show_graph(output_directory / 'check_nnf_equ_output_before_renaming.png')

    output_container.bypass_placeholders()
    output_container.canonical_id_renaming()

    #output_container.show_graph(output_directory / 'check_nnf_equ_output_after_renaming.png')

    assert output_container == expected_output_container




# NNF booleans


def test_nnf_boolean_no_cycle():
    input_statement1: RawSExprList = ['declare', 'h', ['and', 'a', 'b']]
    input_statement2: RawSExprList = ['declare', 'q', ['or', 'b', 'c']]
    input_statement3: RawSExprList = ['declare', 'p', ['not', ['and', ['or', 'a', 'b'], ['not', 'q']]]]
    expected_output_statement3: RawSExprList = ['declare-rec', ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], 'q']]]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'h']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'q']
    root_node_statement3: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, expected_output_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_boolean_no_change():
    input_statement1: RawSExprList = ['declare', 'h', ['and', 'a', 'b']]
    input_statement2: RawSExprList = ['declare', 'q', ['or', 'b', 'c']]
    input_statement3: RawSExprList = ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], 'q']]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'h']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'q']
    root_node_statement3: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
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
    expected_output_statement2: RawSExprList = ['declare', 'h', ['and', ['not', 'a'], ['not', 'b']]]
    expected_output_statement3: RawSExprList = ['declare', 'q', ['and', 'c', 'p']]
    expected_output_statement4: RawSExprList = ['declare', 'p_neg', 'h']
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'h']
    root_node_statement3: RawSExprList = ['parse-sexpr', 'q']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, expected_output_statement2, expected_output_statement3, expected_output_statement4, root_node_statement1, root_node_statement2, root_node_statement3])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_boolean_global_name_of_not_unchanged():
    input_statement1: RawSExprList = ['declare', 'p', ['not', 'a']]
    input_statement2: RawSExprList = ['declare', 'q', ['not', 'b']]
    input_statement3: RawSExprList = ['declare', 'h', ['and', 'p', 'q']]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'q']
    root_node_statement3: RawSExprList = ['parse-sexpr', 'h']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    check_nnf_equivalence(input_document, expected_output_document)



def test_nnf_boolean_constant_even_cycle():
    input_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'p', ['not', ['and', ['or', ['true'], ['false']], ['not', ['or', ['constant', 'true'], 'p']]]]]]
    expected_output_raw_sexpr: RawSExprList = ['declare-rec', ['declare', 'p', ['or', ['and', ['false'], ['true']], ['or', ['true'], 'p']]]]
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']

    input_document: RawSExprList = wrap_multiple_statements_in_document([input_raw_sexpr, root_node_statement1])
    expected_output_document = wrap_multiple_statements_in_document([expected_output_raw_sexpr, root_node_statement1])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_boolean_constant_shared_subgraph():
    input_statement1: RawSExprList = ['declare', 'p', ['or', ['true'], ['false']]]
    input_statement2: RawSExprList = ['declare', 'h', ['not', 'p']]
    input_statement3: RawSExprList = ['declare', 'q', ['and', 'c', 'p']]
    expected_output_statement2: RawSExprList = ['declare', 'h', ['and', ['false'], ['true']]]
    expected_output_statement3: RawSExprList = ['declare', 'q', ['and', 'c', 'p']]
    expected_output_statement4: RawSExprList = ['declare', 'p_neg', 'h']
    root_node_statement1: RawSExprList = ['parse-sexpr', 'p']
    root_node_statement2: RawSExprList = ['parse-sexpr', 'h']
    root_node_statement3: RawSExprList = ['parse-sexpr', 'q']

    input_document = wrap_multiple_statements_in_document([input_statement1, input_statement2, input_statement3, root_node_statement1, root_node_statement2, root_node_statement3])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, expected_output_statement2, expected_output_statement3, expected_output_statement4, root_node_statement1, root_node_statement2, root_node_statement3])
    check_nnf_equivalence(input_document, expected_output_document)





def check_single_declaration_nnf_helper(input_str, output_str):
    input_statement = parse_raw_sexpr(input_str)
    output_statement = parse_raw_sexpr(output_str)
    root_statement: RawSExprList = ['parse-sexpr', 'p']
    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement, root_statement])
    expected_output_document = wrap_multiple_statements_in_document([output_statement, root_statement])
    check_nnf_equivalence(input_document, expected_output_document)



# NNF sequences

def test_nnf_sequence_type_unchanged():
    input_statement_str1: str = """(declare p (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c))))"""
    check_single_declaration_nnf_helper(input_statement_str1, input_statement_str1)

def test_nnf_sequence_unchanged_positive():
    input_statement_str1: str = """(declare p (prop-seq (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c)))))"""
    check_single_declaration_nnf_helper(input_statement_str1, input_statement_str1)

def test_nnf_sequence_unchanged_negative():
    input_statement_str1: str = """(declare p (prop-not (prop-seq (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c))))))"""
    check_single_declaration_nnf_helper(input_statement_str1, input_statement_str1)

def test_nnf_sequence_weak_unchanged():
    input_statement_str1: str = """(declare p (prop-not (prop-weak (seq-bool a))))"""
    check_single_declaration_nnf_helper(input_statement_str1, input_statement_str1)

def test_nnf_sequence_strong():
    input_statement_str1: str = """(declare p (prop-not (prop-strong (seq-bool a))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-implication (seq-bool a) (prop-bool (constant false))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


# NNF properties single primitives

def test_nnf_property_reject_on():
    input_statement_str1: str = """(declare p (prop-not (prop-reject-on a (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-accept-on a (prop-not (prop-bool b))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_accept_on():
    input_statement_str1: str = """(declare p (prop-not (prop-accept-on a (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-reject-on a (prop-not (prop-bool b))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_implication():
    input_statement_str1: str = """(declare p (prop-not (prop-overlapped-implication (seq-bool a) (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-followed-by (seq-bool a) (prop-not (prop-bool b))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_followed_by():
    input_statement_str1: str = """(declare p (prop-not (prop-overlapped-followed-by (seq-bool a) (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-implication (seq-bool a) (prop-not (prop-bool b))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_until():
    input_statement_str1: str = """(declare p (prop-not (prop-until (prop-bool a) (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-strong-until-with (prop-not (prop-bool b)) (prop-not (prop-bool a))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_s_until_with():
    input_statement_str1: str = """(declare p (prop-not (prop-strong-until-with (prop-bool a) (prop-bool b))))"""
    output_statement_str1: str = """(declare p (prop-until (prop-not (prop-bool b)) (prop-not (prop-bool a))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_nexttime():
    input_statement_str1: str = """(declare p (prop-not (prop-nexttime 5 (prop-bool a))))"""
    output_statement_str1: str = """(declare p (prop-strong-nexttime 5 (prop-not (prop-bool a))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_s_nexttime():
    input_statement_str1: str = """(declare p (prop-not (prop-strong-nexttime 5 (prop-bool a))))"""
    output_statement_str1: str = """(declare p (prop-nexttime 5 (prop-not (prop-bool a))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_or_and():
    input_statement_str1: str = """(declare p (prop-not (prop-and (prop-or (prop-bool a) (prop-bool b)) (prop-and (prop-bool c) (prop-bool d)) )))"""
    output_statement_str1: str = """(declare p (prop-or
        (prop-and (prop-not (prop-bool a)) (prop-not (prop-bool b)) )
        (prop-or (prop-not (prop-bool c)) (prop-not (prop-bool d)) ) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)



# NNF properties larger examples

def test_nnf_property_unchanged_positive():
    input_statement1: RawSExprList = raw_sexpr6_declare_rec
    root_statement1: RawSExprList = ['parse-sexpr', 'prop1']
    root_statement2: RawSExprList = ['parse-sexpr', 'prop2']
    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, root_statement1, root_statement2])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, root_statement1, root_statement2])
    check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_property_multiple_replacements():
    input_statement_str1: str = """(declare p
        (prop-not (prop-overlapped-implication
            (seq-bool a)
            (prop-until (prop-bool b) (prop-not (prop-bool c)) )
        )))"""
    output_statement_str1: str = """(declare p
        (prop-overlapped-followed-by
            (seq-bool a)
            (prop-strong-until-with (prop-bool c) (prop-not (prop-bool b)) )
        ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


def test_nnf_property_even_cycle():
    input_statement_str1: str = """(declare-rec (declare p
        (prop-not (prop-overlapped-implication
            (seq-concat (seq-bool a) (seq-bool (constant true)))
            (prop-not (prop-and (prop-bool b) p))
        ))))"""
    output_statement_str1: str = """(declare-rec (declare p
        (prop-overlapped-followed-by
            (seq-concat (seq-bool a) (seq-bool (constant true)))
            (prop-and (prop-bool b) p)
        )))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


def test_nnf_property_odd_cycle():
    with pytest.raises(ValueError, match='odd number of negations'):
        input_statement_str1: str = """(declare-rec (declare p
            (prop-not (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)))
                (prop-and (prop-bool b) p)
            ))))"""
        output_statement_str1: str = """(declare p (prop-bool a))""" # arbitrary because an error is expected anyway
        check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_shared_subgraph():
    input_statement_str1: str = """(declare q (prop-not (prop-bool c)))"""
    input_statement_str2: str = """(declare p
        (prop-not (prop-overlapped-implication
            (seq-bool a)
            (prop-until (prop-bool b) q)
        )))"""
    input_statement1 = parse_raw_sexpr(input_statement_str1)
    input_statement2 = parse_raw_sexpr(input_statement_str2)

    output_statement_str0: str = """(declare q_neg (prop-bool c))"""
    output_statement_str1: str = """(declare q (prop-not q_neg))"""
    output_statement_str2: str = """(declare p
        (prop-overlapped-followed-by
            (seq-bool a)
            (prop-strong-until-with q_neg (prop-not (prop-bool b)) )
        ))"""
    output_statement_str: str = '(declare-rec' + output_statement_str1 + output_statement_str2 + output_statement_str0 + ')'
    output_statement = parse_raw_sexpr(output_statement_str)

    root_statement1: RawSExprList = ['parse-sexpr', 'q']
    root_statement2: RawSExprList = ['parse-sexpr', 'p']

    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, input_statement2, root_statement1, root_statement2])
    expected_output_document = wrap_multiple_statements_in_document([output_statement, root_statement1, root_statement2])
    check_nnf_equivalence(input_document, expected_output_document)