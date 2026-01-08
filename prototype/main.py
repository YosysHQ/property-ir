#from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, field
from typing import Literal, List, Optional, Any, Set, Dict, get_origin, get_args, Tuple, Union, ClassVar
from typing import get_type_hints
from typeguard import typechecked
import re



type NodeId = int
type NodeType = Literal[Bool, Sequence, Property]
type NodeListType = Literal[list[Bool]] | Literal[list[Sequence]] | Literal[list[Property]]
type LiteralType = Literal[bool, int, str, Range, BoundedRange, IntOrUnbounded]

type RawSExpr = list[str | int | RawSExpr]

@typechecked
class UnionFind[T]:
    """Used to keep track of merged nodes. Will only add nodes to the
    data structure when they get merged."""

    parents: dict[T, T]
    ranks: dict[T, int]

    def __init__(self):
        self.parents =  dict()
        self.ranks = dict()

    def find(self, elem: T) -> T:

        if not elem in self.parents:
            return elem

        parent: T = self.parents[elem]
        if elem == parent:
            return elem
        else:
            representative = self.find(parent)
            self.parents[elem] = representative # path compression
            return representative


    def union(self, elem1: T, elem2: T) -> None:

        if elem1 not in self.parents:
            self.parents[elem1] = elem1
            self.ranks[elem1] = 0
        if elem2 not in self.parents:
            self.parents[elem2] = elem2
            self.ranks[elem2] = 0

        repr1: T = self.find(elem1)
        repr2: T = self.find(elem2)

        # union by rank
        if self.ranks[repr1] < self.ranks[repr2]:
            self.parents[repr1] = repr2
        elif self.ranks[repr2] < self.ranks[repr1]:
            self.parents[repr2] = repr1
        else:
            self.parents[repr1] = repr2
            self.ranks[repr2] += 1







@typechecked
@dataclass
class PropertyIrNode(ABC):
    ir_container: 'IrContainer'
    node_id: NodeId
    signature: ClassVar[tuple[NodeType | LiteralType, ...] | tuple[NodeListType]]

    @classmethod
    def get_child_fields(cls) -> list[NodeType | LiteralType]:
        children: list[NodeType | LiteralType] = []
        for field in fields(cls):
            if field.name not in ['ir_container', 'node_id', 'signature']:
                children.append(field)
        return children

    @abstractmethod
    def __init__(self):
        pass



@typechecked
@dataclass
class PlaceholderNode(PropertyIrNode):
    replace_with: PropertyIrNode | None
    expected_type: type[PropertyIrNode] | None
    signature = ()

    def node_type(self) -> type[PropertyIrNode]:
        if self.expected_type is None:
            raise ValueError(f'Placeholder node {self} node type missing')
        else:
            return self.expected_type

    def check_type(self, node_type: type[PropertyIrNode]):
        if self.expected_type is None:
            self.expected_type = node_type
        elif not issubclass(self.expected_type, node_type):
            raise TypeError(f'Placeholder node {self} with type {self.expected_type} cannot be set to type {node_type}')
        # assuming that the type of a placeholder node does not change / get more refined (no unification)

    def instantiate_placeholder(self, node: PropertyIrNode):
        self.check_type(cls_to_type[type(node)])
        self.replace_with = node




@typechecked
class IrContainer:

    nodes: dict[NodeId, PropertyIrNode]

    node_names: dict[str, NodeId]
    merged_nodes: UnionFind[NodeId]

    next_node_id: NodeId

    def __init__(self):
        self.nodes =  dict()
        self.node_names = dict()
        self.merged_nodes = UnionFind()
        self.next_node_id = 1

    def _get_next_node_id(self):
        node_id = self.next_node_id
        self.next_node_id += 1
        return node_id

    def add_node_by_kwargs(self, cls: type, kwargs: dict[str, Any]) -> PropertyIrNode:
        new_node_id = self._get_next_node_id()
        new_node = cls(ir_container=self, node_id=new_node_id, **kwargs)
        self.nodes[new_node_id] = new_node
        return new_node

    def add_placeholder_node(self, name: str, expected_type: Optional[type] = None):
        new_node_id = self._get_next_node_id()
        new_node = PlaceholderNode(ir_container=self, node_id=new_node_id, expected_type=expected_type, replace_with=None)
        self.nodes[new_node_id] = new_node
        self.node_names[name] = new_node_id
        return new_node


    def __getitem__(self, node_id: NodeId) -> PropertyIrNode:
        node_repr_id: NodeId = self.merged_nodes.find(node_id)
        if node_repr_id in self.nodes:
            return self.nodes[node_repr_id]
        else:
            raise ValueError(f'NodeID {node_repr_id} missing' )

    def __contains__(self, node_id: NodeId) -> bool:
        return node_id in nodes

    def __setitem__(self, node_id: NodeId, value: PropertyIrNode):
        if (not node_id in self.nodes):
            raise ValueError(f'Cannot set node with node id {node_id} because it does not exist')
        node_repr_id: NodeId = self.merged_nodes.find(node_id)
        self.nodes[node_repr_id] = value


    def get_node_id_by_name(self, node_name: str):
        if node_name in self.node_names:
            node_id: NodeId = self.node_names[node_name]
            return self.merged_nodes.find(node_id)
        else:
            raise ValueError(f'Node name {node_name} missing' )

    def merge_nodes(self, node_id1, node_id2):
        if (not node_id1 in self.nodes):
            raise ValueError(f'Could not merge {node_id1} and {node_id2} because {node_id1} is missing')
        if (not node_id2 in self.nodes):
            raise ValueError(f'Could not merge {node_id1} and {node_id2} because {node_id2} is missing')

        placeholder_node1: PlaceholderNode = self[node_id1]
        placeholder_node2: PlaceholderNode = self[node_id2]
        replacing_node1: Optional[PropertyIrNode] = placeholder_node1.replace_with
        replacing_node2: Optional[PropertyIrNode] = placeholder_node1.replace_with

        if replacing_node1 is not None and replacing_node2 is not None:
            if replacing_node1 != replacing_node2:
                raise ValueError(f'Attempting to merge {node_id1} and {node_id2}, but both are instantiated with different nodes. Is a node name reused?')
        elif replacing_node1 is not None:
            placeholder_node2.instantiate_placeholder(replacing_node1)
        elif replacing_node2 is not None:
            placeholder_node1.instantiate_placeholder(replacing_node2)

        self.merged_nodes.union(node_id1, node_id2)







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
class IntOrUnbounded():
    value: int | Literal['$']

@typechecked
@dataclass
class Range():
    lower_bound: int
    upper_bound: IntOrUnbounded

@typechecked
@dataclass
class BoundedRange():
    lower_bound: int
    upper_bound: int




@typechecked
@dataclass
class Not(Bool):
    child: NodeId
    signature = (Bool,)

@typechecked
@dataclass
class And(Bool):
    children: list[NodeId]
    signature = (list[Bool],)

@typechecked
@dataclass
class Or(Bool):
    children: list[NodeId]
    signature = (list[Bool],)





# literal treated as node type Bool
@typechecked
@dataclass
class Signal():
    signal_name: str

# literal treated as node type Bool
@typechecked
@dataclass
class Constant():
    value: bool






@typechecked
@dataclass
class SeqConcat(Sequence):
    children: list[NodeId]
    signature = (list[Sequence],)

@typechecked
@dataclass
class SeqBool(Sequence):
    child: Bool
    signature = (Bool,)

@typechecked
@dataclass
class SeqRepeat(Sequence):
    child1: Range
    child2: NodeId
    signature = (Range, Sequence)





@typechecked
@dataclass
class PropAlways(Property):
    child: NodeId
    signature = (Property,)


@typechecked
@dataclass
class PropAlwaysRanged(Property):
    child1: Range
    child2: NodeId
    signature = (Range, Property)

@typechecked
@dataclass
class PropAnd(Property):
    children: list[NodeId]
    signature = (list[Property],)

@typechecked
@dataclass
class PropSeq(Property):
    child: NodeId
    signature = (Sequence,)

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: NodeId
    child2: NodeId
    signature = (Sequence, Property)




def operation_to_class_str(input: str) -> str:
    split: list[str] = input.split('-')
    capitalized : list[str] = [str.capitalize(s) for s in split]
    return(''.join(capitalized))


def class_to_operation_str(input: str) -> str:
    split: list[str] = re.split(r'(?=[A-Z])', input)
    lowercase: list[str] = [str.lower(s) for s in split if s != '']
    return('-'.join(lowercase))


@typechecked
def get_op_symbols() -> tuple[dict[str, NodeType], dict[str, NodeType], dict[type[PropertyIrNode], NodeType]]:
    allowed_types = [Bool, Sequence, Property]
    ops_to_cls: dict[str, NodeType] = dict()
    ops_to_type: dict[str, NodeType] = dict()
    cls_to_type: dict[type[PropertyIrNode], NodeType] = dict()

    for node_type in allowed_types:
        for cls in node_type.__subclasses__():
            ops_to_cls[class_to_operation_str(cls.__name__)] = cls
            ops_to_type[class_to_operation_str(cls.__name__)] = node_type
            cls_to_type[cls] = node_type

    return ops_to_cls, ops_to_type, cls_to_type


op_symbol_tables = get_op_symbols()
op_to_cls: dict[str, NodeType] = op_symbol_tables[0]
op_to_type: dict[str, NodeType] = op_symbol_tables[1]
cls_to_type: dict[type[PropertyIrNode], NodeType] = op_symbol_tables[2]










@typechecked
def expr_to_list(expr: str) -> RawSExpr:
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
    stack: RawSExpr = []

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
            return Range(lower_bound, upper_bound)
        case ['range', int(lower_bound), '$']:
            return Range(lower_bound, '$')
        case _:
            raise ValueError(f'Unexpected range expression form {range_expr}')



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
                return Constant(expr)
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

            if not (expected_type is int or expected_type is IntOrUnbounded):
                raise TypeError(f'Mismatch of expected type {expected_type} and {literal} with type {type(literal)} in {expr}')
            return literal

        case ['range', *args] | ['bounded-range', *args]:

            return parse_range(expr)




        case ['let-rec', *named_subexpressions, return_expression]:

            # create a placeholder node for each new node name
            for (name, subexpr) in named_subexpressions:
                if name in ir_container.node_names:
                    raise ValueError(f'Node name {name} already exists in expression {expr}')
                ir_container.add_placeholder_node(name=name)

            # evaluate each named subexpression
            # and let each placeholder point to the root of its subexpression
            # or if the root is a placeholder, merge placeholders
            for (name, subexpr) in named_subexpressions:
                subexpr_root_node_id: NodeId = parse_expression(subexpr, None, signals, ir_container)
                subexpr_root_node: NodeId = ir_container[subexpr_root_node_id]
                placeholder_id: NodeId = ir_container.get_node_id_by_name(name)
                placeholder_node: PlaceholderNode = ir_container[placeholder_id]

                if isinstance(subexpr_root_node, PlaceholderNode):
                    ir_container.merge_nodes(subexpr_root_node_id, placeholder_id)
                else:
                    placeholder_node.instantiate_placeholder(subexpr_root_node)

            # return value of last expression
            return parse_expression(return_expression, None, signals, ir_container)




        case [str(root_symbol), *args]:

            if root_symbol in op_to_cls:

                root_class: type = op_to_cls[root_symbol]

                if expected_type:
                    if not op_to_type[root_symbol] is expected_type:
                        raise TypeError(f'Mismatch of expected type {expected_type} and operation "{root_symbol}" with type {op_to_type[root_symbol]} in {expr}')

                kwargs: dict[str, Any] = {}

                for (index, field) in enumerate(root_class.get_child_fields()):

                    child_expected_type: type = root_class.signature[index]

                    if get_origin(child_expected_type) is list:
                        list_elem_type: type = get_args(child_expected_type)[0]
                        single_child_list: list[list_elem_type] = []

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


    return 0











def print_expression(root: PropertyIrNode) -> str:
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
        (foo (and a bar))
        (bar (or b c))
        foo
    )"""

    test_expr6 = """(let-rec
                        (prop1 (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool true) prop2)))
                        (prop2 (prop-and
                            (prop-seq (seq-bool a))
                            (prop-non-overlapped-implication (seq-bool true) prop1)))
                        prop1)"""

    test_expr7 = """(let-rec
        (q1 (seq-concat (seq-bool a) q3))
        (q2 (seq-concat (seq-bool b) q4))
        (q3 q4)
        (q4 (seq-bool c))
        (q5 q3)
        (seq-concat (seq-bool d) q5)
    )"""

    # nested let-rec
    test_expr8 = """(let-rec
        (q1 (and a b))
        (q2 (let-rec
                (p1 (not q1))
                (p2 q1)
                (p3 (or q2 c))
                p3))
        q2)"""

    # this should cause a type error
    test_expr9 = """(let-rec
        (foo2 (and a bar2))
        (bar2 (seq-concat (seq-bool a) (seq-bool b)))
        foo2)"""

    signal_dict = {'a': Signal('a'), 'b': Signal('b'), 'c': Signal('c'), 'd': Signal('d')}


    print(op_to_cls)
    print()
    print(op_to_type)
    print()

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
    expr_list6: List[Any] = expr_to_list(test_expr6)
    print()
    expr_list7: List[Any] = expr_to_list(test_expr7)
    print()
    expr_list8: List[Any] = expr_to_list(test_expr8)
    print()
    expr_list9: List[Any] = expr_to_list(test_expr9)
    print()

    ir_container1 = IrContainer()
    ir_container2 = IrContainer()
    ir_container3 = IrContainer()
    ir_container4 = IrContainer()
    ir_container5 = IrContainer()
    ir_container6 = IrContainer()
    ir_container7 = IrContainer()
    ir_container8 = IrContainer()
    ir_container9 = IrContainer()


    parse_expression(expr_list1, None, signal_dict, ir_container1)
    print()
    parse_expression(expr_list2, None, signal_dict, ir_container2)
    print()
    parse_expression(expr_list3, None, signal_dict, ir_container3)
    print()
    parse_expression(expr_list4, None, signal_dict, ir_container4)
    print()
    parse_expression(expr_list5, None, signal_dict, ir_container5)
    print()
    parse_expression(expr_list6, None, signal_dict, ir_container6)
    print()
    parse_expression(expr_list7, None, signal_dict, ir_container7)
    print()
    parse_expression(expr_list8, None, signal_dict, ir_container8)
    print()
    #print(ir_container7.nodes)
    #print(ir_container7.node_names)
    #print(ir_container7.merged_nodes.parents)
    #parse_expression(expr_list9, None, signal_dict, ir_container9)


if __name__ == "__main__":

    main()
