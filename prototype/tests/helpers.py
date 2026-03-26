import logging

from sexpr import RawSExprList
from sexpr import parse_document, IrContainer


logger = logging.getLogger(__name__)

document_beginning: RawSExprList = ['document',
        ['declare-input', 'a'],
        ['declare-input', 'b'],
        ['declare-input', 'c'],
        ['declare-input', 'd']]

def wrap_in_document(expr: RawSExprList) -> RawSExprList:
    return document_beginning + [['parse-sexpr', expr]]

def wrap_multiple_expr_in_document(expr_list: list[RawSExprList]) -> RawSExprList:
    return document_beginning + [['parse-sexpr', expr] for expr in expr_list]


def wrap_statement_in_document(expr: RawSExprList) -> RawSExprList:
    return document_beginning + [expr]

def wrap_multiple_statements_in_document(expr_list: list[RawSExprList]) -> RawSExprList:
    return document_beginning + expr_list

def wrap_signals_and_expr_in_document(signals: list[str], expr: RawSExprList) -> RawSExprList:
    signal_list: RawSExprList = [['declare-input', signal] for signal in signals]
    return ['document'] + signal_list + [['parse-sexpr', expr]]


def apply_roundtrip(document: RawSExprList):
    logger.info('TESTING %s', document)
    container1 = IrContainer()
    parse_document(document, ir_container=container1)
    output_document = container1.output_container()
    logger.info(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2