import pytest
from sexpr import IrContainer


@pytest.fixture
def container():
    return IrContainer()