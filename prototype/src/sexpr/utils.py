from __future__ import annotations
from typeguard import typechecked




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


