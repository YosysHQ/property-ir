from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, fields, Field
from typing import Literal, Optional, Any, get_origin, get_type_hints, get_args
from typeguard import typechecked
from graphviz import Digraph
from pathlib import Path
import re

from .utils import UnionFind




@typechecked
@dataclass
class IntOrUnbounded:
    value: int | Literal['$']

    def get_raw_sexpr_repr(self) -> str:
        return str(self.value)


@typechecked
@dataclass
class Range():
    lower_bound: int
    upper_bound: IntOrUnbounded

    def get_raw_sexpr_repr(self) -> RawSExpr:
        return ['range', str(self.lower_bound), self.upper_bound.get_raw_sexpr_repr()]

@typechecked
@dataclass
class BoundedRange():
    lower_bound: int
    upper_bound: int

    def get_raw_sexpr_repr(self) -> RawSExpr:
        return ['bounded-range', str(self.lower_bound), str(self.upper_bound)]





@dataclass(frozen=True)
class NodeId[T: PropertyIrNode]:
    raw: int

    def __repr__(self):
        return f"{type(self).__name__}({self.raw})"

type LiteralType = bool | Range | BoundedRange | IntOrUnbounded | int | str

type RawSExpr = list[str | RawSExpr]




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





class Declaration():
    @abstractmethod
    def __init__(self):
        pass

@dataclass
class SignalDeclaration(Declaration):
    node_name: str
    node_id: NodeId[Any]

@dataclass
class NamedExpressionDeclaration(Declaration):
    node_name: str
    node_id: NodeId[Any]

@dataclass
class NamedRecursiveDeclaration(Declaration):
    node_names: dict[str, NodeId[Any]]

@dataclass
class UnnamedExpressionDeclaration(Declaration):
    node_id: NodeId[Any]



# @typechecked  # TODO doesn't seem to support add_node_by_kwargs signature
class IrContainer:

    nodes: dict[NodeId, PropertyIrNode]

    node_names: dict[str, NodeId] # local and global node names; pairs are superset of global node names
    global_nodes: dict[str, NodeId] # contains signals and other declared node names
    merged_nodes: UnionFind[NodeId] # nodes that are equivalent through naming; each union must contain only one non-placeholder

    # all declarations that were added to the container in the order they were added
    declarations: list[Declaration]

    source_nodes: dict[str, NodeId] # def-only = signal nodes
    inner_nodes: dict[str, NodeId] # def/use = declare/declare-rec named global nodes
    sink_nodes: list[NodeId] # use-only = unnamed expression roots

    next_raw_node_id: int

    def __init__(self):
        self.nodes =  dict()
        self.node_names = dict()
        self.global_nodes = dict()
        self.declarations = list()
        self.merged_nodes = UnionFind()
        self.source_nodes = dict()
        self.inner_nodes = dict()
        self.sink_nodes = list()
        self.next_raw_node_id = 1

    def _get_next_node_id(self) -> NodeId:
        node_id = NodeId(self.next_raw_node_id)
        self.next_raw_node_id += 1
        return node_id

    def _generate_literal_raw_sexpr(self, literal: LiteralType) -> RawSExpr | str:
        if isinstance(literal, str):
            return literal
        elif isinstance(literal, bool):
            return str.lower(str(literal))
        elif isinstance(literal, int):
            return str(literal)
        elif isinstance(literal, Range | BoundedRange | IntOrUnbounded):
            return literal.get_raw_sexpr_repr()
        raise TypeError(f'Unexpected type {type(literal)} of literal {literal} while generating s-expression of container {self}')

    def output_container(self) -> RawSExpr:
        """Output the complete contents of the container as a property ir document
        s-expression.
        """
        # TODO implement

        # result_document = []
        # declaration_exprs = []

        # for declaration in self. declaration : ...

        #signals_expr = ['add-signals'] + list(signals_to_add)

        #result_document = ['document', signals_expr, ['parse-sexpr', result_expr]]

        #return result_document

        raise NotImplementedError("TODO")


    def generate_raw_sexpr(self, node_id: NodeId, declared_nodes: dict[NodeId, str]) -> RawSExpr | str:
        """With the given node_id as the root, output the graph reachable from it as an s-expression
        in the form of a let-rec with one line per node. Unnamed nodes get a new unique local name based on their id.
        The nodes in declared_nodes are output as their provided name (usually previously declared global node names)
        and not further expanded. The dict is expected to use representative node ids of merged nodes."""

        # TODO handle declare-rec

        if node_id not in self.nodes:
            raise ValueError(f'Cannot generate s-expression for missing node {node_id} of container {self}')

        input_repr_id = self.merged_nodes.find(node_id)
        if input_repr_id in declared_nodes:
            return declared_nodes[input_repr_id]

        id_to_node_name: dict[NodeId, str] = dict()
        for (name, named_node_id) in self.node_names.items():
            id_to_node_name[self.merged_nodes.find(named_node_id)] = name
            # if there are several names for a node, one is chosen arbitrarily
            # to be used consistently

        # overwrite chosen names by those used in declared_nodes
        for (named_node_id, name) in declared_nodes.items():
            id_to_node_name[self.merged_nodes.find(named_node_id)] = name

        print(id_to_node_name)

        node_expr_list: RawSExpr = list()
        visited_nodes: set[NodeId] = set()

        visit_next = deque([node_id])

        # search through reachable nodes from given node or all root nodes of the container
        # and generate expr for each node visited, skip if already visited or declared
        # (can happen if root nodes are part of the same strongly connected component or several edges point to a child)
        while len(visit_next) != 0:
            current_node_id = visit_next.popleft()

            print(f'current node id {current_node_id}')
            print(f'visit next {visit_next}')

            current_repr_id = self.merged_nodes.find(current_node_id)
            if current_repr_id in visited_nodes:
                continue

            # TODO: should this be allowed to happen and we just continue outputting?
            if (current_repr_id not in declared_nodes and current_repr_id in self.global_nodes):
                raise ValueError(f'Encountered undeclared global node {current_repr_id} while generating raw s-expression for node {node_id} with declared nodes {declared_nodes}')

            visited_nodes.add(current_repr_id)

            if current_repr_id not in id_to_node_name:
                new_name = self.uniquify('_node_id_' + str(current_repr_id.raw))
                current_node_expr = [new_name]
                id_to_node_name[current_repr_id] = new_name
                # there can be no name clashes within the newly generated name names
                # because they all have a different node id and uniquify can only append _{number}

            current_node_name: str = id_to_node_name[current_repr_id]
            current_node = self.nodes[current_repr_id]

            if isinstance(current_node, PlaceholderNode):
                raise ValueError(f'Cannot generate s-expression for container {self} with uninstantiated node {current_node.node_id}')
            elif isinstance(current_node, Signal) and current_repr_id not in declared_nodes:
                raise ValueError(f'Cannot generate s-expression for container {self} starting from node id {node_id} with reachable undeclared signal id {current_repr_id}')
            elif isinstance(current_node, Signal):
                continue

            current_node_expr: RawSExpr = [current_node.op_symbol()]
            signature = type(current_node).signature()

            collected_children: list[NodeId | LiteralType] = list()

            for index, field in enumerate(current_node.get_child_fields()):

                field_type: type = signature[index]

                if get_origin(field_type) is list:
                    collected_children += getattr(current_node, field.name)
                else:
                    collected_children.append(getattr(current_node, field.name))


            for child_elem in collected_children:
                if isinstance(child_elem, NodeId):
                    child_repr_id = self.merged_nodes.find(child_elem)
                    if child_repr_id not in id_to_node_name:
                        child_new_name = self.uniquify('_node_id_' + str(child_repr_id.raw))
                        id_to_node_name[child_repr_id] = child_new_name
                    current_node_expr.append(id_to_node_name[child_repr_id])
                    visit_next.append(child_repr_id)
                elif isinstance(child_elem, LiteralType.__value__):
                    current_node_expr.append(self._generate_literal_raw_sexpr(child_elem))
                else:
                    raise TypeError(f'Unexpected child type of {child_elem} while generating s-expression for node {current_node}')


            node_expr_list.append([current_node_name, current_node_expr])


        result_expr: RawSExpr = ['let-rec']
        result_expr += node_expr_list
        result_expr.append(id_to_node_name[self.merged_nodes.find(node_id)])

        return result_expr




    def uniquify(self, name: str) -> str:
        """Given a node name, returns a unique name with that prefix that is not
        used by the container (globally or locally)."""

        if name not in self.node_names:
            return name
        else:
            split_name = name.split('_')
            if len(split_name) == 1:
                return self.uniquify(name + '_2')
            elif len(split_name) > 1:
                suffix = split_name[-1]
                if str.isnumeric(suffix):
                    new_suffix = int(suffix) + 1
                    new_name = '_'.join(split_name[0:-1]) + '_' + str(new_suffix)
                    while new_name in self.node_names:
                        new_suffix += 1
                        new_name = '_'.join(split_name[0:-1]) + '_' + str(new_suffix)
                    return new_name
                else: # suffix is not numeric
                    return self.uniquify(name + '_2')
        raise ValueError(f'Could not uniquify name {name}')

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
        return signal_node

    def add_declaration(self, declaration: Declaration):
        """Adds the declaration to the container and sets global node names accordingly.
        If an identical local name in node_names exists and points to a different node,
        that local name is renamed."""

        name_id_pairs: list[tuple[str, NodeId[Any]]] = []

        if isinstance(declaration, SignalDeclaration):
            name_id_pairs.append((declaration.node_name, declaration.node_id))
            self.source_nodes[declaration.node_name] = declaration.node_id
        elif isinstance(declaration, NamedExpressionDeclaration):
            name_id_pairs.append((declaration.node_name, declaration.node_id))
            self.inner_nodes[declaration.node_name] = declaration.node_id
        elif isinstance(declaration, NamedRecursiveDeclaration):
            for node_name, node_id in declaration.node_names.items():
                name_id_pairs.append((node_name, node_id))
                self.inner_nodes[node_name] = node_id
        elif isinstance(declaration, UnnamedExpressionDeclaration):
            self.sink_nodes.append(declaration.node_id)

        for node_name, node_id in name_id_pairs:
            if node_id not in self.nodes:
                raise ValueError(f'Cannot add declaration for non-existent node {node_id}')
            if node_name in self.global_nodes:
                raise ValueError(f'Attempting redeclaration of global node name {node_name}')
            self.global_nodes[node_name] = node_id
            if node_name in self.node_names: # reset local name if it exists and points to a different node
                if self.node_names[node_name] != node_id:
                    self.node_names[self.uniquify(node_name)] = self.node_names[node_name]
            self.node_names[node_name] = node_id

        self.declarations.append(declaration)


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
        the instantiated nodes they are to be replaced by.
        Updates node_names, global_nodes, and declarations accordingly."""

        placeholder_ids_to_remove = []

        for node_dict in [self.node_names, self.global_nodes, self.inner_nodes, self.source_nodes]:
            for node_name, node_id in node_dict.items():
                node_dict[node_name] = self.merged_nodes.find(node_id)

        for index, node_id in enumerate(self.sink_nodes):
            self.sink_nodes[index] = self.merged_nodes.find(node_id)

        for declaration in self.declarations:
            if isinstance(declaration, SignalDeclaration | NamedExpressionDeclaration | UnnamedExpressionDeclaration):
                declaration.node_id = self.merged_nodes.find(declaration.node_id)
            elif isinstance(declaration, NamedRecursiveDeclaration):
                for node_name, node_id in declaration.node_names.items():
                    declaration.node_names[node_name] = self.merged_nodes.find(node_id)


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

    # TODO this is not used, do we need it at all?
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




def operation_to_class_str(input: str) -> str:
    split: list[str] = input.split('-')
    capitalized : list[str] = [str.capitalize(s) for s in split]
    return(''.join(capitalized))









