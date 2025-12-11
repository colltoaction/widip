from discopy.closed import Box, Ty, Diagram, Id

from .loader import repl_read as stream_diagram


def test_single_wires():
    a = Id("a")
    a0 = stream_diagram("a")
    a1 = stream_diagram("- a")
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a0 == a1

def test_id_boxes():
    a = Box("a", Ty(""), Ty(""))
    a0 = stream_diagram("!a")
    a1 = stream_diagram("!a :")
    a2 = stream_diagram("- !a")
    with Diagram.hypergraph_equality:
        assert a == a0
        assert a == a1
        assert a == a2

def test_the_empty_value():
    a0 = stream_diagram("")
    a1 = stream_diagram("\"\":")
    a2 = stream_diagram("\"\": a")
    a3 = stream_diagram("a:")
    a4 = stream_diagram("!a :")
    a5 = stream_diagram("\"\": !a")
    with Diagram.hypergraph_equality:
        assert a0 == Id()
        assert a1 == Id("")
        assert a2 == Box("map", Ty(""), Ty("a"))
        assert a3 == Id("a")
        assert a4 == Box("a", Ty(""), Ty(""))
        assert a5 == Box("map", Ty(""), Ty("")) >> a4
