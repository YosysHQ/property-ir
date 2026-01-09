from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, field, Field
import types
from typing import Literal, List, Optional, Any, Set, Dict, get_origin, get_args, Tuple, Union, ClassVar
from typing import get_type_hints
from typeguard import typechecked
import re
from graphviz import Digraph





@typechecked
@dataclass
class Int():
    value: int

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


@dataclass(frozen=True)
class NodeId[T: PropertyIrNode]:
    raw: int

    def __repr__(self):
        return f"{type(self).__name__}({self.raw})"

type LiteralType = bool | Int | str | Range | BoundedRange | IntOrUnbounded | Signal | Constant

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

        if elem not in self.parents:
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

    def make_representative(self, elem: T):
        current_repr = self.find(elem)
        if current_repr == elem:
            return
        self.parents[current_repr] = elem
        self.parents[elem] = elem


def forward_node_id_types(ty: Any) -> type:
    if hasattr(ty, '__origin__'):
        if ty.__origin__ is NodeId:
            return ty.__args__[0]
        return ty.__origin__[*map(forward_node_id_types, ty.__args__)]
    return ty




@typechecked
@dataclass
class PropertyIrNode(ABC):
    ir_container: IrContainer
    node_id: NodeId

    @classmethod
    def type_class(cls) -> type[PropertyIrNode]:
        while cls.__base__ is not PropertyIrNode:
            cls = cls.__base__
            if cls is None:
                raise NotImplementedError("type_class called on non-derived class")
        return cls

    @classmethod
    def get_child_fields(cls) -> list[Field[Any]]:
        children = []
        for field in fields(cls):
            if field.name not in ['ir_container', 'node_id', 'signature']:
                children.append(field)
        return children


    @classmethod
    def signature(cls) -> list[type]:
        signature = []

        for field in cls.get_child_fields():
            field_type = get_type_hints(cls)[field.name]
            signature.append(forward_node_id_types(field_type))

        return signature

    @abstractmethod
    def __init__(self):
        pass

    def node_type(self) -> type[PropertyIrNode]:
        return type(self)

@typechecked
@dataclass
class PlaceholderNode(PropertyIrNode):
    expected_type: type[PropertyIrNode] | None

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
        self.check_type(node.node_type().type_class())
        self.ir_container.merge_nodes(self.node_id, node.node_id)




# @typechecked  # TODO doesn't seem to support add_node_by_kwargs signature
class IrContainer:

    nodes: dict[NodeId, PropertyIrNode]

    node_names: dict[str, NodeId]
    node_names_instantiated: dict[str, NodeId]
    merged_nodes: UnionFind[NodeId]

    next_raw_node_id: int

    def __init__(self):
        self.nodes =  dict()
        self.node_names = dict()
        self.node_names_instantiated = dict()
        self.merged_nodes = UnionFind()
        self.next_raw_node_id = 1

    def _get_next_node_id(self) -> NodeId:
        node_id = NodeId(self.next_raw_node_id)
        self.next_raw_node_id += 1
        return node_id

    def add_node_by_kwargs[T: PropertyIrNode](self, cls: type[T], kwargs: dict[str, Any]) -> T:
        new_node_id = self._get_next_node_id()
        new_node = cls(ir_container=self, node_id=new_node_id, **kwargs) # type: ignore # TODO can this be type checked?
        self.nodes[new_node_id] = new_node
        return new_node

    def add_placeholder_node(self, name: str, expected_type: Optional[type] = None) -> PlaceholderNode:
        new_node_id = self._get_next_node_id()
        new_node = PlaceholderNode(ir_container=self, node_id=new_node_id, expected_type=expected_type)
        self.nodes[new_node_id] = new_node
        self.node_names[name] = new_node_id
        return new_node

    def show_graph(self, filename: str) -> None:


        graph: Digraph = Digraph()


        for node in self.nodes.values():

            representative_id = self.merged_nodes.find(node.node_id)
            if representative_id != node.node_id:
                graph.edge(repr(node.node_id), repr(representative_id), 'merged', style='dashed')

            if isinstance(node, PlaceholderNode):

                graph.node(repr(node.node_id), repr(node.node_id))

            else: # if node is not a PlaceholderNode

                graph.node(repr(node.node_id), f'{type(node).__name__} {node.node_id}', shape='box')

                signature = type(node).signature()

                for index, field in enumerate(node.get_child_fields()):

                    child_type: type = signature[index]
                    if get_origin(child_type) is list:
                        children_list = getattr(node, field.name)
                        for child_node_id in children_list:
                            if isinstance(child_node_id, LiteralType.__value__):
                                graph.node(repr(child_node_id), repr(child_node_id), shape='diamond')
                            graph.edge(repr(node.node_id), repr(child_node_id), field.name)

                    else: # if child type is not a list
                        child_node_id = getattr(node, field.name)
                        if isinstance(child_node_id, LiteralType.__value__):
                            graph.node(repr(child_node_id), repr(child_node_id), shape='diamond')
                        graph.edge(repr(node.node_id), repr(child_node_id), field.name)



        for (node_name, node_id) in self.node_names.items():
            graph.node(f'__NODENAME__{node_name}', node_name, shape='plain')
            graph.edge(f'__NODENAME__{node_name}', repr(node_id), 'name', style='dashed')


        graph.render(filename, view=True, format='png')



    def bypass_placeholders(self) -> None:
        """Remove placeholder nodes by letting their parents point directly to
        the instantiated nodes they are to be replaced by."""

        placeholder_ids_to_remove = []

        # for all nodes for all their children
        for node in self.nodes.values():
            print(f'START NODE {node}')
            if isinstance(node, PlaceholderNode):
                representative_id = self.merged_nodes.find(node.node_id)
                if representative_id != node.node_id:
                    placeholder_ids_to_remove.append(node.node_id)
                print(f'SKIP PLACEHOLDER')
                continue

            signature = type(node).signature()

            for index, field in enumerate(node.get_child_fields()):

                child_type: type = signature[index]
                if get_origin(child_type) is list:

                    children_list = getattr(node, field.name)
                    for child_list_index, child_node_id in enumerate(children_list):
                        if isinstance(child_node_id, LiteralType.__value__): # skip literal type
                            continue
                        child_node = self[child_node_id]

                        # if child is a placeholder
                        # replace child node id by node id the placeholder (or its representative) points to
                        if isinstance(child_node, PlaceholderNode):
                            print(f'CHILD PLACEHOLDER {child_node}')
                            child_representative_id = self.merged_nodes.find(child_node_id)
                            children_list[child_list_index] = child_representative_id

                else: # attribute is not a list
                    child_node_id = getattr(node, field.name)
                    if isinstance(child_node_id, LiteralType.__value__): # skip literal type
                        continue
                    child_node = self[child_node_id]
                    if isinstance(child_node, PlaceholderNode):
                        print(f'CHILD PLACEHOLDER {child_node}')
                        child_representative_id = self.merged_nodes.find(child_node_id)
                        setattr(node, field.name, child_representative_id)

        for placeholder_id in placeholder_ids_to_remove:
            del self.nodes[placeholder_id]

    def __getitem__(self, node_id: NodeId) -> PropertyIrNode:
        node_repr_id: NodeId = self.merged_nodes.find(node_id)
        if node_repr_id in self.nodes:
            return self.nodes[node_repr_id]
        else:
            raise ValueError(f'NodeID {node_repr_id} missing' )

    def __contains__(self, node_id: NodeId) -> bool:
        return node_id in self.nodes

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

        node1 = self[node_id1]
        node2 = self[node_id2]

        if not (isinstance(node1, PlaceholderNode) or isinstance(node2, PlaceholderNode)):
            raise ValueError(f'Cannot merge non-placeholder node {node_id1} with non-placeholder node {node_id2}')

        self.merged_nodes.union(node_id1, node_id2)

        if isinstance(node1, PlaceholderNode) and not isinstance(node2, PlaceholderNode):
            self.merged_nodes.make_representative(node_id2)
        elif isinstance(node2, PlaceholderNode) and not isinstance(node1, PlaceholderNode):
            self.merged_nodes.make_representative(node_id1)




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
class Not(Bool):
    child: NodeId[Bool]

@typechecked
@dataclass
class And(Bool):
    children: list[NodeId[Bool]]

@typechecked
@dataclass
class Or(Bool):
    children: list[NodeId[Bool]]






@typechecked
@dataclass
class SeqConcat(Sequence):
    children: list[NodeId[Sequence]]

@typechecked
@dataclass
class SeqBool(Sequence):
    child: Bool

@typechecked
@dataclass
class SeqRepeat(Sequence):
    child1: Range
    child2: NodeId[Sequence]





@typechecked
@dataclass
class PropAlways(Property):
    child: NodeId[Property]


@typechecked
@dataclass
class PropAlwaysRanged(Property):
    child1: Range
    child2: NodeId[Property]

@typechecked
@dataclass
class PropAnd(Property):
    children: list[NodeId[Property]]

@typechecked
@dataclass
class PropSeq(Property):
    child: NodeId[Sequence]

@typechecked
@dataclass
class PropNonOverlappedImplication(Property):
    child1: NodeId[Sequence]
    child2: NodeId[Property]




def operation_to_class_str(input: str) -> str:
    split: list[str] = input.split('-')
    capitalized : list[str] = [str.capitalize(s) for s in split]
    return(''.join(capitalized))


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


    return 0











def print_expression(root: PropertyIrNode) -> str:
    raise NotImplementedError("TODO")






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

    print(ir_container5.nodes)
    print(ir_container5.node_names)
    print(ir_container5.merged_nodes.parents)

    #parse_expression(expr_list9, None, signal_dict, ir_container9)
    ir_container5.show_graph('container5.png')
    #ir_container7.bypass_placeholders()

    #ir_container7.show_graph('container7_no_placeholders.png')

    #print(ir_container7.nodes)
    #print(ir_container7.node_names)
    #print(ir_container7.merged_nodes.parents)

if __name__ == "__main__":

    main()
