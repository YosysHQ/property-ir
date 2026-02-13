from sexpr import RawSExprList

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
