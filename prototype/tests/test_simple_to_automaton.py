import logging

from hypothesis import Verbosity, given, settings

from ir.automata import simple_to_automaton, split_seq_repeat
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

    split_seq_repeat(container1)

    container2 = simple_to_automaton(container1)

    container2.canonical_id_renaming(remove_unreachable_declared_nodes=True)


@settings(verbosity=Verbosity.verbose, max_examples=30, deadline=500)
@given(random_ir_simple(
    final_node_type=Property,
    directive=AssertProperty,
    primitive_filter = lambda node_type: not issubclass(PropNot, PropRefuted)))
def _test_simple_to_automaton_random_no_error(doc):
    check_simple_to_automaton_no_error(doc)
