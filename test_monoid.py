import pathlib
from discopy.frobenius import Box, Ty, Diagram

from files import file_diagram

u = Ty("unit")
m = Ty("monoid")


def test_monoid():
    diagram = file_diagram(pathlib.Path("src/data/monoid.yaml").open())
    # TODO (unit@unit);product
    with Diagram.hypergraph_equality:
        assert diagram == Box(u.name, Ty(), m) @ Box("product", m @ m, m)
