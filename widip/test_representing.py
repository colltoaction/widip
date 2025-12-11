import os
import pytest

from discopy.markov import Ty, Box, Hypergraph
from nx_yaml import nx_serialize_all, nx_compose_all

from .representing import discopy_to_hif, hif_to_discopy


def test_roundtrip_simple_box():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, y)
    h = Hypergraph.from_box(f)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)
    nx_h_prime = discopy_to_hif(h_prime)

    assert nx_serialize_all(nx_h_prime) == nx_serialize_all(nx_h)


def test_roundtrip_composition():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box('f', x, y)
    g = Box('g', y, z)
    h = Hypergraph.from_box(f) >> Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)
    nx_h_prime = discopy_to_hif(h_prime)

    assert nx_serialize_all(nx_h_prime) == nx_serialize_all(nx_h)


def test_roundtrip_tensor():
    x, y = Ty('x'), Ty('y')
    f = Box('f', x, x)
    g = Box('g', y, y)
    h = Hypergraph.from_box(f) @ Hypergraph.from_box(g)

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)
    nx_h_prime = discopy_to_hif(h_prime)

    assert nx_serialize_all(nx_h_prime) == nx_serialize_all(nx_h)

def test_roundtrip_identity():
    x = Ty('x')
    h = Hypergraph(x, x, [], ((0,), (), (0,)), (x,))

    nx_h = discopy_to_hif(h)
    h_prime = hif_to_discopy(nx_h)

    nx_h_prime = discopy_to_hif(h_prime)
    assert nx_serialize_all(nx_h_prime) == nx_serialize_all(nx_h)

def find_yaml_files():
    files = []
    base_dirs = ['src/data', 'src/control']
    for base in base_dirs:
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

    # note that we re-serialize nx_h.
    # further changes to nx_yaml are necessary for equality with the original file
    assert nx_serialize_all(nx_h_prime) == nx_serialize_all(nx_h)
