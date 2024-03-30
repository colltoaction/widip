from discopy.frobenius import Box, Ty, Diagram

from bin.py.files import files_f

u = Ty("unit")
m = Ty("monoid")


def test_monoid():
    diagram = files_f(Box("file://./src/data/monoid.yaml", Ty(), Ty()))
    with Diagram.hypergraph_equality:
        assert diagram == Box("unit", Ty(), Ty("")) @ Box("product", Ty("") @ Ty(""), Ty(""))
