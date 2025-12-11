from discopy.markov import Ty, Box, Hypergraph
from nx_hif.hif import hif_nodes, hif_edges, hif_edge_incidences, hif_node
from nx_hif.readwrite import encode_hif_data
import nx_yaml
import os
import glob
import pytest

from .representing import discopy_to_hif, hif_to_discopy

def test_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)

    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)

    nodes = list(hif_nodes(nx_h))
    assert 0 in nodes
    assert 1 in nodes

    # Verify node attributes instead of dom/cod edges
    assert hif_node(nx_h, 0).get('dom_ports') == [0]
    assert hif_node(nx_h, 1).get('cod_ports') == [0]

    edges = list(hif_edges(nx_h))
    # No explicit dom/cod edges
    assert "dom" not in edges
    assert "cod" not in edges

    # Look for box_0 (name might not be in ID)
    box_edge = [e for e in edges if str(e) == "box_0"][0]

    box_incs = list(hif_edge_incidences(nx_h, box_edge))
    assert len(box_incs) == 2

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

    # 0 is input x, 1 is internal y, 2 is output z
    assert hif_node(nx_h, 0).get('dom_ports') == [0]
    assert hif_node(nx_h, 2).get('cod_ports') == [0]
    # Node 1 is internal, should not have boundary ports
    assert 'dom_ports' not in hif_node(nx_h, 1)
    assert 'cod_ports' not in hif_node(nx_h, 1)

    edges = list(hif_edges(nx_h))
    assert "dom" not in edges
    assert "cod" not in edges

    f_edge = [e for e in edges if "box_0" in str(e)][0]
    g_edge = [e for e in edges if "box_1" in str(e)][0]

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

    # h_prime uses HIFOb, so Ty won't be strictly equal to h.dom (Ty(Ob))
    # Check names instead
    assert h_prime.dom.name == h.dom.name
    assert h_prime.cod.name == h.cod.name
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == h.boxes[0].name

    assert h_prime.n_spiders == h.n_spiders
    # Wires might differ if we have extra metadata or order,
    # but Hypergraph from_box wires are standard.
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

    assert h_prime.dom.name == h.dom.name
    assert h_prime.cod.name == h.cod.name
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

    assert h_prime.dom.name == h.dom.name
    assert h_prime.cod.name == h.cod.name
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

    assert h_prime.dom.name == h.dom.name
    assert h_prime.cod.name == h.cod.name
    assert len(h_prime.boxes) == 0
    assert h_prime.wires == h.wires

    nx_h_prime = discopy_to_hif(h_prime)
    assert encode_hif_data(nx_h) == encode_hif_data(nx_h_prime)

def find_yaml_files():
    files = []
    base_dirs = ['src/data', 'src/control']
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files_in_dir in os.walk(base):
            for file in files_in_dir:
                if file.endswith('.yaml'):
                    files.append(os.path.join(root, file))
    return files

@pytest.mark.parametrize("yaml_file", find_yaml_files())
def test_src_yaml_files(yaml_file):
    """
    Test loading static HIF files from YAML in src/data and src/control.
    """
    print(f"Testing {yaml_file}")
    with open(yaml_file, "r") as f:
        # nx_compose_all returns tuple of (nodes, edges, incidences) graphs?
        # Assuming hif_to_discopy takes this tuple structure (nx_hif convention).
        nx_h = nx_yaml.nx_compose_all(f)

    h_prime = hif_to_discopy(nx_h)

    assert isinstance(h_prime, Hypergraph)
    # n_spiders should match nodes count
    assert h_prime.n_spiders == len(list(hif_nodes(nx_h)))
    # boxes count should match edges count
    assert len(h_prime.boxes) == len(list(hif_edges(nx_h)))

    # Verify roundtrip back to HIF structure
    nx_h_prime = discopy_to_hif(h_prime)

    encoded = encode_hif_data(nx_h)
    encoded_prime = encode_hif_data(nx_h_prime)

    # Check counts match
    assert len(encoded['nodes']) == len(encoded_prime['nodes'])
    assert len(encoded['edges']) == len(encoded_prime['edges'])

    # Check incidences count
    # Allow some leniency if incidences with key=None vs key=... handled differently?
    # But ideally exact match.
    assert len(encoded['incidences']) == len(encoded_prime['incidences'])

    # Ensure incidence structure is somewhat preserved
    if len(encoded['incidences']) > 0:
        assert len(encoded_prime['incidences']) > 0

    # Ensure boundaries are empty unless specified
    # The files in src/data/control seem to be open graphs (string diagrams) usually?
    # But as syntax trees (implicit boundary).
    # If explicit boundary ports are absent in YAML, they should be empty in Hypergraph.
    # Note: hif_to_discopy reads 'dom_ports'/'cod_ports' attributes.
    # The YAMLs likely don't have them unless they were generated by this code.
    # So h_prime.dom and h_prime.cod will be empty types.
    # This is expected for "closed" diagrams or raw syntax trees.
