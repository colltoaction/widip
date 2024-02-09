import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id

from loader import HypergraphLoader

def test_bool():
    d = Box("true", Ty(), Ty()) @ \
        Box("false", Ty(), Ty())
    t = yaml.compose(open("src/yaml/data/bool.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d

def test_maybe():
    d = Box("a", Ty(), Ty("just")) @ \
        Id(Ty("nothing"))
    t = yaml.compose(open("src/yaml/data/maybe.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d

def test_either():
    d = Box("a", Ty(), Ty("left")) @ \
        Box("b", Ty(), Ty("right"))
    t = yaml.compose(open("src/yaml/data/either.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d

def test_single_wires():
    a = Id(Ty("a"))
    a0 = yaml.compose("a", Loader=HypergraphLoader)
    a1 = yaml.compose("a:", Loader=HypergraphLoader)
    a2 = yaml.compose("- a", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0.to_diagram()
        assert a0.to_diagram() == a1.to_diagram()
        assert a1.to_diagram() == a2.to_diagram()

def test_single_boxes():
    a = Box("a", Ty(), Ty())
    a0 = yaml.compose("!a", Loader=HypergraphLoader)
    a1 = yaml.compose("!a :", Loader=HypergraphLoader)
    a2 = yaml.compose("- !a", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0.to_diagram()
        assert a0.to_diagram() == a1.to_diagram()
        assert a1.to_diagram() == a2.to_diagram()
