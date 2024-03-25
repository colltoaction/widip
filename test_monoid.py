from discopy.frobenius import Box, Ty, Diagram

from bin.py.files import files_f

u = Ty("unit")
m = Ty("monoid")


def test_monoid():
    diagram = files_f(Box("src/data/monoid.yaml", Ty(), Ty()))
    # TODO (unit@unit);product
    with Diagram.hypergraph_equality:
        assert diagram == Box(u.name, Ty(), m) @ Box("product", m @ m, m)
