from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Literal, List, Optional, Any, Set, Dict, get_origin, get_args, Tuple, Union
from typeguard import typechecked
import re



Uninitialized = Literal['uninitialized']

type NodeId = int

class UnionFind[T]:
    ...

class IrContainer:
    nodes: dict[NodeId, PropertyIrNode]

    node_names: dict[NodeId, str]
    next_node_id: int

    merged_nodes: UnionFind[int]

    def __getitem__(self, node_id: int):
        node_id = self.merged_nodes.find_representative(node_id)
        ...

class PropertyIrNode(ABC):
    ir_container: IrContainer
    node_id: NodeId
    @abstractmethod
    def __init__(self):
        pass

    def sort(self) -> type[PropertyIrNode]:
        return type(self)

    def check_sort(self, sort: type[PropertyIrNode]):
        if not isinstance(self, sort):
            raise TypeError("...")

    def bypass_placeholders(self):
        raise NotImplementedError("todo...")

class PlaceholderNode(PropertyIrNode):
    replace_with: PropertyIrNode | None
    expected_sort: type[PropertyIrNode] | None

    def sort(self) -> type[PropertyIrNode]:
        if self.expected_sort is None:
            raise ValueError("...")
        else:
            return self.expected_sort

    def check_sort(self, sort: type[PropertyIrNode]):
        if self.expected_sort is None:
            self.expected_sort = sort
        elif not issubclass(self.expected_sort, sort):
            raise TypeError("...")

    def instantiate_placeholder(self, node: PropertyIrNode):
        self.check_sort(type(node))
        self.replace_with = node





class Bool(PropertyIrNode):
    @abstractmethod
    def __init__(self):
        pass

class Sequence(PropertyIrNode):
    @abstractmethod
    def __init__(self):
        pass

class Property(PropertyIrNode):
    @abstractmethod
    def __init__(self):
        pass



@typechecked
@dataclass
class Int(PropertyIrNode):
    value: int


@typechecked
@dataclass
class IntOrInf(PropertyIrNode):
    value: int | Literal['$']

type IntOrUnbounded = int | Literal['$']


@typechecked
@dataclass
class Range:
    lower_bound: int
    upper_bound: IntOrUnbounded

@typechecked
@dataclass
class BoundedRange(Range):
    lower_bound: int
    upper_bound: int # type: ignore




@typechecked
@dataclass
class Not(Bool):
    child: NodeId

@typechecked
@dataclass
class And(Bool):
    children: List[Bool]

@typechecked
@dataclass
class Or(Bool):
    children: List[Bool]

# not an operation
@typechecked
@dataclass
class Signal(Bool):
    signal_name: str

# not an operation
@typechecked
@dataclass
class Constant(Bool):
    value: bool






@typechecked
@dataclass
class SeqConcat(Sequence):
    children: List[Sequence]

@typechecked
@dataclass
class SeqBool(Sequence):
    child: Bool

@typechecked
@dataclass
class SeqRepeat(Sequence):
    child1: Range
    child2: Sequence





@typechecked
@dataclass
class PropAlways(Property):
    child: Property | Uninitialized


@typechecked
@dataclass
class PropAlwaysRanged(Property):
    child1: Range | Uninitialized
    child2: Property | Uninitialized

@typechecked
@dataclass
class PropAnd(Property):
    children: List[Property] | Uninitialized

@typechecked
@dataclass
class PropSeq(Property):
    child: Sequence | Uninitialized

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: Sequence | Uninitialized
    child2: Property | Uninitialized




def operation_to_class_str(input: str) -> str:
    splitted: List[str] = input.split('-')
    capitalized : List[str] = [str.capitalize(s) for s in splitted]
    return(''.join(capitalized))


def class_to_operation_str(input: str) -> str:
    splitted: List[str] = re.split(r'(?=[A-Z])', input)
    lowercase: List[str] = [str.lower(s) for s in splitted if s != '']
    return('-'.join(lowercase))


@typechecked
def get_op_symbols() -> Tuple[Dict[str, type], Dict[str, type]]:
    allowed_sorts = [Bool, Sequence, Property]
    ops_to_cls: Dict[str, type] = dict()
    ops_to_sort: Dict[str, type] = dict()
    
    for sort in allowed_sorts:
        for cls in sort.__subclasses__():
            if cls not in [Constant, Signal]:
                ops_to_cls[class_to_operation_str(cls.__name__)] = cls
                ops_to_sort[class_to_operation_str(cls.__name__)] = sort
    
    ops_to_cls['range'] = Range
    ops_to_sort['range'] = Range

    return ops_to_cls, ops_to_sort


op_to_cls: Dict[str, type]
op_to_sort: Dict[str, type]

op_to_cls, op_to_sort = get_op_symbols()


print(op_to_cls)
print(op_to_sort)




type RawSExpr = list[str | int | RawSExpr]

@typechecked
def expr_to_list(expr: str) -> List[Any]:

    print(expr)

    tokens: List[str] = re.split(r'[\s]+|(?=[()])|(?<=[()])', expr)
    tokens = [t for t in tokens if t != '']
    if tokens.pop(0) != '(':
            raise ValueError(f"Expression not starting with '('")
    if tokens.pop() != ')':
            raise ValueError(f"Expression not ending in ')'")

    print(tokens)

    current_list: List[Any] = []
    stack: List[Any] = []
    
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




@typechecked
def parse_expression(
    expr: List[Any] | str | int,
    expected_sort: Optional[type],
    signals: Dict[str, Signal],
    node_refs: Dict[str, PropertyIrNode],
    node_refs_sorts: Dict[str, type],
    root_node_ref: Optional[PropertyIrNode] = None) -> PropertyIrNode:

    print(f"start with {expr}")

    match expr:
        case str(name):
            ...
        case int(literal):
            ...
        case ['let-rec', *args]:
            ...
        case [str(operation), *args]:
            ...
                

    if isinstance(expr, str) or isinstance(expr, int):
        if expr in signals:
            if not expected_sort is Bool:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and {expr} with sort {Bool} in {expr}')
            return signals[expr]
        elif expr in node_refs:
            return node_refs[expr]
        elif expr in ['true', 'false']:
            if not expected_sort is Bool:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and {expr} with sort {Bool} in {expr}')
            return Constant(expr)
        elif expr == '$':
            if not expected_sort is IntOrInf:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and {expr} with sort {IntOrInf} in {expr}')
            return IntOrInf('$')
        elif type(expr) is int:
            if not (expected_sort is Int or expected_sort is IntOrInf):
                raise TypeError(f'Mismatch of expected sort {expected_sort} and {expr} with sort {type(expr)} in {expr}')
            return Int(expr)
        else:
            raise ValueError(f'Unexpected symbol {expr}')

    elif len(expr) <= 0:
        raise ValueError('Expression must not contain empty or singleton list')

    root_symbol: str = expr.pop(0)

    # check if root symbol has correct sort
    # assuming that the expected sort is unambigious (Uninitialized already removed and no Union/List allowed)
    if root_symbol in op_to_cls:

        root_class: type = op_to_cls[root_symbol]

        if not root_node_ref is None:
            if not type(root_node_ref) is root_class:
                raise TypeError(f'Mismatch of expected operation {type(root_node_ref)} and actual operation {root_class} at {expr}')

        if expected_sort:
            if not op_to_sort[root_symbol] is expected_sort:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and operation "{root_symbol}" with sort {op_to_sort[root_symbol]} at {expr}')

        '''

        (letrec
            (foo (and a bar)) ; remembers that the expected type of bar (currently a placeholder) is now a bool
            (bar (or b c)) ; when instantiating the placeholder for bar with the or node, the remembered expected type is checked against the type of or

            (foo2 (and a bar2))
            (bar2 (seq-concat ...)) ; instantiating bar2's placeholder will produce a type error here
        )

        '''


        children: List[Any] = []

        for field in fields(root_class):

            # remove Uninitialized case from expected child sort
            # this assumes that the child sort is never the Union of several sorts (only Union with Uninitialized)
            child_expected_sort: type
            if get_origin(field.type) is Union:
                child_expected_sort_union = get_args(field.type)
                without_uninit = [s for s in child_expected_sort_union if not s is Uninitialized]
                if (len(without_uninit) != 1):
                    raise TypeError(f'Operation {root_class} has parameter {field.name} with ambiguous sort {without_uninit}')
                child_expected_sort = without_uninit[0]
            else:
                child_expected_sort = field.type

            if get_origin(child_expected_sort) is list:
                list_elem_type: type = get_args(child_expected_sort)[0]
                single_child_list: List[list_elem_type] = []

                # this assumes that the children list comes as the last parameter of the root operation
                while len(expr) > 0:
                    child_expr = expr.pop(0)
                    child_node = parse_expression(child_expr, list_elem_type, signals, node_refs, node_refs_sorts)
                    single_child_list.append(child_node)
                children.append(single_child_list)

            else:
                child_expr = expr.pop(0)
                child_node = parse_expression(child_expr, child_expected_sort, signals, node_refs, node_refs_sorts)
                children.append(child_node)
        

        if root_node_ref is None:
            root_node = root_class(*children)
            print(root_node)
            return root_node
        else:
            for index, field in enumerate(fields(root_node_ref)):
                # set uninitialized children of the root node argument
                setattr(root_node_ref, field.name, children[index])
            print(root_node_ref)
            return root_node_ref
            



    if root_symbol == 'let-rec':

        if len(expr) < 2:
            raise ValueError(f'let-rec requires at least 2 parameters, {len(expr)} given in {expr}')

        # get return value identifier
        return_value_id: str = expr.pop()

        new_node_ids = []

        # create nodes for identifiers
        for child_definition in expr:

            if len(child_definition) != 3:
                raise ValueError(f'let-rec requires a definition to consist of 3 parameters, {len(child_definition)} given in {child_definition}')

            child_id = child_definition[0]

            # check that none of the identifiers are already in use
            if child_id in node_refs or child_id in new_node_ids:
                raise ValueError(f'Identifier {child_id} already in use in {child_definition}')
            new_node_ids.append(child_id)

            child_operation = child_definition[1]
            child_expression = child_definition[2]

            child_class: type = op_to_cls[child_operation]
            child_sort: type = op_to_sort[child_operation]

            # restrict to only the sorts that can be cyclic
            # which at the moment are properties
            # add other sorts later (automata states and property variants)
            if not child_sort is Property:
                raise TypeError(f'let-rec with forbidden sort {child_sort} in {child_definition}')

            # set sort dict for identifiers
            node_refs_sorts[child_id] = child_sort

            # set dict with uninitialized nodes
            child_param_num = len(fields(child_class))
            node_refs[child_id] = child_class(*['uninitialized' for i in range(child_param_num)])

        # check that the return value identifier is one of the defined ones
        if not return_value_id in new_node_ids:
            raise ValueError(f'let-rec return value identifier {return_value_id} not among the previously defined identifiers {new_node_ids}')

        # recursion for defined subexpressions
        for [child_id, child_operation, child_expression] in expr:
            
            # usually the recursive call would create a new node for the root operation
            # but we already create that node earlier
            # give the root node object as an additional optional parameter
            # the uninitialized children of the root node object are set in the subcall
            parse_expression(child_expression, node_refs_sorts[child_id], signals, node_refs, node_refs_sorts, node_refs[child_id])

        # return value of return value identifier
        return node_refs[return_value_id]







def print_expression(root: PropertyIrNode) -> str:
    pass



def get_sort(expr: str) -> type:
    pass



def main():

    test_expr1 = '(or (and a b) (not (and (not a) c)) d)'

    test_expr2 = """(seq-concat
                        (seq-repeat (range 5 5) (seq-bool a))
                        (seq-concat (seq-bool b) (seq-bool c)))"""
    
    test_expr3 = """(prop-always-ranged
                        (range 4 $)
                        (prop-seq (seq-bool (not b))))"""

    test_expr4 = """(prop-always (prop-and
                        (prop-seq (seq-bool (not b)))
                        (prop-seq (seq-bool a))
                    ))"""

    # give not sort but root operation of each named subexpression as a parameter
    # to be able to immediately create the correct node
    # in case the expression again starts with let-rec
    test_expr5 = """(let-rec
                        (prop1 prop-and (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool true) prop2)))
                        (prop2 prop-and (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool true) prop1)))
                        prop1)"""

    signal_dict = {'a': Signal('a'), 'b': Signal('b'), 'c': Signal('c'), 'd': Signal('d')}


    expr_list1: List[Any] = expr_to_list(test_expr1)
    print()
    expr_list2: List[Any] = expr_to_list(test_expr2)
    print()
    expr_list3: List[Any] = expr_to_list(test_expr3)
    print()
    expr_list4: List[Any] = expr_to_list(test_expr4)
    print()
    expr_list5: List[Any] = expr_to_list(test_expr5)
    print()
 
    parse_expression(expr_list1, None, signal_dict, dict(), dict())
    print()
    parse_expression(expr_list2, None, signal_dict, dict(), dict())
    print()
    parse_expression(expr_list3, None, signal_dict, dict(), dict())
    print()
    parse_expression(expr_list4, None, signal_dict, dict(), dict())
    print()
    parse_expression(expr_list5, None, signal_dict, dict(), dict())



if __name__ == "__main__":

    main()
