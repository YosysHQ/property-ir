from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, Field
from typing import Literal, Optional, Any, get_origin, get_type_hints
from typeguard import typechecked
from graphviz import Digraph
from pathlib import Path
import re

from .utils import UnionFind




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





@dataclass(frozen=True)
class NodeId[T: PropertyIrNode]:
    raw: int

    def __repr__(self):
        return f"{type(self).__name__}({self.raw})"

type LiteralType = bool | Int | str | Range | BoundedRange | IntOrUnbounded

type RawSExpr = list[str | int | RawSExpr]




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
    def op_symbol(cls):
        split: list[str] = re.split(r'(?=[A-Z])', cls.__name__)
        lowercase: list[str] = [str.lower(s) for s in split if s != '']
        return('-'.join(lowercase))

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

    def check_type(self, node_type: type[PropertyIrNode]):
        if not issubclass(self.node_type(), node_type):
            raise TypeError(f'Placeholder node {self} with type {self.node_type()} cannot be set to type {node_type}')


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
        else:
            # assuming that the type of a placeholder node does not change / get more refined (no unification)
            super().check_type(node_type)

    def instantiate_placeholder(self, node: PropertyIrNode):
        self.check_type(node.node_type().type_class())
        self.ir_container.merge_nodes(self.node_id, node.node_id)




# @typechecked  # TODO doesn't seem to support add_node_by_kwargs signature
class IrContainer:

    nodes: dict[NodeId, PropertyIrNode]

    node_names: dict[str, NodeId]
    global_nodes: dict[str, NodeId]
    merged_nodes: UnionFind[NodeId]

    next_raw_node_id: int

    def __init__(self):
        self.nodes =  dict()
        self.node_names = dict()
        self.global_nodes = dict()
        self.merged_nodes = UnionFind()
        self.next_raw_node_id = 1

    def _get_next_node_id(self) -> NodeId:
        node_id = NodeId(self.next_raw_node_id)
        self.next_raw_node_id += 1
        return node_id

    def uniquify(self, name: str): # TODO: implement this
        return name

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

    def add_signal_node(self, signal_name: str) -> PropertyIrNode:
        if signal_name in self.global_nodes:
            raise ValueError(f'Attempting to add signal with name {signal_name}, but the name is already in use')
        signal_node = self.add_node_by_kwargs(Signal, dict(signal_name=signal_name))
        self.global_nodes[signal_name] = signal_node.node_id
        return signal_node

    def show_graph(self, output_path: Path) -> None:


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
            graph.edge(f'__NODENAME__{node_name}', repr(node_id), style='dashed')

        if not output_path.parent.exists():
                raise ValueError(f'Output directory {output_path.parent} for graph rendering missing')

        graph.render(filename=output_path.stem, directory=output_path.parent, view=True, format=output_path.suffix.lstrip('.'), cleanup=True)



    def bypass_placeholders(self) -> None:
        """Remove placeholder nodes by letting their parents point directly to
        the instantiated nodes they are to be replaced by."""

        placeholder_ids_to_remove = []

        for node_name, node_id in self.node_names.items():
            self.node_names[node_name] = self.merged_nodes.find(node_id)

        for node in self.nodes.values():
            print(f'START NODE {node}')
            if isinstance(node, PlaceholderNode):
                representative_id = self.merged_nodes.find(node.node_id)
                if representative_id != node.node_id:
                    print(f'represented by {representative_id}, mark to delete')
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
                        child_node_representative = self[child_node_id]
                        print(f'child node {child_node_representative}')

                        child_representative_id: NodeId = child_node_representative.node_id
                        if child_representative_id != child_node_id:
                            children_list[child_list_index] = child_representative_id

                else: # if child type is not list
                    child_node_id = getattr(node, field.name)
                    if isinstance(child_node_id, LiteralType.__value__): # skip literal type
                        continue

                    child_node_representative = self[child_node_id]
                    print(f'child node {child_node_representative}')

                    child_representative_id: NodeId = child_node_representative.node_id
                    if child_representative_id != child_node_id:
                        setattr(node, field.name, child_representative_id)

        for placeholder_id in placeholder_ids_to_remove:
            del self.nodes[placeholder_id]

        self.merged_nodes = UnionFind()


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



    def print_expression(self, root: PropertyIrNode) -> str:
        raise NotImplementedError("TODO")


def operation_to_class_str(input: str) -> str:
    split: list[str] = input.split('-')
    capitalized : list[str] = [str.capitalize(s) for s in split]
    return(''.join(capitalized))










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
class Signal(Bool):
    signal_name: str
