from discopy.markov import Ty, Box, Hypergraph
from .represent import encode_hif_data, read_hif_data

def test_roundtrip_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)

    # h = f.to_hypergraph()
    h = Hypergraph.from_box(f)

    nx_h = encode_hif_data(h)
    h_prime = read_hif_data(nx_h)

    # Assert equality
    # We might need to check attributes because equality of Hypergraphs depends on internal order.
    # But read_hif_data attempts to preserve order.

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == h.boxes[0].name
    assert h_prime.boxes[0].dom == h.boxes[0].dom
    assert h_prime.boxes[0].cod == h.boxes[0].cod

    assert h_prime.n_spiders == h.n_spiders
    assert h_prime.wires == h.wires

def test_roundtrip_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)

    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = encode_hif_data(h)
    h_prime = read_hif_data(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == f.name
    assert h_prime.boxes[1].name == g.name

    assert h_prime.n_spiders == h.n_spiders
    assert h_prime.wires == h.wires

def test_roundtrip_tensor():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, x)
    g = Box('g', y, y)

    h = Hypergraph.from_box(f) @ Hypergraph.from_box(g)

    nx_h = encode_hif_data(h)
    h_prime = read_hif_data(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == 2

    # Order of boxes in parallel composition might be preserved or not depending on implementation,
    # but Hypergraph usually preserves it.
    assert h_prime.boxes[0].name == f.name
    assert h_prime.boxes[1].name == g.name

    assert h_prime.wires == h.wires
