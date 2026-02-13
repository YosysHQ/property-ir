from hypothesis import given, settings, Verbosity, example

from sexpr import parse_expression, parse_literal, parse_raw_sexpr, RawSExprList, IrContainer, Signal, parse_document
from tests.helpers import wrap_in_document, wrap_multiple_expr_in_document, wrap_statement_in_document, wrap_multiple_statements_in_document
from tests.strategies import parsable_document, parsable_boolean_document, parsable_sequence_document, parsable_property_document


@settings(verbosity=Verbosity.verbose, max_examples=20)
@example(['document', ['add-signals', '0'], ['parse-sexpr', '0']])
@given(parsable_boolean_document())
def test_roundtrip_unnamed_expr_random_boolean(doc):
    print(f'TESTING {doc}')
    container1 = IrContainer()
    parse_document(doc, ir_container=container1)
    output_document = container1.output_container()
    print(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2

@settings(verbosity=Verbosity.verbose, max_examples=20)
@given(parsable_sequence_document())
def test_roundtrip_unnamed_expr_random_sequence(doc):
    print(f'TESTING {doc}')
    container1 = IrContainer()
    parse_document(doc, ir_container=container1)
    output_document = container1.output_container()
    print(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2


@settings(verbosity=Verbosity.verbose, max_examples=20)
@given(parsable_property_document())
def test_roundtrip_unnamed_expr_random_property(doc):
    print(f'TESTING {doc}')
    container1 = IrContainer()
    parse_document(doc, ir_container=container1)
    output_document = container1.output_container()
    print(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2