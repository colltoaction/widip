from discopy.frobenius import Box, Ty, Diagram

from bin.py.shell import shell_f

u = Ty("unit")
m = Ty("monoid")


def test_monoid():
    diagram = shell_f(Box("read", Ty("src/data/monoid.yaml"), Ty()))
    # TODO (unit@unit);product
    with Diagram.hypergraph_equality:
        assert diagram == Box(u.name, Ty(), m) @ Box("product", m @ m, m)
