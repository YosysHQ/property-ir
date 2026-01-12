from __future__ import annotations
from typing import Optional, Any,get_origin, get_args
from typeguard import typechecked
import re

from .base import RawSExpr, LiteralType, NodeId
from .base import IrContainer, PropertyIrNode, PlaceholderNode
from .base import Bool, Sequence, Property
from .base import Int, Range, BoundedRange, IntOrUnbounded, Constant, Signal
from .primitives import *



def class_to_operation_str(input: str) -> str:
    split: list[str] = re.split(r'(?=[A-Z])', input)
    lowercase: list[str] = [str.lower(s) for s in split if s != '']
    return('-'.join(lowercase))


@typechecked
def get_op_symbols() -> dict[str, type[PropertyIrNode]]:
    allowed_types = [Bool, Sequence, Property]
    ops_to_cls: dict[str, type[PropertyIrNode]] = dict()

    for node_type in allowed_types:
        for cls in node_type.__subclasses__():
            ops_to_cls[class_to_operation_str(cls.__name__)] = cls

    return ops_to_cls


op_to_cls: dict[str, type[PropertyIrNode]] = get_op_symbols()


@typechecked
def tokenize(expr: str) -> RawSExpr:
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
    expected_type: Optional[type],
    signals: dict[str, Signal],
    ir_container: IrContainer) -> NodeId | LiteralType:

    print(f"start with {expr}")
    print(f"expecting type {expected_type}")

    match expr:

        case str(name):

            if name in signals:
                if not expected_type is Bool:
                    raise TypeError(f'Mismatch of expected type {expected_type} and {name} with type {Bool} in {expr}')
                return signals[name]
            elif name in ['true', 'false']:
                if not expected_type is Bool:
                    raise TypeError(f'Mismatch of expected type {expected_type} and {name} with type {Bool} in {expr}')
                return Constant(expr == 'true')
            elif name in ir_container.node_names:
                named_node_id: NodeId = ir_container.get_node_id_by_name(name)
                named_node: PropertyIrNode = ir_container[named_node_id]
                if expected_type is not None:
                    if isinstance(named_node, PlaceholderNode):
                        named_node.check_type(expected_type)
                    elif not isinstance(named_node, expected_type):
                            raise TypeError(f'Mismatch of expected type {expected_type} and {name} with type {type(named_node)} in {expr}')
                return named_node_id
            else:
                raise ValueError(f'Unexpected symbol {name}')

        case int(literal):

            if not (expected_type is Int or expected_type is IntOrUnbounded):
                raise TypeError(f'Mismatch of expected type {expected_type} and {literal} with type {type(literal)} in {expr}')
            return Int(literal)

        case ['range', *args] | ['bounded-range', *args]:

            return parse_range(expr)




        case ['let-rec', *named_subexpressions, return_expression]:

            named_subexpressions = check_names_sexpr(named_subexpressions)

            # create a placeholder node for each new node name
            for (name, subexpr) in named_subexpressions:
                if name in ir_container.node_names:
                    raise ValueError(f'Node name {name} already exists in expression {expr}')
                ir_container.add_placeholder_node(name=name)

            # evaluate each named subexpression
            # and let each placeholder point to the root of its subexpression
            # or if the root is a placeholder, merge placeholders
            for (name, subexpr) in named_subexpressions:
                subexpr_root_node_id = parse_expression(subexpr, None, signals, ir_container)
                assert isinstance(subexpr_root_node_id, NodeId) # TODO split parse_expression into sepate node / literal variant
                subexpr_root_node: PropertyIrNode = ir_container[subexpr_root_node_id]
                placeholder_id: NodeId = ir_container.get_node_id_by_name(name)
                placeholder_node = ir_container[placeholder_id]
                assert isinstance(placeholder_node, PlaceholderNode)

                placeholder_node.instantiate_placeholder(subexpr_root_node)

            # return value of last expression
            return parse_expression(return_expression, None, signals, ir_container)




        case [str(root_symbol), *args]:

            if root_symbol in op_to_cls:

                root_class: type = op_to_cls[root_symbol]
                root_signature = root_class.signature()

                if expected_type:
                    if op_to_cls[root_symbol].type_class() is not expected_type:
                        raise TypeError(f'Mismatch of expected type {expected_type} and operation "{root_symbol}" with type {op_to_cls[root_symbol].type_class()} in {expr}')

                kwargs: dict[str, Any] = {}

                for (index, field) in enumerate(root_class.get_child_fields()):

                    child_expected_type: type = root_signature[index]

                    if get_origin(child_expected_type) is list:
                        list_elem_type: type = get_args(child_expected_type)[0]
                        single_child_list = []

                        # this assumes that a list parameter is never combined with other parameters
                        for child_expr in args:
                            child_node = parse_expression(child_expr, list_elem_type, signals, ir_container)
                            single_child_list.append(child_node)
                        kwargs[field.name] = single_child_list

                    else:
                        child_expr = args[index]
                        child_node = parse_expression(child_expr, child_expected_type, signals, ir_container)
                        kwargs[field.name] = child_node

                root_node: PropertyIrNode = ir_container.add_node_by_kwargs(root_class, kwargs)

                print(root_node)
                return root_node.node_id

            else: # if root_symbol not in op_to_cls
                raise ValueError(f'Unexpected operation {root_symbol} in {expr}')

        case _:
            raise ValueError(f'Unexpected expression form {expr}')
