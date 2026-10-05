import logging
from pathlib import Path

import pytest
from hypothesis import example, given, settings
from ir import IrContainer, nnf
from ir.base import NodeId, RawSExprList
from ir.parsing import parse_document, parse_raw_sexpr, unparse_raw_sexpr
from ir.primitives.bool_primitives import (
    ChangingGclk,
    Eq,
    FallingGclk,
    Ite,
    RisingGclk,
    Xor,
)
from ir.primitives.simple_primitives import PropNot, PropRefuted

from tests.evaluate import (
    BoolMemoDict,
    MaybeBool,
    PropertyMemoDict,
    SequenceMemoDict,
    Trace,
    evaluate_property,
)
from tests.helpers import (
    wrap_multiple_statements_in_document,
    wrap_statement_in_document,
)
from tests.strategies import random_ir_with_trace_simple

logger = logging.getLogger(__name__)



def check_nnf_equivalence(input_document: RawSExprList, expected_output_document: RawSExprList, visualize: bool = False):
    container = IrContainer()
    parse_document(input_document, container)

    expected_output_container = IrContainer()
    parse_document(expected_output_document, expected_output_container)

    container.bypass_placeholders()
    container.canonical_id_renaming()
    expected_output_container.bypass_placeholders()
    expected_output_container.canonical_id_renaming()

    output_directory: Path = Path('./output')
    if visualize:
        container.show_graph(output_directory / 'check_nnf_equ_input.png')
        expected_output_container.show_graph(output_directory / 'check_nnf_equ_expected_output.png')

    output_container = nnf(container)

    if visualize:
        output_container.show_graph(output_directory / 'check_nnf_equ_output_before_renaming.png')

    output_container.bypass_placeholders()
    output_container.canonical_id_renaming()

    if visualize:
        output_container.show_graph(output_directory / 'check_nnf_equ_output_after_renaming.png')

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

def test_nnf_boolean_initial_positive():
    input_statement: RawSExprList = ['declare', 'p', ['and', ['or', 'a', 'b'], ['initial']]]
    root_node_statement: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement, root_node_statement])
    expected_output_document = input_document
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_boolean_initial_negative():
    input_statement: RawSExprList = ['declare', 'p', ['not', ['and', ['or', 'a', 'b'], ['initial']]]]
    expected_output_statement: RawSExprList = ['declare', 'p', ['or', ['and', ['not', 'a'], ['not', 'b']], ['not', ['initial']]]]
    root_node_statement: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement, root_node_statement])
    expected_output_document = wrap_multiple_statements_in_document([expected_output_statement, root_node_statement])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_boolean_future_gclk():
    input_statement: RawSExprList = ['declare', 'p', ['not', ['and', ['or', ['future-gclk', 'a'], 'b']]]]
    expected_output_statement: RawSExprList = ['declare', 'p', ['or', ['and', ['future-gclk', ['not', 'a']], ['not', 'b']]]]
    root_node_statement: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement, root_node_statement])
    expected_output_document = wrap_multiple_statements_in_document([expected_output_statement, root_node_statement])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_boolean_reg_gclk():
    input_statement: RawSExprList = ['declare', 'p', ['not', ['reg-gclk', 'a', ['and', 'a', 'b']]]]
    expected_output_statement: RawSExprList = ['declare-rec', ['not_a', ['not', 'a']],
        ['declare', 'p', ['reg-gclk', 'not_a', ['or', 'not_a', ['not', 'b']]]]]
    root_node_statement: RawSExprList = ['parse-sexpr', 'p']

    input_document = wrap_multiple_statements_in_document([input_statement, root_node_statement])
    expected_output_document = wrap_multiple_statements_in_document([expected_output_statement, root_node_statement])
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
    input_statement_str1: str = """(declare p (prop-strong (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c)))))"""
    check_single_declaration_nnf_helper(input_statement_str1, input_statement_str1)

def test_nnf_sequence_weak_negative():
    input_statement_str1: str = """(declare p (prop-not (prop-weak (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c))))))"""
    output_statement_str1: str = """(declare p (prop-refuted (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c)))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_sequence_strong_negative():
    input_statement_str1: str = """(declare p (prop-not (prop-strong (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c))))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-implication (seq-concat (seq-or (seq-bool a) (seq-bool b)) (seq-repeat (range 2 3) (seq-bool c))) (prop-weak-bool (constant false)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_boolean_weak1():
    input_statement_str1: str = """(declare p (prop-not (prop-weak-bool a)))"""
    output_statement_str1: str = """(declare p (prop-strong-bool (not a)))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_boolean_weak2():
    input_statement_str1: str = """(declare p (prop-not (prop-weak (seq-bool a))))"""
    output_statement_str1: str = """(declare p (prop-refuted (seq-bool a) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_sequence_weak_with_label_single_root():
    input_statement_str1: str = """(declare p (prop-weak (seq-bool a)))"""
    input_statement_str2: str = """(declare q (prop-not p))"""
    output_statement_str1: str = """(declare q (prop-refuted (seq-bool a)))"""
    output_statement_str2: str = """(declare p_neg q)"""
    input_statement1 = parse_raw_sexpr(input_statement_str1)
    input_statement2 = parse_raw_sexpr(input_statement_str2)
    output_statement1 = parse_raw_sexpr(output_statement_str1)
    output_statement2 = parse_raw_sexpr(output_statement_str2)
    root_statement1: RawSExprList = ['parse-sexpr', 'q']
    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, input_statement2, root_statement1])
    expected_output_document: RawSExprList = wrap_multiple_statements_in_document([output_statement1, output_statement2, root_statement1])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_sequence_weak_with_label_two_roots():
    input_statement_str1: str = """(declare p (prop-weak (seq-bool a)))"""
    input_statement_str2: str = """(declare q (prop-not p))"""
    output_statement_str: str = """(declare-rec
            (s_bool_a (seq-bool a))
            (declare p (prop-weak s_bool_a))
            (declare p_neg (prop-refuted s_bool_a))
            (declare q p_neg)
        )"""
    input_statement1 = parse_raw_sexpr(input_statement_str1)
    input_statement2 = parse_raw_sexpr(input_statement_str2)
    output_statement = parse_raw_sexpr(output_statement_str)
    root_statement1: RawSExprList = ['parse-sexpr', 'p']
    root_statement2: RawSExprList = ['parse-sexpr', 'q']
    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, input_statement2, root_statement1, root_statement2])
    expected_output_document: RawSExprList = wrap_multiple_statements_in_document([output_statement, root_statement1, root_statement2])
    check_nnf_equivalence(input_document, expected_output_document)

def test_nnf_sequence_strong():
    input_statement_str1: str = """(declare p (prop-not (prop-strong (seq-bool a))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-implication (seq-bool a) (prop-weak-bool (constant false))))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


# NNF properties single primitives

def test_nnf_property_reject_on():
    input_statement_str1: str = """(declare p (prop-not (prop-reject-on a (prop-weak-bool b))))"""
    output_statement_str1: str = """(declare p (prop-accept-on a (prop-strong-bool (not b)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_accept_on():
    input_statement_str1: str = """(declare p (prop-not (prop-accept-on a (prop-weak-bool b))))"""
    output_statement_str1: str = """(declare p (prop-reject-on a (prop-strong-bool (not b)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_implication():
    input_statement_str1: str = """(declare p (prop-not (prop-overlapped-implication (seq-bool a) (prop-weak-bool b))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-followed-by (seq-bool a) (prop-strong-bool (not b)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_followed_by():
    input_statement_str1: str = """(declare p (prop-not (prop-overlapped-followed-by (seq-bool a) (prop-strong-bool b))))"""
    output_statement_str1: str = """(declare p (prop-overlapped-implication (seq-bool a) (prop-weak-bool (not b)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_until():
    input_statement_str1: str = """(declare p (prop-not (prop-until (prop-weak-bool a) (prop-weak-bool b))))"""
    output_statement_str1: str = """(declare p (prop-strong-until-with (prop-strong-bool (not b)) (prop-strong-bool (not a)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_s_until_with():
    input_statement_str1: str = """(declare p (prop-not (prop-strong-until-with (prop-strong-bool a) (prop-strong-bool b)) ))"""
    output_statement_str1: str = """(declare p (prop-until (prop-weak-bool (not b)) (prop-weak-bool (not a)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_nexttime():
    input_statement_str1: str = """(declare p (prop-not (prop-nexttime 5 (prop-weak-bool a))))"""
    output_statement_str1: str = """(declare p (prop-strong-nexttime 5 (prop-strong-bool (not a)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_s_nexttime():
    input_statement_str1: str = """(declare p (prop-not (prop-strong-nexttime 5 (prop-strong-bool a))))"""
    output_statement_str1: str = """(declare p (prop-nexttime 5 (prop-weak-bool (not a)) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_or_and():
    input_statement_str1: str = """(declare p (prop-not (prop-and (prop-or (prop-weak-bool a) (prop-weak-bool b)) (prop-and (prop-weak-bool c) (prop-weak-bool d)) )))"""
    output_statement_str1: str = """(declare p (prop-or
        (prop-and (prop-strong-bool (not a)) (prop-strong-bool (not b)) )
        (prop-or (prop-strong-bool (not c)) (prop-strong-bool (not d)) ) ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)



# NNF properties larger examples

def test_nnf_property_unchanged_positive():
    input_statement1: RawSExprList = ['declare-rec',
                ['declare', 'prop1', ['prop-and',
                    ['prop-weak', ['seq-bool', 'a']],
                    ['prop-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop2']]],
                ['declare', 'prop2', ['prop-and',
                    ['prop-weak', ['seq-bool', 'a']],
                    ['prop-overlapped-implication', ['seq-bool', ['constant', 'true']], 'prop1']]],
                ]
    root_statement1: RawSExprList = ['parse-sexpr', 'prop1']
    root_statement2: RawSExprList = ['parse-sexpr', 'prop2']
    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, root_statement1, root_statement2])
    expected_output_document = wrap_multiple_statements_in_document([input_statement1, root_statement1, root_statement2])
    check_nnf_equivalence(input_document, expected_output_document)


def test_nnf_property_multiple_replacements():
    input_statement_str1: str = """(declare p
        (prop-not (prop-overlapped-implication
            (seq-bool a)
            (prop-until (prop-weak-bool b) (prop-not (prop-weak-bool c)) )
        )))"""
    output_statement_str1: str = """(declare p
        (prop-overlapped-followed-by
            (seq-bool a)
            (prop-strong-until-with (prop-weak-bool c) (prop-strong-bool (not b)) )
        ))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


def test_nnf_property_even_cycle():
    input_statement_str1: str = """(declare-rec (declare p
        (prop-not (prop-overlapped-implication
            (seq-concat (seq-bool a) (seq-bool (constant true)))
            (prop-not (prop-and (prop-weak-bool b) p))
        ))))"""
    output_statement_str1: str = """(declare-rec (declare p
        (prop-overlapped-followed-by
            (seq-concat (seq-bool a) (seq-bool (constant true)))
            (prop-and (prop-weak-bool b) p)
        )))"""
    check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)


def test_nnf_property_odd_cycle():
    with pytest.raises(ValueError, match='odd number of negations'):
        input_statement_str1: str = """(declare-rec (declare p
            (prop-not (prop-overlapped-implication
                (seq-concat (seq-bool a) (seq-bool (constant true)))
                (prop-and (prop-weak-bool b) p)
            ))))"""
        output_statement_str1: str = """(declare p (prop-weak-bool a))""" # arbitrary because an error is expected anyway
        check_single_declaration_nnf_helper(input_statement_str1, output_statement_str1)

def test_nnf_property_shared_subgraph():
    input_statement_str1: str = """(declare q (prop-not (prop-weak-bool c)))"""
    input_statement_str2: str = """(declare p
        (prop-not (prop-overlapped-implication
            (seq-bool a)
            (prop-until (prop-weak-bool b) q)
        )))"""
    input_statement1 = parse_raw_sexpr(input_statement_str1)
    input_statement2 = parse_raw_sexpr(input_statement_str2)

    output_statement_str0: str = """(declare q_neg (prop-weak-bool c))"""
    output_statement_str1: str = """(declare q (prop-strong-bool (not c)))"""
    output_statement_str2: str = """(declare p
        (prop-overlapped-followed-by
            (seq-bool a)
            (prop-strong-until-with q_neg (prop-strong-bool (not b)) )
        ))"""
    output_statement_str: str = '(declare-rec' + output_statement_str1 + output_statement_str0 + output_statement_str2 + ')'
    output_statement = parse_raw_sexpr(output_statement_str)

    root_statement1: RawSExprList = ['parse-sexpr', 'q']
    root_statement2: RawSExprList = ['parse-sexpr', 'p']

    input_document: RawSExprList = wrap_multiple_statements_in_document([input_statement1, input_statement2, root_statement1, root_statement2])
    expected_output_document = wrap_multiple_statements_in_document([output_statement, root_statement1, root_statement2])
    check_nnf_equivalence(input_document, expected_output_document)



def check_nnf_random_property_evaluation(doc_and_trace: tuple[str, Trace], visualize=False):

    doc: str = doc_and_trace[0]
    trace: Trace = doc_and_trace[1]

    bool_results1: BoolMemoDict = {}
    seq_results1: SequenceMemoDict = {}
    prop_results1: PropertyMemoDict = {}

    bool_results2: BoolMemoDict = {}
    seq_results2: SequenceMemoDict = {}
    prop_results2: PropertyMemoDict = {}

    input_container: IrContainer = IrContainer()
    parse_document(parse_raw_sexpr(doc), input_container)

    root_node_id1: NodeId = input_container.get_sink_nodes()[0]
    result1: MaybeBool = evaluate_property(root_node_id1, input_container, trace, bool_results1, seq_results1, prop_results1)

    output_container: IrContainer = nnf(container=input_container)

    root_node_id2: NodeId = output_container.get_sink_nodes()[0]
    result2: MaybeBool = evaluate_property(root_node_id2, output_container, trace, bool_results2, seq_results2, prop_results2)

    logger.debug('input_doc: %s', doc)
    logger.debug('output_doc: %s', unparse_raw_sexpr(output_container.output_container()))
    logger.debug('trace: %s', trace)
    logger.debug('result1: %s', result1)
    logger.debug('result2: %s', result2)

    if visualize:
        output_directory: Path = Path('./output')
        input_container.bypass_placeholders()
        output_container.bypass_placeholders()
        input_container.show_graph(output_directory / 'nnf_input.png')
        output_container.show_graph(output_directory / 'nnf_output.png')

    assert result1 == result2 or result1 == 'unknown' or result2 == 'unknown'



@settings(max_examples=100, deadline=500)
@given(random_ir_with_trace_simple(final_node_type=PropNot,
    primitive_filter=lambda node_type:
        not issubclass(node_type, (Xor, Ite, Eq, ChangingGclk, RisingGclk, FallingGclk, PropRefuted)),
    trace_min_length=0))
@example(("""(document (declare-input 0)
    (parse-sexpr (let-rec
        (step0 (future-gclk (true)))
        (step1 (prop-weak-bool step0))
        (step2 (prop-not step1)) step2)))""",
     Trace(finite_part=(frozenset(),), suffix='top_omega')))
@example((
"""(document (declare-input 0) (declare-input 00)
    (parse-sexpr (let-rec
        (step0 (prop-until (prop-weak-bool 0) (prop-weak-bool 00)))
        (step1 (prop-not step0))
        (step2 (prop-not step1)) step2)))""",
    Trace(finite_part=(frozenset({'00'}), frozenset()), suffix='end')))
def test_nnf_random_property_evaluation_with_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_nnf_random_property_evaluation(doc_and_trace, visualize=False)

@settings(max_examples=100, deadline=500)
@given(random_ir_with_trace_simple(final_node_type=PropNot,
    primitive_filter=lambda node_type:
        not issubclass(node_type, (Xor, Ite, Eq, ChangingGclk, RisingGclk, FallingGclk, PropRefuted)),
    trace_min_length=5))
def test_nnf_random_property_evaluation_no_empty_trace(doc_and_trace: tuple[str, Trace]):
    check_nnf_random_property_evaluation(doc_and_trace)
