import pytest
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Swap

from .files import stream_diagram, files_f

def test_monoid():
    diagram = files_f(Box("file://./src/data/monoid.yaml", Ty(), Ty()))
    with Diagram.hypergraph_equality:
        assert diagram == Box("unit", Ty(), Ty("")) @ Box("product", Ty("") @ Ty(""), Ty(""))

@pytest.mark.skip(reason="extensions such as functor")
def test_maybe():
    d = Box("just", Ty("a"), Ty("")) @ \
        Box("nothing", Ty(), Ty(""))
    t = stream_diagram(open("src/data/maybe.yaml"))
    with Diagram.hypergraph_equality:
        assert t == d

@pytest.mark.skip(reason="extensions such as functor")
def test_either():
    d = Box("left", Ty("a"), Ty("")) @ \
        Box("right", Ty("b"), Ty(""))
    t = stream_diagram(open("src/data/either.yaml"))
    with Diagram.hypergraph_equality:
        assert t == d
