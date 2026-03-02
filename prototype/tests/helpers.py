from sexpr import RawSExprList
from sexpr import parse_document, IrContainer

def wrap_in_document(expr: RawSExprList) -> RawSExprList:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
        ['parse-sexpr', expr]
    ]

def wrap_multiple_expr_in_document(expr_list: list[RawSExprList]) -> RawSExprList:
    parse_expr_list = [['parse-sexpr', expr] for expr in expr_list]
    return ['document', ['add-signals', 'a', 'b', 'c', 'd']] + parse_expr_list


def wrap_statement_in_document(expr: RawSExprList) -> RawSExprList:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
        expr
    ]

def wrap_multiple_statements_in_document(expr_list: list[RawSExprList]) -> RawSExprList:
    return ['document',
        ['add-signals', 'a', 'b'],
        ['add-signals', 'c', 'd'],
    ] + expr_list


def apply_roundtrip(document: RawSExprList):
    print(f'TESTING {document}')
    container1 = IrContainer()
    parse_document(document, ir_container=container1)
    output_document = container1.output_container()
    print(output_document)
    container2 = IrContainer()
    parse_document(output_document, ir_container=container2)
    container1.canonical_id_renaming()
    container2.canonical_id_renaming()
    assert container1 == container2