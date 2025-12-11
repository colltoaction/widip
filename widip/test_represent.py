from discopy.markov import Ty, Box, Hypergraph
from nx_hif.hif import hif_nodes, hif_edges, hif_edge_incidences, hif_node_incidences, hif_edge
from networkx.utils import graphs_equal

from .represent import encode_hif_data, read_hif_data
from .loader import repl_read

def test_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)

    h = Hypergraph.from_box(f)

    nx_h = encode_hif_data(h)

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

def test_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)

    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = encode_hif_data(h)

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

def test_roundtrip_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)
    h = Hypergraph.from_box(f)

    nx_h = encode_hif_data(h)
    h_prime = read_hif_data(nx_h)

    assert h_prime.dom == h.dom
    assert h_prime.cod == h.cod
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == h.boxes[0].name

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
    assert len(h_prime.boxes) == 2
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
    assert h_prime.wires == h.wires
