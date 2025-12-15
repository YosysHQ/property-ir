from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Literal, List, Optional, Any, Set, Dict, get_origin, get_args
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
    child1: Optional[Range] | Uninitialized
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


def get_op_symbols() -> Dict[str, type]:
    allowed_sorts = [Bool, Sequence, Property]
    ops_to_cls: Dict[str, type] = dict()
    ops_to_sort: Dict[str, type] = dict()
    
    for sort in allowed_sorts:
        for cls in sort.__subclasses__():
            if cls not in [Constant, Signal]:
                ops_to_cls[class_to_operation_str(cls.__name__)] = cls
                ops_to_sort[class_to_operation_str(cls.__name__)] = sort

    return ops_to_cls, ops_to_sort


op_to_cls, op_to_sort = get_op_symbols()


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
def parse_expression(expr_list: List[Any], expected_sort: Optional[type], signals: Dict[str, Signal], node_refs: Dict[str, PropertyIrNode]) -> PropertyIrNode:

    #if expr_list is str or expr_list is int:

    if len(expr_list) == 0:
        raise ValueError('Expression must not contain empty list')

    root_symbol: str = expr_list[0]

    if len(expr_list) == 1:
        if root_symbol in signals:
            return signals[root_symbol]
        elif root_symbol in node_refs:
            return node_refs[root_symbol]
        elif type(root_symbol) is int:
            return Int(root_symbol)
        elif root_symbol == '$':
            return IntOrInf('$')
        else:
            raise ValueError(f'Unexpected symbol {root_symbol}')

    elif root_symbol in op_to_cls:
        if expected_sort:
            if expected_sort != op_to_sort[root_symbol]:
                raise TypeError(f'Mismatch of expected sort {expected_sort} and operation "{root_symbol}" in {expr_list}')
        root_class: type = op_to_cls[root_symbol]

        print(root_symbol)
        print(root_class)

        expr_list.pop(0) # remove op symbol

        children = []

        for field in fields(root_class):
            print(field)

            if get_origin(field.type) is list:
                list_elem_type: type = get_args(field.type)[0]
                print("LIST")
                print(list_elem_type)

                # this assumes that the children list comes last
                while len(expr_list) > 0:
                    child_expr = expr_list.pop(0)
                    print(child_expr)
                    child_node = parse_expression(child_expr, list_elem_type, signals, node_refs)
                    children.append(child_node)

            else:
                child_expected_sort = field.type
                child_expr = expr_list.pop(0)
                print(child_expr)
                child_node = parse_expression(child_expr, child_expected_sort, signals, node_refs)
                children.append(child_node)
        
        root_node = root_class(*children)

        return root_node





    if root_symbol == 'let-rec':
        pass









    pass


def print_expression(root: PropertyIrNode) -> str:
    pass



def get_sort(expr: str) -> type:
    pass



def main():

    test_expr1 = '(or (and a b) (not (and (not a) c)) d)'

    test_expr2 = """(seq-concat
                        (seq-repeat 5 (seq-bool a))
                        (seq-concat (seq-bool b) (seq-bool c)))"""
    
    test_expr3 = """(always
                        (range 4 $)
                        (prop-seq (seq-bool (not b))))"""

    test_expr4 = """(always (prop-seq (seq-bool (not b))))"""

    test_expr5 = """(let-rec
                    (prop1 (prop-and
                        (prop-bool a)
                        (prop-non-overlapped-implication (seq-bool true) prop2)))
                    (prop2 (prop-and
                        (prop-bool b)
                        (prop-non-overlapped-implication (seq-bool true) prop1)))
                    prop1)"""

    signal_dict = {'a': Signal('a'), 'b': Signal('b'), 'c': Signal('c')}


    expr_list1: List[Any] = expr_to_list(test_expr1)
    expr_list2: List[Any] = expr_to_list(test_expr2)
    expr_list3: List[Any] = expr_to_list(test_expr3)
    expr_list4: List[Any] = expr_to_list(test_expr4)
    expr_list5: List[Any] = expr_to_list(test_expr5)
 
    parse_expression(expr_list1, None, signal_dict, dict())
    parse_expression(expr_list2, None, signal_dict, dict())
    parse_expression(expr_list3, None, signal_dict, dict())
    parse_expression(expr_list4, None, signal_dict, dict())
    parse_expression(expr_list5, None, signal_dict, dict())



if __name__ == "__main__":

    main()
