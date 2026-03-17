from hypothesis import given, settings, Verbosity, example

from sexpr import parse_expression, parse_literal, parse_raw_sexpr, RawSExprList, IrContainer, Signal, parse_document
from tests.helpers import wrap_in_document, wrap_multiple_expr_in_document, wrap_statement_in_document, wrap_multiple_statements_in_document
from tests.helpers import apply_roundtrip
from tests.strategies import parsable_document, parsable_boolean_document, parsable_let_rec_boolean_document, parsable_sequence_document, parsable_property_document
from tests.strategies import parsable_let_rec_boolean_nested_document, parsable_declare_rec_boolean_document



@settings(verbosity=Verbosity.verbose, max_examples=20)
@example(['document', ['add-signals', '0'], ['parse-sexpr', '0']])
@given(parsable_boolean_document())
def test_roundtrip_unnamed_expr_random_boolean(doc):
    apply_roundtrip(doc)


@settings(verbosity=Verbosity.verbose, max_examples=20)
@given(parsable_sequence_document())
def test_roundtrip_unnamed_expr_random_sequence(doc):
    apply_roundtrip(doc)


@settings(verbosity=Verbosity.verbose, max_examples=20)
@given(parsable_property_document())
def test_roundtrip_unnamed_expr_random_property(doc):
    apply_roundtrip(doc)


@settings(verbosity=Verbosity.verbose, max_examples=20, deadline=3000)
@example(['document', ['add-signals', '1'], ['parse-sexpr', ['let-rec', ['0', '1'], ['00', '000'], ['000', '1'], '0']]])
@given(parsable_let_rec_boolean_document())
def test_roundtrip_unnamed_expr_random_let_rec_boolean(doc):
    apply_roundtrip(doc)


@settings(verbosity=Verbosity.verbose, max_examples=20, deadline=3000)
@given(parsable_let_rec_boolean_nested_document())
def test_roundtrip_unnamed_expr_random_let_rec_boolean_nested(doc):
    apply_roundtrip(doc)


@example(['document', ['add-signals', 'o'], ['declare-rec', ['declare', '3g', ['not', 'o']]], ['declare-rec', ['declare', '0', '3g']]])
@settings(verbosity=Verbosity.verbose, max_examples=30, deadline=3000)
@given(parsable_declare_rec_boolean_document())
def test_roundtrip_declare_rec_boolean(doc):
    apply_roundtrip(doc)
