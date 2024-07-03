from discopy.frobenius import Box, Ty, Diagram, Spider, Id, Spider

from .loader import compose_all


id_box = lambda i: Box("!", Ty(i), Ty(i))

def test_tagged():
    a0 = compose_all("!a")
    a1 = compose_all("!a :")
    a2 = compose_all("--- !a")
    a3 = compose_all("--- !a\n--- !b")
    a4 = compose_all("\"\": !a")
    a5 = compose_all("? !a")
    with Diagram.hypergraph_equality:
        assert a0 == Box("a", Ty(""), Ty(""))
        assert a1 == a0
        assert a2 == a0
        assert a3 == a0 @ Box("b", Ty(""), Ty(""))
        assert a4 == Box("map", Ty(""), Ty("")) >> a0
        assert a5 == a0

def test_untagged():
    a0 = compose_all("")
    a1 = compose_all("\"\":")
    a2 = compose_all("\"\": a")
    a3 = compose_all("a:")
    a4 = compose_all("? a")
    with Diagram.hypergraph_equality:
        assert a0 == Id()
        assert a1 == Id("")
        assert a2 == Box("map", Ty(""), Ty("a"))
        assert a3 == Id("a")
        assert a4 == a3

def test_bool():
    d = Id("true") @ Id("false")
    t = compose_all(open("src/data/bool.yaml"))
    with Diagram.hypergraph_equality:
        assert t == d

# u = Ty("unit")
# m = Ty("monoid")

# def test_monoid():
#     d = Box(u.name, Ty(), m) @ Box("product", m @ m, m)
#     t = compose_all(open("src/data/monoid.yaml"))
#     with Diagram.hypergraph_equality:
#         assert t == d
