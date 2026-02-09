import pytest
from pathlib import Path

from sexpr import IrContainer
from sexpr import parse_document
from sexpr.base import NodeId
from input_data import raw_sexpr1, raw_sexpr6_declare_rec, raw_sexpr7_declare_rec, raw_sexpr5
from helpers import wrap_in_document, wrap_multiple_statements_in_document


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

def test_node_renaming1():
    container1 = IrContainer()
    parse_document(wrap_in_document(raw_sexpr1), container1)

    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'before_renaming.png')

    container1.canonical_id_renaming()

    #container1.show_graph(output_directory / 'after_renaming.png')

    container2 = IrContainer()
    parse_document(wrap_in_document(raw_sexpr1), container2)
    container2.canonical_id_renaming()

    assert container1.sink_nodes[0] == NodeId(5)

    assert container1.global_nodes == container2.global_nodes
    assert container1.source_nodes == container2.source_nodes
    assert container1.sink_nodes == container2.sink_nodes
    assert container1.inner_nodes == container2.inner_nodes

    assert container1 == container2

def test_node_renaming2():
    container1 = IrContainer()
    parse_document(wrap_multiple_statements_in_document(
            [raw_sexpr6_declare_rec, raw_sexpr7_declare_rec, ['parse-sexpr', raw_sexpr5]]), container1)

    #container1.bypass_placeholders()
    #output_directory: Path = Path('./output')
    #container1.show_graph(output_directory / 'before_renaming.png')

    container1.canonical_id_renaming()

    #container1.show_graph(output_directory / 'after_renaming.png')

    container2 = IrContainer()
    parse_document(wrap_multiple_statements_in_document(
            [['parse-sexpr', raw_sexpr5], raw_sexpr6_declare_rec, raw_sexpr7_declare_rec]), container2)
    container2.canonical_id_renaming()

    assert container1.global_nodes == container2.global_nodes
    assert container1.source_nodes == container2.source_nodes
    assert container1.sink_nodes == container2.sink_nodes
    assert container1.inner_nodes == container2.inner_nodes

    assert container1 == container2


