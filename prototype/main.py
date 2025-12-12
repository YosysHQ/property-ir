from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, List, Optional, Any
from typeguard import typechecked
import re



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
class Range(PropertyIrNode):
    lower_bound: int
    upper_bound: int | Literal['$']

@typechecked
@dataclass
class BoundedRange(Range):
    lower_bound: int
    upper_bound: int




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

@typechecked
@dataclass
class Signal(Bool):
    signal_name: str

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
    child1: Optional[Range]
    child2: Property

@typechecked
@dataclass
class PropAnd(Property):
    children: List[Property]

@typechecked
@dataclass
class PropSeq(Property):
    child: Sequence

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: Sequence
    child2: Property




def operation_to_class(input: str) -> str:
    splitted: List[str] = input.split('-')
    capitalized : List[str] = [str.capitalize(s) for s in splitted]
    return(''.join(capitalized))


def class_to_operation(input: str) -> str:
    splitted: List[str] = re.split(r'(?=[A-Z])', input)
    lowercase: List[str] = [str.lower(s) for s in splitted]
    return('-'.join(lowercase))










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



def get_parse_tree(expr: str) -> List[Any]:

    pass


def parse_expression(expr: str) -> PropertyIrNode:
    pass


def print_expression(root: PropertyIrNode) -> str:
    pass



def get_sort(expr: str) -> type:
    pass



def main():
    print("Hello from property-ir!")


if __name__ == "__main__":

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

 
    expr_to_list(test_expr1)
    expr_to_list(test_expr2)
    expr_to_list(test_expr3)
    expr_to_list(test_expr4)
    expr_to_list(test_expr5)

    main()
