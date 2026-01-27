import pytest
from sexpr import IrContainer
from sexpr.base import SignalDeclaration


@pytest.fixture
def container():
    container = IrContainer()
    signal_node1 = container.add_signal_node('a')
    signal_node2 = container.add_signal_node('b')
    signal_node3 = container.add_signal_node('c')
    signal_node4 = container.add_signal_node('d')
    container.add_declaration(SignalDeclaration('a', signal_node1.node_id))
    container.add_declaration(SignalDeclaration('b', signal_node2.node_id))
    container.add_declaration(SignalDeclaration('c', signal_node3.node_id))
    container.add_declaration(SignalDeclaration('d', signal_node4.node_id))
    return container


@pytest.fixture
def empty_container():
    container = IrContainer()
    return container
