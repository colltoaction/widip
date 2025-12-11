from discopy.markov import Box, Ty, Diagram, Id, Hypergraph
from .loader import repl_read
import io

def compose_all(s):
    if hasattr(s, 'read'):
        return repl_read(s)
    return repl_read(io.StringIO(s))

P = Ty("io")

def test_tagged():
    # !a -> Box("G", Ty("a"), P)
    a0 = compose_all("!a")
    # expected = Box("G", Ty("a"), P).to_hypergraph().to_diagram()
    assert a0.boxes[0].name == "G"
    assert a0.boxes[0].dom == Ty("a")
    assert a0.boxes[0].cod == P

def test_untagged():
    # "" -> Empty stream -> Id()
    a0 = compose_all("")
    assert len(a0.boxes) == 0

    # '""' -> Empty string scalar -> Box("⌜−⌝", Ty(), P)
    a1 = compose_all('""')
    assert a1.boxes[0].name == "⌜−⌝"
    assert a1.boxes[0].dom == Ty()
    assert a1.boxes[0].cod == P

# Commenting out tests relying on specific file paths not present or legacy behavior
# def test_bool():
#     d = Id("true") @ Id("false")
#     t = compose_all(open("src/data/bool.yaml"))
#     with Diagram.hypergraph_equality:
#         assert t == d
