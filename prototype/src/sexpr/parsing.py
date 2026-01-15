from __future__ import annotations
from typing import Optional, Any,get_origin, get_args
from typeguard import typechecked
import re

from .base import RawSExpr, LiteralType, NodeId
from .base import IrContainer, PropertyIrNode, PlaceholderNode
from .base import Bool, Sequence, Property
from .base import Int, Range, BoundedRange, IntOrUnbounded, Signal
from .primitives import *




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
def tokenize(expr: str) -> RawSExpr: # TODO rename to parse_raw_sexpr
    """Converts the s-expression given as a str to a nested list whose base
    elements are either str or int (int used only for integers, not for
    booleans)."""

    print(expr)

    tokens: list[str] = re.split(r'[\s]+|(?=[()])|(?<=[()])', expr)
    tokens = [t for t in tokens if t != '']
    if tokens.pop(0) != '(':
            raise ValueError(f"Expression not starting with '('")
    if tokens.pop() != ')':
            raise ValueError(f"Expression not ending in ')'")

    print(tokens)

    current_list: RawSExpr = []
    stack: list[RawSExpr] = []

    for t in tokens:
        if str.isnumeric(t):
            current_list.append(int(t))
        elif re.fullmatch(r'[a-zA-Z0-9\-\$]+', t):
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

    print(current_list)

    return current_list

def unparse_raw_sexpr(sexpr: RawSExpr) -> str:
    raise NotImplementedError # TODO implement me



def parse_range(range_expr: RawSExpr) -> Range | BoundedRange:

    match range_expr:

        case ['bounded-range', int(lower_bound), int(upper_bound)]:
            return BoundedRange(lower_bound, upper_bound)
        case ['range', int(lower_bound), int(upper_bound)]:
            return Range(lower_bound, IntOrUnbounded(upper_bound))
        case ['range', int(lower_bound), '$']:
            return Range(lower_bound, IntOrUnbounded('$'))
        case _:
            raise ValueError(f'Unexpected range expression form {range_expr}')

def parse_bool(bool_literal: str) -> bool:
        if bool_literal == 'true':
            return True
        elif bool_literal == 'false':
            return False
        else:
            raise TypeError('Expected bool constant instead of {bool_literal}')

def check_names_sexpr(expr: RawSExpr) -> list[tuple[str, RawSExpr]]:
    if not isinstance(expr, list):
        raise ValueError(f"Expected list of named expressions instead of {expr}")
    for item in expr:
        match item:
            case [str(_), _]:
                continue
            case _:
                raise ValueError(f"Expected (name expression) pair instead of {item}")
    return expr # type: ignore

@typechecked
def parse_expression(
    expr: RawSExpr | str | int,
    expected_type: Optional[type[PropertyIrNode]],
    local_nodes: dict[str, NodeId],
    ir_container: IrContainer) -> NodeId | LiteralType:

    print(f"start with {expr}")
    print(f"expecting type {expected_type}")

    match expr:

        case str(name):

            if name in local_nodes:
                if expected_type is not None:
                    ir_container[local_nodes[name]].check_type(expected_type)
                return local_nodes[name]
            #elif name in ['true', 'false']:  # sexpr: "true", "false"
            #    if not expected_type is Bool:
            #        raise TypeError(f'Mismatch of expected type {expected_type} and {name} with type {Bool} in {expr}')
            #    return Constant(expr == 'true')
            else:
                raise ValueError(f'Unexpected symbol {name}')

        case int(literal):

            if not (expected_type is Int or expected_type is IntOrUnbounded):
                raise TypeError(f'Mismatch of expected type {expected_type} and {literal} with type {type(literal)} in {expr}')
            return Int(literal)





        case ['let-rec', *named_subexpressions, return_expression]:

            named_subexpressions = check_names_sexpr(named_subexpressions)

            inner_local_nodes = dict(local_nodes)

            # create a placeholder node for each new node name
            for (name, subexpr) in named_subexpressions:
                node_name = ir_container.uniquify(name) # returns name if not used otherwise returns f"{name}_{counter}" for a counter value that results in an unused name
                if name in inner_local_nodes:
                    raise ValueError # TODO message
                inner_local_nodes[name] = ir_container.add_placeholder_node(name=node_name).node_id


            # evaluate each named subexpression
            # and let each placeholder point to the root of its subexpression
            # or if the root is a placeholder, merge placeholders
            for (name, subexpr) in named_subexpressions:
                subexpr_root_node_id = parse_expression(subexpr, None, inner_local_nodes, ir_container)
                assert isinstance(subexpr_root_node_id, NodeId) # TODO split parse_expression into sepate node / literal variant
                subexpr_root_node: PropertyIrNode = ir_container[subexpr_root_node_id]
                placeholder_id: NodeId = inner_local_nodes[name]
                placeholder_node = ir_container[placeholder_id]
                assert isinstance(placeholder_node, PlaceholderNode)

                placeholder_node.instantiate_placeholder(subexpr_root_node)

            for (name, subexpr) in named_subexpressions:
                subexpr_id: NodeId = inner_local_nodes[name]
                subexpr_node = ir_container[subexpr_id]
                if isinstance(subexpr_node, PlaceholderNode):
                    raise ValueError # TODO message


            # return value of last expression
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
                        for child_expr in args:
                            child_node = parse_expression(child_expr, list_elem_type, local_nodes, ir_container)
                            single_child_list.append(child_node)
                        kwargs[field.name] = single_child_list

                    elif issubclass(field_type, PropertyIrNode):
                        child_expr = args[index]
                        child_node = parse_expression(child_expr, field_type, local_nodes, ir_container)
                        kwargs[field.name] = child_node

                    elif issubclass(field_type, bool):
                        child_expr = args[index]
                        if isinstance(child_expr, str):
                            kwargs[field.name] = parse_bool(child_expr)
                        else:
                            raise TypeError(f'Expected string representation of bool instead of {child_expr} in {expr}')

                    elif issubclass(field_type, Range | BoundedRange):
                        child_expr = args[index]
                        if isinstance(child_expr, list):
                            parsed_range = parse_range(child_expr)
                        else:
                            raise TypeError(f'Expected range expression instead of {child_expr} in {expr}')
                        if not isinstance(parsed_range, field_type):
                            raise TypeError(f'Expected {field_type}, but received {parsed_range} in {expr}')
                        kwargs[field.name] = parsed_range


                root_node: PropertyIrNode = ir_container.add_node_by_kwargs(root_class, kwargs)

                print(root_node)
                return root_node.node_id

            else: # if root_symbol not in op_to_cls
                raise ValueError(f'Unexpected operation {root_symbol} in {expr}')

        case _:
            raise ValueError(f'Unexpected expression form {expr}')
