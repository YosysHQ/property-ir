from __future__ import annotations
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, fields, Field, field
import logging
from typing import Literal, Optional, Any, get_origin, get_type_hints, get_args
from typeguard import typechecked
from graphviz import Digraph
from pathlib import Path
import re

from .utils import UnionFind


logger = logging.getLogger(__name__)


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

    def get_raw_sexpr_repr(self) -> RawSExprList:
        return ['range', str(self.lower_bound), self.upper_bound.get_raw_sexpr_repr()]

@typechecked
@dataclass
class BoundedRange():
    lower_bound: int
    upper_bound: int

    def get_raw_sexpr_repr(self) -> RawSExprList:
        return ['bounded-range', str(self.lower_bound), str(self.upper_bound)]





@dataclass(frozen=True)
class NodeId[T: PropertyIrNode]:
    raw: int

    def __repr__(self):
        return f"{type(self).__name__}({self.raw})"

type LiteralType = bool | Range | BoundedRange | IntOrUnbounded | int | str

type RawSExprList = list[RawSExpr]
type RawSExpr = RawSExprList | str




def forward_node_id_types(ty: Any) -> type:
    if hasattr(ty, '__origin__'):
        if ty.__origin__ is NodeId:
            return ty.__args__[0]
        return ty.__origin__[*map(forward_node_id_types, ty.__args__)]
    return ty




@typechecked
@dataclass(eq=True)
class PropertyIrNode(ABC):
    ir_container: IrContainer = field(compare=False)
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
        # merging 2 uninstantiated placeholders
        if isinstance(node, PlaceholderNode):
            if self.expected_type is None and node.expected_type is None:
                self.ir_container.merge_nodes(self.node_id, node.node_id)
                return

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

    def __eq__(self, other):
        """Two containers are only considered equivalent if they have the same types of nodes with the same node ids
        connected in the same way, and the same declared names and unnamed root nodes, each added in the same order,
        respectively. No merged nodes are allowed, else the equality check is not possible.
        Use canonical_id_renaming first in order to remove all unreachable or redundant nodes and rename node ids in
        depth-first order (this also resets merged_nodes)."""

        if not isinstance(other, IrContainer):
            return NotImplemented
        if not (len(self.merged_nodes.parents) == 0 and len(other.merged_nodes.parents) == 0):
            return NotImplemented
        return (self.nodes == other.nodes and
                self.global_nodes == other.global_nodes and
                self.source_nodes == other.source_nodes and
                self.inner_nodes == other.inner_nodes and
                self.sink_nodes == other.sink_nodes)

    def _get_next_node_id(self) -> NodeId:
        node_id = NodeId(self.next_raw_node_id)
        self.next_raw_node_id += 1
        return node_id

    def _generate_literal_raw_sexpr(self, literal: LiteralType) -> RawSExprList | str:
        if isinstance(literal, str):
            return literal
        elif isinstance(literal, bool):
            return str.lower(str(literal))
        elif isinstance(literal, int):
            return str(literal)
        elif isinstance(literal, Range | BoundedRange | IntOrUnbounded):
            return literal.get_raw_sexpr_repr()
        raise TypeError(f'Unexpected type {type(literal)} of literal {literal} while generating s-expression of container {self}')

    def output_container(self) -> RawSExprList:
        """Output the complete contents of the container as a property ir document s-expression.
        The order of output is source_nodes (signals), inner_nodes (declare/declare-rec), sink_nodes (unnamed expression roots),
        where everything reachable from inner_nodes is output in one large declare-rec expression.
        """

        statements: list[RawSExprList] = []

        for node_name in self.source_nodes:
            statements.append(['add-signals', node_name])

        if len(self.inner_nodes) != 0:
            inner_nodes_expr = self.generate_raw_sexpr_inner_nodes()
            statements.append(inner_nodes_expr)

        declared_nodes: dict[NodeId, str] = {self.merged_nodes.find(node_id): name for (name, node_id) in self.global_nodes.items()}
        for node_id in self.sink_nodes:
            statements.append(['parse-sexpr', self.generate_raw_sexpr_unnamed_root(node_id=node_id, declared_nodes=declared_nodes)])

        return ['document', *statements]


    def generate_raw_sexpr_inner_nodes(self) -> RawSExprList:
        """Generates one large declare-rec expression for all inner nodes (added with declare/declare-rec).
        Expects that all source node names can be used (have been declared earlier).
        Unnamed nodes get a new unique local name based on their id. Declared nodes use their global name(s) and nodes
        with only local names use one of those consistently (chosen aribitrarily).
        """

        inner_node_reprs_with_duplicates: list[NodeId] = [self.merged_nodes.find(node_id) for node_id in self.inner_nodes.values()]
        inner_node_reprs: list[NodeId] = list(dict.fromkeys(inner_node_reprs_with_duplicates))

        declared_nodes = {self.merged_nodes.find(node_id): name for (name, node_id) in self.source_nodes.items()}
        global_names_to_use = {self.merged_nodes.find(node_id): name for (name, node_id) in self.global_nodes.items() if self.merged_nodes.find(node_id) not in declared_nodes}

        processed_names = set(declared_nodes.values()).union(global_names_to_use.values())
        all_global_names = set(self.global_nodes.keys())
        unprocessed_names = all_global_names.difference(processed_names)

        node_names_to_use = {self.merged_nodes.find(node_id): name for (name, node_id) in self.node_names.items() if self.merged_nodes.find(node_id) not in declared_nodes}
        node_names_to_use |= global_names_to_use

        node_expr_defs: dict[str, RawSExprList] = self.generate_raw_sexpr_node_defs(inner_node_reprs, declared_nodes, node_names_to_use)

        logger.debug('node_expr_defs while generating inner nodes expr: %s', node_expr_defs)

        output_expr: RawSExprList = ['declare-rec']
        for (name, expr) in node_expr_defs.items():
            if name in self.global_nodes:
                output_expr.append(['declare', name, expr])
            else:
                output_expr.append([name, expr])

        logger.debug('unprocessed_names %s', unprocessed_names)

        for name in unprocessed_names:
            node_id = self.merged_nodes.find(self.global_nodes[name])
            used_name = declared_nodes[node_id]
            if used_name is None:
                used_name = global_names_to_use[node_id]
            output_expr.append(['declare', name, used_name])

        return output_expr



    def generate_raw_sexpr_node_defs(self, node_list: list[NodeId], declared_nodes: dict[NodeId, str], node_names_to_use: dict[NodeId, str]) -> dict[str, RawSExprList]:
        """Generates a list of node definitions of the form (name expression) for all nodes reachable from those in node_list.
        The nodes in declared_nodes are not output or further expanded, and when appearing as children, they are named as
        in declared_nodes. The generated node expressions get a new unique local name, or, if present, use
        node_names_to_use instead. These two dicts need to consist of disjoint node sets.
        No uninstantiated placeholder nodes are allowed and all encountered signal nodes need to be contained in declared_nodes.
        """

        node_reprs_with_duplicates: list[NodeId] = [self.merged_nodes.find(node_id) for node_id in node_list]
        node_reprs: list[NodeId] = list(dict.fromkeys(node_reprs_with_duplicates))

        for node_id in node_reprs:
            if node_id not in self.nodes:
                raise ValueError(f'Cannot generate s-expression for missing node {node_id} of container {self}')

        visit_next: deque[NodeId] = deque(node_reprs)

        # give new node names to all nodes
        # there can be no name clashes within the newly generated names
        # because they all have a different node id and uniquify can only append _{number}
        id_to_node_name: dict[NodeId, str] = dict()
        for node_id in self.nodes:
            id_to_node_name[node_id] = self.uniquify('_node_id_' + str(node_id.raw))
        # overwrite chosen names by those used in declared_nodes and in node_names_to_use
        declared_nodes_reprs: set[NodeId] = {self.merged_nodes.find(node_id) for node_id in declared_nodes}
        for (named_node_id, name) in declared_nodes.items():
            id_to_node_name[self.merged_nodes.find(named_node_id)] = name
        for (named_node_id, name) in node_names_to_use.items():
            repr_id = self.merged_nodes.find(named_node_id)
            if repr_id in declared_nodes_reprs:
                raise ValueError(f'Declared nodes and node names to use must be disjoint, node with id {repr_id} and name {name} occuring in both')
            id_to_node_name[repr_id] = name

        node_expr_dict: dict[str, RawSExprList] = dict()
        visited_nodes: set[NodeId] = set()

        # search through reachable nodes and generate expr for each node visited, skip if already visited or declared
        while len(visit_next) != 0:
            current_node_id = visit_next.popleft()

            current_repr_id = self.merged_nodes.find(current_node_id)
            if current_repr_id in visited_nodes or current_repr_id in declared_nodes:
                continue

            visited_nodes.add(current_repr_id)

            current_node_name: str = id_to_node_name[current_repr_id]
            current_node = self.nodes[current_repr_id]

            if isinstance(current_node, PlaceholderNode):
                raise ValueError(f'Cannot generate s-expression for container {self} with uninstantiated node {current_node.node_id}')
            elif isinstance(current_node, Signal) and current_repr_id not in declared_nodes:
                raise ValueError(f'Cannot generate s-expression for container {self} with reachable undeclared signal id {current_repr_id}')
            elif isinstance(current_node, Signal):
                continue

            current_node_expr: RawSExprList = [current_node.op_symbol()]
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
                    current_node_expr.append(id_to_node_name[child_repr_id])
                    visit_next.append(child_repr_id)
                elif isinstance(child_elem, LiteralType.__value__):
                    current_node_expr.append(self._generate_literal_raw_sexpr(child_elem))
                else:
                    raise TypeError(f'Unexpected child type of {child_elem} while generating s-expression for node {current_node}')

            node_expr_dict[current_node_name] = current_node_expr

        return node_expr_dict


    def generate_raw_sexpr_unnamed_root(self, node_id: NodeId, declared_nodes: dict[NodeId, str]) -> RawSExprList:
        """With the given node_id as the root, output the graph reachable from it as an s-expression
        in the form of a let-rec with one line per node. Unnamed nodes get a new unique local name based on their id.
        The nodes in declared_nodes are output as their provided name (usually previously declared global node names)
        and not further expanded when encountered. If node_id is in declared_nodes, it is wrapped in a let-rec
        with a new local name. The dict declared_nodes is expected to use representative node ids of merged nodes."""

        node_names_to_use: dict[NodeId, str] = {self.merged_nodes.find(node_id): name
            for (name, node_id) in self.node_names.items()
            if self.merged_nodes.find(node_id) not in declared_nodes}

        repr_id = self.merged_nodes.find(node_id)

        if repr_id in declared_nodes:
            local_name = self.uniquify('_node_id_' + str(repr_id.raw))
            return ['let-rec', [local_name, declared_nodes[repr_id]], local_name]

        node_expr_defs: dict[str, RawSExprList] = self.generate_raw_sexpr_node_defs([repr_id], declared_nodes, node_names_to_use)

        output_expr: RawSExprList = ['let-rec']
        for (name, expr) in node_expr_defs.items():
            output_expr.append([name, expr])

        return_node_name = next(iter(node_expr_defs))

        output_expr.append(return_node_name)

        return output_expr

    def canonical_id_renaming(self) -> None:
        """Gives each node a new NodeId by first bypassing placeholders and then searching from the root nodes contained
        in source_nodes, inner_nodes, sink_nodes (in this order) depth-first and numbering nodes in the order they are
        encountered first. Note that the order in which expressions are added to the container influences this order.
        References to and names of unreachable nodes are removed.
        Used to check equivalence of containers (for testing purposes only)."""

        self.bypass_placeholders()

        id_mapping: dict[NodeId, NodeId] = dict()
        next_raw_id: int = 1

        visit_next: deque[NodeId] = deque(self.source_nodes.values())
        visit_next += self.inner_nodes.values()
        visit_next += self.sink_nodes

        logger.debug('visit_next %s', visit_next)

        visited: set[NodeId] = set()

        while len(visit_next) > 0:
            current_id: NodeId = visit_next.popleft()
            if current_id in visited:
                continue
            id_mapping[current_id] = NodeId(next_raw_id)
            next_raw_id += 1
            visited.add(current_id)

            current_node = self.nodes[current_id]
            signature = type(current_node).signature()
            collected_children: list[NodeId | LiteralType] = list()
            for index, field in enumerate(current_node.get_child_fields()):
                field_type: type = signature[index]
                if get_origin(field_type) is list:
                    collected_children += getattr(current_node, field.name)
                else:
                    collected_children.append(getattr(current_node, field.name))
            for child_elem in reversed(collected_children): # to achieve depth-first order
                if isinstance(child_elem, NodeId) and child_elem not in visited:
                        visit_next.appendleft(child_elem)

        logger.debug('id_mapping %s', id_mapping)

        new_nodes: dict[NodeId, PropertyIrNode] = dict()
        new_node_names: dict[str, NodeId] = dict()
        new_global_nodes: dict[str, NodeId] = dict()
        new_source_nodes: dict[str, NodeId] = dict()
        new_inner_nodes: dict[str, NodeId] = dict()
        new_sink_nodes: list[NodeId] = list()

        for old_id, new_id in id_mapping.items():
            new_nodes[new_id] = self.nodes[old_id]

        for old_str_id_dict, new_str_id_dict in [
                (self.node_names, new_node_names), (self.global_nodes, new_global_nodes), (self.source_nodes, new_source_nodes), (self.inner_nodes, new_inner_nodes)]:
            for node_name, old_id in old_str_id_dict.items():
                if old_id in id_mapping: # forget names of unreachable nodes
                    new_str_id_dict[node_name] = id_mapping[old_id]

        new_sink_nodes = [id_mapping[old_id] for old_id in self.sink_nodes]

        self.nodes = new_nodes
        self.node_names = new_node_names
        self.global_nodes = new_global_nodes
        self.source_nodes = new_source_nodes
        self.inner_nodes = new_inner_nodes
        self.sink_nodes = new_sink_nodes

        for declaration in self.declarations:
            if isinstance(declaration, SignalDeclaration | NamedExpressionDeclaration | UnnamedExpressionDeclaration):
                declaration.node_id = id_mapping[declaration.node_id]
            elif isinstance(declaration, NamedRecursiveDeclaration):
                for node_name, node_id in declaration.node_names.items():
                    declaration.node_names[node_name] = id_mapping[node_id]

        self.next_raw_id = next_raw_id

        for node in self.nodes.values():
            node.node_id = id_mapping[node.node_id]
            signature = type(node).signature()
            for index, field in enumerate(node.get_child_fields()):
                child_type: type = signature[index]
                if get_origin(child_type) is list:
                    children_list = getattr(node, field.name)
                    setattr(node, field.name, [id_mapping[old_id] for old_id in children_list.copy()])
                else:
                    child_node_id = getattr(node, field.name)
                    if isinstance(child_node_id, NodeId):
                        setattr(node, field.name, id_mapping[child_node_id])



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
            if node_name in self.global_nodes:
                graph.node(f'__NODENAME__{node_name}', label=f'<<U>{node_name}</U>>', shape='plain')
            else:
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
            logger.debug('START NODE %s', node)
            if isinstance(node, PlaceholderNode):
                representative_id = self.merged_nodes.find(node.node_id)
                if representative_id != node.node_id:
                    logger.debug('represented by %s - mark to delete', representative_id)
                    placeholder_ids_to_remove.append(node.node_id)
                logger.debug('SKIP PLACEHOLDER')
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
                        logger.debug('child node %s', child_node_representative)

                        child_representative_id: NodeId = child_node_representative.node_id
                        if child_representative_id != child_node_id:
                            children_list[child_list_index] = child_representative_id

                else: # if child type is not list
                    child_node_id = getattr(node, field.name)
                    if isinstance(child_node_id, LiteralType.__value__): # skip literal type
                        continue

                    child_node_representative = self[child_node_id]
                    logger.debug('child node %s', child_node_representative)

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









