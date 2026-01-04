import pytest
from discopy.symmetric import Box, Ty, Swap, Id

# Import from parse.py instead of hif.py
from computer.yaml.parse import to_hif, from_hif


@pytest.mark.parametrize("diagram", [
    Id(Ty('x')),
    Id(Ty()),
    Swap(Ty('x'), Ty('y')),
    Box('f', Ty('x'), Ty('y')),
    Box('f', Ty('x', 'y'), Ty('z')),
    Box('f', Ty('x'), Ty('y')) >> Box('g', Ty('y'), Ty('z')),
    Box('f', Ty('x'), Ty('y')) @ Box('g', Ty('z'), Ty('w')),
    Box('f', Ty('x'), Ty('y')) @ Id(Ty('z')),
])
def test_simple_cases(diagram):
    hg = diagram.to_hypergraph()
    data = to_hif(hg)
    hg_new = from_hif(data)
    assert hg == hg_new
