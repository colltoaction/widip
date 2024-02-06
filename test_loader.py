import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id

from loader import HypergraphLoader

def test_bool():
    d = Box("true", Ty("true"), Ty("true")) @ \
        Box("false", Ty("false"), Ty("false"))
    t = yaml.compose(open("src/yaml/data/bool.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d

def test_maybe():
    d = Id(Ty("nothing")) @ \
        Box("a", Ty("just"), Ty("just"))
    t = yaml.compose(open("src/yaml/data/maybe.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d

def test_either():
    d = Box("a", Ty("left"), Ty("left")) @ \
        Box("b", Ty("right"), Ty("right"))
    t = yaml.compose(open("src/yaml/data/either.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t.to_diagram() == d
