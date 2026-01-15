import pytest
from sexpr import IrContainer


@pytest.fixture
def container():
    container = IrContainer()
    container.add_signal_node('a')
    container.add_signal_node('b')
    container.add_signal_node('c')
    container.add_signal_node('d')
    return container