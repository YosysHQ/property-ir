from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Literal, List, Optional, Any, Set, Dict, get_origin, get_args, Tuple, Union
from typeguard import typechecked
import re



Uninitialized = Literal["uninitialized"]



class PropertyIrNode(ABC):
    @abstractmethod
    def __init__(self):
        pass

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



@typechecked
@dataclass
class Range(PropertyIrNode):
    lower_bound: Int
    upper_bound: IntOrInf

@typechecked
@dataclass
class BoundedRange(Range):
    lower_bound: Int
    upper_bound: Int




@typechecked
@dataclass
class Not(Bool):
    child: Bool

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


op_symbol_tables = get_op_symbols()
op_to_cls: Dict[str, type] = op_symbol_tables[0]
op_to_sort: Dict[str, type] = op_symbol_tables[1]


print(op_to_cls)
print(op_to_sort)






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
def parse_expression(expr: List[Any] | str | int, expected_sort: Optional[type], signals: Dict[str, Signal], node_refs: Dict[str, PropertyIrNode]) -> PropertyIrNode:

    print(f"start with {expr}")

    if type(expr) is str or type(expr) is int:
                
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
    root_class: type = op_to_cls[root_symbol]

    print(root_symbol)
    print(root_class)

    # TODO: fix case Union of uninitialized and list
    if root_symbol in op_to_cls:
        if expected_sort:
            expected_sort_list = []
            if get_origin(expected_sort) is Union:
                expected_sort_list = get_args(expected_sort)
            else:
                expected_sort_list = [expected_sort]
            if not op_to_sort[root_symbol] in expected_sort_list:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and operation "{root_symbol}" with sort {op_to_sort[root_symbol]} in {expr}')

        children = []

        for field in fields(root_class):

            if get_origin(field.type) is list or get_args(field.type) is list:
                list_elem_type: type = get_args(field.type)[0]
                single_child_list = []

                # this assumes that the children list comes last
                while len(expr) > 0:
                    child_expr = expr.pop(0)
                    child_node = parse_expression(child_expr, list_elem_type, signals, node_refs)
                    single_child_list.append(child_node)
                children.append(single_child_list)

            else:
                child_expected_sort = field.type
                child_expr = expr.pop(0)
                child_node = parse_expression(child_expr, child_expected_sort, signals, node_refs)
                children.append(child_node)
        
        root_node = root_class(*children)

        print(root_node)
        return root_node



    if root_symbol == 'let-rec':
        pass
        # TODO expr with cycles











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

    test_expr5 = """(let-rec
                    (prop1 (prop-and
                        (prop-bool a)
                        (prop-non-overlapped-implication (seq-bool true) prop2)))
                    (prop2 (prop-and
                        (prop-bool b)
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
 
    parse_expression(expr_list1, None, signal_dict, dict())
    print()
    parse_expression(expr_list2, None, signal_dict, dict())
    print()
    parse_expression(expr_list3, None, signal_dict, dict())
    print()
    parse_expression(expr_list4, None, signal_dict, dict())
    print()
    #parse_expression(expr_list5, None, signal_dict, dict())



if __name__ == "__main__":

    main()
