import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Swap

from loader import HypergraphLoader

u = Ty("unit")
m = Ty("monoid")

def test_single_wires():
    a = Id(Ty("a"))
    a0 = yaml.compose("a", Loader=HypergraphLoader)
    a1 = yaml.compose("- a", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a0 == a1

def test_id_boxes():
    a = Spider(0, 1, Ty("")) >> Box("a", Ty(""), Ty(""))
    a0 = yaml.compose("!a", Loader=HypergraphLoader)
    a1 = yaml.compose("!a :", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a0 == a1

def test_boxes_with_empty_domain_and_codomain():
    a = Box("a", Ty(""), Ty(""))
    a0 = yaml.compose("- !a", Loader=HypergraphLoader)
    a1 = yaml.compose("\"\": !a", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a0 == a1

def test_the_empty_value():
    a0 = yaml.compose("", Loader=HypergraphLoader)
    a1 = yaml.compose("\"\":", Loader=HypergraphLoader)
    a2 = yaml.compose("\"\": a", Loader=HypergraphLoader)
    a3 = yaml.compose("a:", Loader=HypergraphLoader)
    a4 = yaml.compose("\"\": !a", Loader=HypergraphLoader)
    a5 = yaml.compose("!a :", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a0 == None
        assert a1 == Id(Ty(""))
        assert a2 == Id(Ty("a"))
        assert a3 == Id(Ty("a"))
        assert a4 == Box("a", Ty(""), Ty(""))
        assert a5 == Spider(0, 1, Ty("")) >> Box("a", Ty(""), Ty(""))

def test_bool():
    d = Id("true") @ Id("false")
    t = yaml.compose(open("src/yaml/data/bool.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d

def test_maybe():
    d = Box("just", Ty("a"), Ty("")) @ \
        Box("nothing", Ty(), Ty(""))
    t = yaml.compose(open("src/yaml/data/maybe.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d

def test_either():
    d = Box("left", Ty("a"), Ty("")) @ \
        Box("right", Ty("b"), Ty(""))
    t = yaml.compose(open("src/yaml/data/either.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d

def test_monoid():
    d = Box(u.name, Ty(), m) @ Box("product", m @ m, m)
    t = yaml.compose(open("src/yaml/data/monoid.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d
