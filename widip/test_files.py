from discopy.closed import Box, Ty, Diagram, Id
from discopy.hypergraph import Hypergraph

def assert_hg_eq(d1, d2):
    assert Hypergraph.from_diagram(d1) == Hypergraph.from_diagram(d2)

from .files import repl_read as stream_diagram


def test_single_wires():
    a = Id("a")
    a0 = stream_diagram("a")
    a1 = stream_diagram("- a")
    assert_hg_eq(a, a0)
    assert_hg_eq(a0, a1)

def test_id_boxes():
    a = Box("a", Ty(""), Ty(""))
    a0 = stream_diagram("!a")
    a1 = stream_diagram("!a :")
    a2 = stream_diagram("- !a")
    assert_hg_eq(a, a0)
    assert_hg_eq(a, a1)
    assert_hg_eq(a, a2)

def test_the_empty_value():
    a0 = stream_diagram("")
    a1 = stream_diagram("\"\":")
    a2 = stream_diagram("\"\": a")
    a3 = stream_diagram("a:")
    a4 = stream_diagram("!a :")
    a5 = stream_diagram("\"\": !a")
    assert_hg_eq(a0, Id())
    assert_hg_eq(a1, Id(""))
    assert_hg_eq(a2, Box("map", Ty(""), Ty("a")))
    assert_hg_eq(a3, Id("a"))
    assert_hg_eq(a4, Box("a", Ty(""), Ty("")))
    assert_hg_eq(a5, Box("map", Ty(""), Ty("")) >> a4)
