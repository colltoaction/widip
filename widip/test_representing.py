from discopy.markov import Ty, Box, Hypergraph
from nx_yaml import nx_serialize_all, nx_compose_all
import os
import pytest

from .representing import discopy_to_hif, hif_to_discopy

def test_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)

    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)

    # Simple check that we got a graph tuple
    assert isinstance(nx_h, tuple)
    assert len(nx_h) == 3

def test_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)

    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)

    assert isinstance(nx_h, tuple)
    assert len(nx_h) == 3

def test_roundtrip_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)
    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert len(h_prime.dom) == 0
    assert len(h_prime.cod) == 0
    assert len(h_prime.boxes) == len(h.boxes)
    assert h_prime.boxes[0].name == h.boxes[0].name

    assert h_prime.n_spiders == h.n_spiders
    assert h_prime.wires[1] == h.wires[1]

def test_roundtrip_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)
    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert len(h_prime.dom) == 0
    assert len(h_prime.cod) == 0
    assert len(h_prime.boxes) == 2
    assert h_prime.wires[1] == h.wires[1]

def test_roundtrip_tensor():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, x)
    g = Box('g', y, y)
    h = Hypergraph.from_box(f) @ Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert len(h_prime.dom) == 0
    assert len(h_prime.cod) == 0
    assert len(h_prime.boxes) == 2

def test_roundtrip_identity():
    x = Ty('x')
    h = Hypergraph(x, x, [], ((0,), (), (0,)), (x,))

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    assert len(h_prime.dom) == 0
    assert len(h_prime.cod) == 0
    assert len(h_prime.boxes) == 0
    assert h_prime.wires[1] == h.wires[1]

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
    print(f"Testing {yaml_file}")
    with open(yaml_file, "r") as f:
        nx_h = nx_compose_all(f)

    h_prime = hif_to_discopy(nx_h)
    nx_h_prime = discopy_to_hif(h_prime)

    yaml_orig = nx_serialize_all(nx_h)
    yaml_prime = nx_serialize_all(nx_h_prime)

    assert yaml_orig == yaml_prime
