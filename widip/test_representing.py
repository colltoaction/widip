from discopy.markov import Ty, Box, Hypergraph
from nx_hif.hif import hif_nodes, hif_edges, hif_edge_incidences
from nx_hif.readwrite import encode_hif_data

from .representing import discopy_to_hif, hif_to_discopy

def test_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)

    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)

    nodes = list(hif_nodes(nx_h))
    assert 0 in nodes
    assert 1 in nodes

    edges = list(hif_edges(nx_h))
    assert "dom" in edges
    assert "cod" in edges
    box_edge = [e for e in edges if str(e).startswith("box_0_f")][0]

    dom_incs = list(hif_edge_incidences(nx_h, "dom"))
    assert len(dom_incs) == 1
    assert dom_incs[0][1] == 0

    box_incs = list(hif_edge_incidences(nx_h, box_edge))
    assert len(box_incs) == 2

    cod_incs = list(hif_edge_incidences(nx_h, "cod"))
    assert len(cod_incs) == 1
    assert cod_incs[0][1] == 1

    encoded = encode_hif_data(nx_h)
    assert encoded['edges']
    assert encoded['incidences']

def test_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)

    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)

    nodes = list(hif_nodes(nx_h))
    assert 0 in nodes
    assert 1 in nodes
    assert 2 in nodes

    edges = list(hif_edges(nx_h))
    assert "dom" in edges
    assert "cod" in edges

    f_edge = [e for e in edges if "box_0_f" in str(e)][0]
    g_edge = [e for e in edges if "box_1_g" in str(e)][0]

    f_incs = list(hif_edge_incidences(nx_h, f_edge))
    g_incs = list(hif_edge_incidences(nx_h, g_edge))

    f_cod = [inc for inc in f_incs if inc[3]["role"] == "cod"][0]
    g_dom = [inc for inc in g_incs if inc[3]["role"] == "dom"][0]

    assert f_cod[1] == 1
    assert g_dom[1] == 1

    encoded = encode_hif_data(nx_h)
    assert encoded['edges']
    assert encoded['incidences']

def test_roundtrip_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)
    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == h.boxes[0].name

    assert h_prime.n_spiders == h.n_spiders
    assert h_prime.wires == h.wires

    nx_h_prime = discopy_to_hif(h_prime)
    encoded_orig = encode_hif_data(nx_h)
    encoded_prime = encode_hif_data(nx_h_prime)
    assert encoded_orig == encoded_prime


def test_roundtrip_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)
    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == 2
    assert h_prime.wires == h.wires

    nx_h_prime = discopy_to_hif(h_prime)
    assert encode_hif_data(nx_h) == encode_hif_data(nx_h_prime)

def test_roundtrip_tensor():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, x)
    g = Box('g', y, y)
    h = Hypergraph.from_box(f) @ Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == 2
    assert h_prime.wires == h.wires

    nx_h_prime = discopy_to_hif(h_prime)
    assert encode_hif_data(nx_h) == encode_hif_data(nx_h_prime)

def test_roundtrip_identity():
    x = Ty('x')
    # Identity wire: x -> x
    # 1 spider (0)
    # dom: [0], cod: [0]
    # boxes: []
    # wires must be tuples to satisfy Hypergraph.__init__ checks when summing
    h = Hypergraph(x, x, [], ((0,), (), (0,)), (x,))

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == 0
    assert h_prime.wires == h.wires
    assert h_prime.spider_types == h.spider_types

    nx_h_prime = discopy_to_hif(h_prime)
    assert encode_hif_data(nx_h) == encode_hif_data(nx_h_prime)
