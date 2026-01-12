from sexpr import UnionFind


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
