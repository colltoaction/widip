import yaml

from discopy.frobenius import Box, Ty, Diagram, Spider, Id, Spider

from loader import HypergraphLoader


u = Ty("unit")
m = Ty("monoid")

def test_single_wires():
    a = Id("a")
    a0 = yaml.compose("a", Loader=HypergraphLoader)
    a1 = yaml.compose("- a", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a0 == a1

def test_id_boxes():
    a = Box("a", Ty(""), Ty(""))
    a0 = yaml.compose("!a", Loader=HypergraphLoader)
    a1 = yaml.compose("!a :", Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert a0 == a
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
        assert a1 == Id("")
        assert a2 == Id("") @ Id("a")
        assert a3 == Id("a")
        assert a4 == Box("a", Ty(""), Ty(""))
        assert a5 == a4

def test_bool():
    d = Id("true") @ Id("false")
    t = yaml.compose(open("src/data/bool.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d

def test_monoid():
    d = Box(u.name, Ty(), m) @ Box("product", m @ m, m)
    t = yaml.compose(open("src/data/monoid.yaml"), Loader=HypergraphLoader)
    with Diagram.hypergraph_equality:
        assert t == d
