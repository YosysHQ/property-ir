import pytest
from sexpr import IrContainer


@pytest.fixture
def container():
    container = IrContainer()
    container.global_nodes = {
        'a': container.add_node_by_kwargs(Signal, name='a'),
    }
