from __future__ import annotations
from typing import Optional, Any, TypeAliasType,get_origin, get_args, Literal
from typeguard import typechecked
import re
import logging

from .base import RawSExpr, RawSExprList, LiteralType, NodeId
from .base import IrContainer, PropertyIrNode, PlaceholderNode
from .base import Bool, Sequence, Property
from .base import Range, BoundedRange, IntOrUnbounded
from .base import UnnamedExpressionDeclaration, NamedExpressionDeclaration, SignalDeclaration, NamedRecursiveDeclaration
from .primitives import *


logger = logging.getLogger(__name__)


@typechecked
def get_op_symbols() -> dict[str, type[PropertyIrNode]]:
    allowed_types = [Bool, Sequence, Property]
    ops_to_cls: dict[str, type[PropertyIrNode]] = dict()

    for node_type in allowed_types:
        for cls in node_type.__subclasses__():
            ops_to_cls[cls.op_symbol()] = cls

    return ops_to_cls


op_to_cls: dict[str, type[PropertyIrNode]] = get_op_symbols()


@typechecked
def parse_raw_sexpr(expr: str) -> RawSExprList:
    """Converts the s-expression given as a str to a nested list whose base
    elements are either str or int (int used only for integers, not for
    booleans)."""

    logger.debug(expr)

    tokens: list[str] = re.split(r'[\s]+|(?=[()])|(?<=[()])', expr)
    tokens = [t for t in tokens if t != '']
    if tokens.pop(0) != '(':
            raise ValueError(f"Expression not starting with '('")
    if tokens.pop() != ')':
            raise ValueError(f"Expression not ending in ')'")

    logger.debug(tokens)

    current_list: RawSExprList = []
    stack: list[RawSExprList] = []

    for t in tokens:
        if re.fullmatch(r'[a-zA-Z0-9\-\$]+', t):
            current_list.append(t)
        elif t == "(":
            stack.append(current_list)
            current_list = []
        elif t == ")":
            finished_list = current_list
            if len(stack) == 0:
                raise ValueError(f"Trying to pop from empty stack. Missing '('?")
            current_list = stack.pop()
            current_list.append(finished_list)
        else:
            raise ValueError(f"Unexpected token {t}")

    if len(stack) != 0:
            raise ValueError(f"Unexpected end of expression with stack {stack}. Missing ')'?")

    logger.debug(current_list)

    return current_list


def unparse_raw_sexpr(sexpr: RawSExpr) -> str:

    if isinstance(sexpr, str):
        return sexpr

    elif isinstance(sexpr, list):
        return '(' + ' '.join([unparse_raw_sexpr(subexpr) for subexpr in sexpr]) +')'

    raise TypeError('Unexpected element in RawSExpr {sexpr}')



def parse_range(range_expr: RawSExprList) -> Range | BoundedRange:

    match range_expr:

        case ['bounded-range', str(lower_bound), str(upper_bound)] if str.isnumeric(lower_bound) and str.isnumeric(upper_bound):
            if int(lower_bound) > int(upper_bound):
                raise ValueError(f'Lower bound higher than upper bound in range expression {range_expr}')
            return BoundedRange(int(lower_bound), int(upper_bound))
        case ['range', str(lower_bound), str(upper_bound)] if str.isnumeric(lower_bound) and str.isnumeric(upper_bound):
            if int(lower_bound) > int(upper_bound):
                raise ValueError(f'Lower bound higher than upper bound in range expression {range_expr}')
            return Range(int(lower_bound), IntOrUnbounded(int(upper_bound)))
        case ['range', str(lower_bound), '$'] if str.isnumeric(lower_bound):
            return Range(int(lower_bound), IntOrUnbounded('$'))
        case _:
            raise ValueError(f'Unexpected range expression form {range_expr}')

def parse_bool(bool_literal: str) -> bool:
        if bool_literal == 'true':
            return True
        elif bool_literal == 'false':
            return False
        else:
            raise TypeError(f'Mismatch of expected type bool constant and {bool_literal}')

def parse_int(int_literal: str) -> int | Literal['$']:
    if str.isnumeric(int_literal):
        return(int(int_literal))
    elif int_literal == '$':
        return '$'
    else:
        raise TypeError(f"Mismatch of expected type int or '$' and {int_literal}")


def parse_literal(literal_expr: RawSExpr, expected_type: type) -> LiteralType:

    if issubclass(expected_type, bool) and isinstance(literal_expr, str):
        return parse_bool(literal_expr)

    elif issubclass(expected_type, Range | BoundedRange) and isinstance(literal_expr, list):
        parsed_range = parse_range(literal_expr)
        if not isinstance(parsed_range, expected_type):
            raise TypeError(f'Mismatch of expected type {expected_type} and {parsed_range}')
        return parsed_range

    elif issubclass(expected_type, int)  and isinstance(literal_expr, str):
        parsed_int = parse_int(literal_expr)
        if parsed_int == '$':
            raise TypeError(f"Mismatch of expected type int and '$'")
        else:
            return parsed_int

    elif issubclass(expected_type, IntOrUnbounded) and isinstance(literal_expr, str):
        parsed_int = parse_int(literal_expr)
        return IntOrUnbounded(parsed_int)

    raise TypeError(f'Mismatch of expected type literal {expected_type} and expression {literal_expr}')


def check_names_sexpr(expr: RawSExprList) -> list[tuple[str, RawSExpr]]:
    named_subexpressions: list[tuple[str, RawSExpr]] = list()
    if not isinstance(expr, list):
        raise ValueError(f"Expected list of named expressions instead of {expr}")
    for item in expr:
        match item:
            case [str(first), second]:
                named_subexpressions.append((first, second))
            case _:
                raise ValueError(f"Expected (name expression) pair instead of {item}")
    return named_subexpressions


@typechecked
def process_named_subexpressions(local_nodes: dict[str, NodeId], named_subexpressions, ir_container: IrContainer) -> dict[str, NodeId]:
    """Parse a list of possibly mutually recursive expressions of the form
    (name expression) as it occurs in let-rec and declare-rec.
    This method exists to deduplicate the common code of parsing these two.
    local_nodes contains the already defined names (globally and locally earlier
    in a surrounding expression). Returns a dict of newly defined (local) node names.
    (Some of the new node names might be global, but this information is not available here,
    and the global names are updated later via add_declaration in parse_document.)
    """

    inner_local_nodes: dict[str, NodeId] = dict(local_nodes)

    # create a placeholder node for each new node name
    for (name, subexpr) in named_subexpressions:
        node_name = ir_container.uniquify(name) # returns name if not used otherwise returns f"{name}_{counter}" for a counter value that results in an unused name
        if name in inner_local_nodes:
            raise ValueError(f'Node name {name} already in use')
        inner_local_nodes[name] = ir_container.add_placeholder_node(name=node_name).node_id

    # evaluate each named subexpression
    # and let each placeholder point to the root of its subexpression
    # or if the root is a placeholder, merge placeholders
    for (name, subexpr) in named_subexpressions:
        subexpr_root_node_id = parse_expression(subexpr, None, inner_local_nodes, ir_container)
        assert isinstance(subexpr_root_node_id, NodeId)
        subexpr_root_node: PropertyIrNode = ir_container[subexpr_root_node_id]
        placeholder_id: NodeId = inner_local_nodes[name]
        placeholder_node = ir_container[placeholder_id]
        assert isinstance(placeholder_node, PlaceholderNode)

        placeholder_node.instantiate_placeholder(subexpr_root_node)

    for (name, subexpr) in named_subexpressions:
        subexpr_id: NodeId = inner_local_nodes[name]
        subexpr_node = ir_container[subexpr_id]
        if isinstance(subexpr_node, PlaceholderNode):
            raise ValueError(f'Subexpression ({name} {subexpr}) in let-rec expression corresponds to uninstantiated node')
    return inner_local_nodes


@typechecked
def parse_expression(
    expr: RawSExpr,
    expected_type: Optional[type[PropertyIrNode]],
    local_nodes: dict[str, NodeId],
    ir_container: IrContainer) -> NodeId:

    logger.info(f"start with {expr}")
    logger.info(f"expecting type {expected_type}")

    match expr:

        case str(name):

            if name in local_nodes:
                if expected_type is not None:
                    ir_container[local_nodes[name]].check_type(expected_type)
                return local_nodes[name]
            else:
                raise ValueError(f'Unexpected symbol {name}')


        case ['let-rec', *named_subexpressions, return_expression]:

            checked_named_subexpressions: list[tuple[str, RawSExpr]] = check_names_sexpr(named_subexpressions)

            inner_local_nodes: dict[str, NodeId] = process_named_subexpressions(local_nodes, checked_named_subexpressions, ir_container)

            return parse_expression(return_expression, None, inner_local_nodes, ir_container)

        case ["true" | "false" as root_symbol]: # "(false)" "(true)"
            return parse_expression(["constant", root_symbol], expected_type, local_nodes, ir_container)


        case [str(root_symbol), *args]:

            if root_symbol in op_to_cls:

                root_class: type = op_to_cls[root_symbol]
                root_signature = root_class.signature()

                if expected_type:
                    if op_to_cls[root_symbol].type_class() is not expected_type:
                        raise TypeError(f'Mismatch of expected type {expected_type} and operation "{root_symbol}" with type {op_to_cls[root_symbol].type_class()} in {expr}')

                kwargs: dict[str, Any] = {}

                for (index, field) in enumerate(root_class.get_child_fields()):

                    field_type: type = root_signature[index]

                    if get_origin(field_type) is list:
                        list_elem_type: type = get_args(field_type)[0]
                        assert issubclass(list_elem_type, PropertyIrNode)
                        single_child_list = []

                        # this assumes that a list parameter is never combined with other parameters
                        # and always contains NodeIds (no literals allowed)
                        for child_expr in args:
                            child_node_id = parse_expression(child_expr, list_elem_type, local_nodes, ir_container)
                            single_child_list.append(child_node_id)
                        kwargs[field.name] = single_child_list

                    elif issubclass(field_type, PropertyIrNode):
                        child_expr = args[index]
                        child_node_id = parse_expression(child_expr, field_type, local_nodes, ir_container)
                        kwargs[field.name] = child_node_id

                    elif issubclass(field_type, LiteralType.__value__):
                        child_expr = args[index]
                        parsed_literal = parse_literal(child_expr, field_type)
                        kwargs[field.name] = parsed_literal


                root_node: PropertyIrNode = ir_container.add_node_by_kwargs(root_class, kwargs)

                logger.info(root_node)
                return root_node.node_id

            else: # if root_symbol not in op_to_cls
                raise ValueError(f'Unexpected operation {root_symbol} in {expr}')

        case _:
            raise ValueError(f'Unexpected expression form {expr}')


@typechecked
def parse_declare_rec(expression_list: list[RawSExprList], ir_container: IrContainer) -> dict[str, NodeId]:
    """Parses a declare-rec expression, adds its nodes to the given ir_container,
    and returns a dict of new global nodes that are specified with the declare keyword within the expression.
    This method is separate from parse_expression because not only a single NodeId is returned.
    """

    local_nodes = ir_container.global_nodes

    new_global_names = []
    new_global_nodes: dict[str, NodeId] = dict()

    named_subexpressions: list[tuple[str, RawSExpr]] = list()

    # collect all named expressions and keep track of new global names
    for expr in expression_list:
        match(expr):
            case [str(name), list(subexpr)] | [str(name), str(subexpr)]:
                named_subexpressions.append((name, subexpr))
            case ['declare', str(name), list(subexpr)] | ['declare', str(name), str(subexpr)]:
                named_subexpressions.append((name, subexpr))
                new_global_names.append(name)
            case _:
                raise ValueError(f"Expected (name expression) or (declare name expression) in let-rec instead of {expr}")

    inner_local_nodes: dict[str, NodeId] = process_named_subexpressions(local_nodes, named_subexpressions, ir_container)

    # collect all global nodes specified with declare to return
    for name in new_global_names:
        new_global_nodes[name] = inner_local_nodes[name]

    return new_global_nodes


@typechecked
def parse_document(document: RawSExprList, ir_container: IrContainer):
    """Parses a document of property IR statements and adds it to the given ir_container.
    Adds declarations to the container (which in turn updates the global nodes).
    """

    match(document):
        case ['document', *statements]:

            for statement in statements:

                match(statement):

                    case ['add-signals', *signal_list]:
                        for signal_name in signal_list:
                            if not isinstance(signal_name, str):
                                raise ValueError(f"Expected signal name instead of {signal_name} in statement {statement}")
                            signal_node = ir_container.add_signal_node(signal_name)
                            ir_container.add_declaration(SignalDeclaration(signal_name, signal_node.node_id))

                    case ['parse-sexpr', list(expression)] | ['parse-sexpr', str(expression)]:
                        root_node_id = parse_expression(expr=expression, expected_type=None, local_nodes=ir_container.global_nodes, ir_container=ir_container)
                        ir_container.add_declaration(UnnamedExpressionDeclaration(root_node_id))

                    case ['declare', str(node_name), list(expression)] | ['declare', str(node_name), str(expression)]:
                        root_node_id = parse_expression(expr=expression, expected_type=None, local_nodes=ir_container.global_nodes, ir_container=ir_container)
                        ir_container.add_declaration(NamedExpressionDeclaration(node_name, root_node_id))

                    case ['declare-rec', *expression_list]:
                        root_nodes_dict = parse_declare_rec(expression_list, ir_container) # type:ignore # TODO can this be typechecked?
                        ir_container.add_declaration(NamedRecursiveDeclaration(root_nodes_dict))

                    case _:
                        raise ValueError(f'Unexpected statement form {statement}')

        case _:
            raise ValueError(f'Unexpected document form {document}')



