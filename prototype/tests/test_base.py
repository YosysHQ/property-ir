import pytest

from sexpr import IrContainer


def test_uniquify1(container):
    container.add_placeholder_node(name=container.uniquify('test_name'))
    container.add_placeholder_node(name=container.uniquify('test_name'))
    container.add_placeholder_node(name=container.uniquify('test_name'))
    container.add_placeholder_node(name=container.uniquify('test_name'))
    assert 'test_name' in container.node_names
    assert 'test_name_2' in container.node_names
    assert 'test_name_3' in container.node_names
    assert 'test_name_4' in container.node_names

def test_uniquify2(container):
    container.add_placeholder_node(name=container.uniquify('test'))
    container.add_placeholder_node(name=container.uniquify('test'))
    container.add_placeholder_node(name=container.uniquify('test'))
    container.add_placeholder_node(name=container.uniquify('test'))
    assert 'test' in container.node_names
    assert 'test_2' in container.node_names
    assert 'test_3' in container.node_names
    assert 'test_4' in container.node_names


def test_uniquify3(container):
    container.add_placeholder_node(name=container.uniquify('1111'))
    container.add_placeholder_node(name=container.uniquify('1111'))
    container.add_placeholder_node(name=container.uniquify('1111_2'))
    container.add_placeholder_node(name=container.uniquify('1111_3'))
    assert '1111' in container.node_names
    assert '1111_2' in container.node_names
    assert '1111_3' in container.node_names
    assert '1111_4' in container.node_names

def test_uniquify4(empty_container):
    container = empty_container
    container.add_placeholder_node(name=container.uniquify(''))
    container.add_placeholder_node(name=container.uniquify(''))
    assert len(container.node_names) == 2

def test_uniquify5(empty_container):
    container = empty_container
    container.add_placeholder_node(name=container.uniquify('1111_22'))
    container.add_placeholder_node(name=container.uniquify('1111_22'))
    container.add_placeholder_node(name=container.uniquify('1111_35'))
    container.add_placeholder_node(name=container.uniquify('1111_35'))
    assert len(container.node_names) == 4