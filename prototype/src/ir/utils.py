from __future__ import annotations

from collections.abc import Collection, Iterable, Iterator, Mapping
from collections.abc import Set as AbstractSet

from typeguard import typechecked


@typechecked
class UnionFind[T]:
    """Used to keep track of merged nodes. Will only add nodes to the
    data structure when they get merged."""

    parents: dict[T, T]

    def __init__(self):
        self.parents =  {}

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
        if elem2 not in self.parents:
            self.parents[elem2] = elem2

        repr1: T = self.find(elem1)
        repr2: T = self.find(elem2)

        self.parents[repr1] = repr2

    def make_representative(self, elem: T):
        current_repr = self.find(elem)
        if current_repr == elem:
            return
        self.parents[current_repr] = elem
        self.parents[elem] = elem


def find_sccs[T](
    adjacency: Mapping[T, Collection[T]], roots: Iterable[T] | None = None
) -> list[list[T]]:
    """Iterative implementation of Tarjan's algorithm for finding strongly connected
    components (in reverse topological order).

    Missing keys in adjacency are considered sinks.
    Passing roots restricts the computation to vertices reachable from roots
    """
    components: list[list[T]] = []
    low: dict[T, int] = {}
    dfs: list[tuple[T, Iterator[T] | None, int]] = []
    stack: list[T] = []

    vertices = {}
    for vertex, successors in adjacency.items():
        vertices[vertex] = None
        for successor in successors:
            vertices[successor] = None

    if roots is None:
        roots = vertices

    for start in roots:
        if start in low:
            continue

        dfs.append((start, None, len(low)))

        while dfs:
            vertex, vertex_edges, num = dfs.pop()
            if vertex_edges is None:
                if vertex in low:
                    continue
                else:
                    low[vertex] = num
                    stack.append(vertex)
                vertex_edges = iter(adjacency.get(vertex, ()))

            try:
                next_edge = next(vertex_edges)
            except StopIteration:
                pass
            else:
                dfs.append((vertex, vertex_edges, num))
                dfs.append((next_edge, None, len(low)))
                continue

            val = low[vertex]
            for edge in adjacency.get(vertex, ()):
                if edge in low:
                    val = min(val, low[edge])

            low[vertex] = val

            if num == val:
                component: list[T] = []
                while stack:
                    component_vertex = stack.pop()
                    component.append(component_vertex)
                    low[component_vertex] = len(vertices)
                    if component_vertex == vertex:
                        break

                components.append(component)
    return components


def has_productive_cycle[T](
    adjacency: Mapping[T, Collection[T]], productive: AbstractSet[T]
) -> bool:
    """Tests whether the graph has directed cycle containing at least one productive
    vertex. Handles self-loops of productive vertices.
    """
    for scc in find_sccs(adjacency):
        if not any(v in productive for v in scc):
            continue

        if len(scc) == 1:
            singleton_vertex = scc[0]
            if singleton_vertex in adjacency.get(singleton_vertex, ()):
                return True
        else:
            return True

    return False
