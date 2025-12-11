from nx_yaml import nx_compose_all, nx_serialize_all
from discopy.markov import Hypergraph
from widip.representing import discopy_to_hif, hif_to_discopy
from widip.loader import repl_read
import pytest

# Example YAML structure (mock)
YAML_CONTENT = """
foo:
    - bar
    - baz
"""

def test_bidirectional_roundtrip():
    # 1. Parse YAML to HIF
    hif_graph = nx_compose_all(YAML_CONTENT)

    # 2. Convert HIF to DisCoPy Hypergraph
    hypergraph = hif_to_discopy(hif_graph)
    assert isinstance(hypergraph, Hypergraph)

    # 3. Convert back to HIF
    hif_graph_back = discopy_to_hif(hypergraph)

    # 4. Serialize back to YAML
    yaml_output = nx_serialize_all(hif_graph_back)

    # Verify basics
    assert "foo" in yaml_output
    assert "bar" in yaml_output
    assert "baz" in yaml_output

def test_loader_usage():
    # Test if loader can produce a Hypergraph from a simple YAML stream

    # Simple scalar
    yaml_scalar = """
!int 42
"""
    # nx_compose_all expects stream.
    # repl_read takes a stream.

    # If we pass a string, nx_compose_all usually handles it (via yaml.safe_load_all or similar).
    # But let's check repl_read impl: incidences = nx_compose_all(stream)

    diagram = repl_read(yaml_scalar)
    assert isinstance(diagram, Hypergraph)
    # Check if it has the right boxes
    # Scalar loader produces Box("⌜−⌝", Ty(v), ...) or Box("G", ...)
    # !int 42 -> tag="int", value="42" (as string or int)

    assert len(diagram.boxes) > 0
    # box name should be "G" if tag is present, or "⌜−⌝" if just value.
    # !int 42 -> tag=int, value=42.
    # load_scalar: if tag and v: Box("G", ...)

    assert diagram.boxes[0].name == "G"

def test_loader_sequence():
    yaml_seq = """
- !x A
- !y B
"""
    diagram = repl_read(yaml_seq)
    assert isinstance(diagram, Hypergraph)
    # Sequence loader composes elements.
    # Should have boxes for A and B.
    # !x A -> Box("G", ...)

    # We expect 2 main content boxes plus gluing logic boxes (seq, eval, etc).

    # Just check if it's a Hypergraph and has boxes.
    assert len(diagram.boxes) > 0
