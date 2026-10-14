from ir import UnionFind
from ir.utils import find_sccs, has_productive_cycle


def test_union_find():

    uf = UnionFind[int]()

    assert uf.find(1) == 1
    assert uf.find(2) == 2

    uf.union(1, 2)

    assert uf.find(1) == uf.find(2)
    assert uf.find(1) in [1,2]

    uf.union(1, 3)
    assert all(uf.find(value) == uf.find(3) for value in [1,2,3])
    assert uf.find(3) in [1,2,3]

    uf.union(1, 4)
    uf.union(1, 3)
    assert all(uf.find(value) == uf.find(3) for value in [1,2,3,4])
    assert uf.find(4) in [1,2,3,4]

    uf.union(6, 8)
    assert uf.find(6) == uf.find(8)
    assert uf.find(6) in [6,8]

    uf.union(7, 8)
    assert all(uf.find(value) == uf.find(8) for value in [6,7,8])
    assert uf.find(6) in [6,7,8]

    uf.make_representative(7)
    assert all(uf.find(value) == 7 for value in [6,7,8])
    uf.make_representative(8)
    assert all(uf.find(value) == 8 for value in [6,7,8])

    assert all(uf.find(value) == uf.find(3) for value in [1,2,3,4])
    assert uf.find(3) in [1,2,3,4]

    uf.union(4, 8)

    assert all(uf.find(value) == uf.find(3) for value in [1,2,3,4,6,7,8])
    assert uf.find(3) in [1,2,3,4,6,7,8]

    assert uf.find(15) == 15


def test_find_sccs_empty_and_singleton():
    assert find_sccs({}) == []
    assert find_sccs({0: []}) == [[0]]
    assert find_sccs({0: [0]}) == [[0]]


def test_find_sccs_reverse_topological_order():
    # {0, 1} -> {2, 3} -> {4} where 4 is an implicit sink.
    adjacency = {0: [1, 1, 4], 1: [0, 2], 2: [3, 4], 3: [2]}
    assert [sorted(scc) for scc in find_sccs(adjacency)] == [[4], [2, 3], [0, 1]]


def test_find_sccs_external_roots():
    components = find_sccs({0: [], 1: [0]}, [2, 3, 0, 1])
    assert sorted(components) == [[0], [1], [2], [3]]
    assert components.index([0]) < components.index([1])


def test_has_productive_cycle_empty_and_acyclic():
    assert not has_productive_cycle({}, set())
    assert not has_productive_cycle({}, {0})
    assert not has_productive_cycle({0: []}, {0})
    assert not has_productive_cycle({0: [1]}, {0, 1})


def test_has_productive_cycle_self_loop():
    adjacency = {0: [0, 1]}
    assert has_productive_cycle(adjacency, {0})
    assert not has_productive_cycle(adjacency, set())
    assert not has_productive_cycle(adjacency, {1})


def test_has_productive_cycle_scc():
    # 0 -> 1 <-> 2 -> 3
    adjacency = {0: [1], 1: [2], 2: [1, 3]}
    assert not has_productive_cycle(adjacency, {0})
    assert not has_productive_cycle(adjacency, {3})
    assert has_productive_cycle(adjacency, {1})


def test_has_productive_cycle_disconnected():
    adjacency = {0: [1], 1: [0], 2: [3], 3: [2]}
    assert sorted(sorted(scc) for scc in find_sccs(adjacency)) == [[0, 1], [2, 3]]
    assert has_productive_cycle(adjacency, {0})
    assert has_productive_cycle(adjacency, {2})
    assert not has_productive_cycle(adjacency, {4})
