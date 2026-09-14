import logging

from hypothesis import Verbosity, given, settings
from ir.automata import prepare_container_for_automaton_translation, simple_to_automaton
from ir.base import AssertProperty, IrContainer, Property, RawSExprList
from ir.parsing import parse_document, parse_raw_sexpr
from ir.primitives.simple_primitives import PropNot, PropRefuted

from tests.strategies import random_ir_simple

logger = logging.getLogger(__name__)

def check_simple_to_automaton_no_error(doc):
    doc_raw_sexpr: RawSExprList = parse_raw_sexpr(doc)
    container1: IrContainer = IrContainer()
    parse_document(doc_raw_sexpr, container1)

    logger.info(doc)
    logger.info(doc_raw_sexpr)

    prepare_container_for_automaton_translation(container1)

    container2 = simple_to_automaton(container1)

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)


@settings(verbosity=Verbosity.verbose, max_examples=50, deadline=500)
@given(random_ir_simple(
    final_node_type=Property,
    directive=AssertProperty,
    primitive_filter = lambda node_type: not issubclass(node_type, (PropNot, PropRefuted))))
def test_simple_to_automaton_random_no_error(doc):
    check_simple_to_automaton_no_error(doc)
