import pytest
from discopy.closed import Box, Ty, Diagram, Id
from discopy.frobenius import Spider, Functor
from discopy.hypergraph import Hypergraph

_to_frobenius = Functor(lambda x: x, lambda f: f)

def assert_hg_eq(d1, d2):
    assert str(d1) == str(d2)

from .loader import repl_read as compose_all


id_box = lambda i: Box("!", Ty(i), Ty(i))

@pytest.mark.skip(reason="Discopy 1.2.2 incompatibility with hypergraph equality")
def test_tagged():
    a0 = compose_all("!a")
    a1 = compose_all("!a :")
    a2 = compose_all("--- !a")
    a3 = compose_all("--- !a\n--- !b")
    a4 = compose_all("\"\": !a")
    a5 = compose_all("? !a")
    assert_hg_eq(a0, Box("a", Ty(""), Ty("")))
    assert_hg_eq(a1, a0)
    assert_hg_eq(a2, a0)
    assert_hg_eq(a3, a0 @ Box("b", Ty(""), Ty("")))
    assert_hg_eq(a4, Box("map", Ty(""), Ty("a")) >> a0)
    assert_hg_eq(a5, a0)

@pytest.mark.skip(reason="Discopy 1.2.2 incompatibility with hypergraph equality")
def test_untagged():
    a0 = compose_all("")
    a1 = compose_all("\"\":")
    a2 = compose_all("\"\": a")
    a3 = compose_all("a:")
    a4 = compose_all("? a")
    assert_hg_eq(a0, Id())
    assert_hg_eq(a1, Id(""))
    assert_hg_eq(a2, Box("map", Ty(""), Ty("a")))
    assert_hg_eq(a3, Id("a"))
    assert_hg_eq(a4, a3)

@pytest.mark.skip(reason="Discopy 1.2.2 incompatibility with hypergraph equality")
def test_bool():
    d = Id("true") @ Id("false")
    t = compose_all(open("src/data/bool.yaml"))
    assert_hg_eq(t, d)

# u = Ty("unit")
# m = Ty("monoid")

# def test_monoid():
#     d = Box(u.name, Ty(), m) @ Box("product", m @ m, m)
#     t = compose_all(open("src/data/monoid.yaml"))
#     with Diagram.hypergraph_equality:
#         assert t == d
