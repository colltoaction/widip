from discopy.symmetric import Box, Ty
from nx_hif.readwrite import encode_hif_data
from widip.discopy_to_hif import discopy_to_hif


def test_discopy_to_hif():
    x, y, z = Ty('x'), Ty('y'), Ty('z')
    f = Box("f", x, y @ z, data={"foo": "bar"})
    g = Box("g", y @ z, x, data={"baz": 42})
    
    discopy_hg = (f >> g).to_hypergraph()
    hif_hg = discopy_to_hif(discopy_hg)
    data = encode_hif_data(hif_hg)
    assert data == {'incidences': [{'edge': 0, 'node': 0, 'attrs': {'key': 0, 'role': 'dom', 'index': 0}}, {'edge': 0, 'node': 1, 'attrs': {'key': 0, 'role': 'dom', 'index': 0}}, {'edge': 1, 'node': 1, 'attrs': {'key': 0, 'role': 'cod', 'index': 0}}, {'edge': 1, 'node': 2, 'attrs': {'key': 0, 'role': 'dom', 'index': 0}}, {'edge': 2, 'node': 1, 'attrs': {'key': 0, 'role': 'cod', 'index': 1}}, {'edge': 2, 'node': 2, 'attrs': {'key': 0, 'role': 'dom', 'index': 1}}, {'edge': 3, 'node': 0, 'attrs': {'key': 0, 'role': 'cod', 'index': 0}}, {'edge': 3, 'node': 2, 'attrs': {'key': 0, 'role': 'cod', 'index': 0}}], 'edges': [{'edge': 0, 'attrs': {'kind': 'spider'}}, {'edge': 1, 'attrs': {'kind': 'spider'}}, {'edge': 2, 'attrs': {'kind': 'spider'}}, {'edge': 3, 'attrs': {'kind': 'spider'}}], 'nodes': [{'node': 0, 'attrs': {'kind': 'boundary'}}, {'node': 1, 'attrs': {'foo': 'bar', 'kind': 'f'}}, {'node': 2, 'attrs': {'baz': 42, 'kind': 'g'}}]}
