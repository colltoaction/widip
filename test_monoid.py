import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from files import path_diagram
from composing import glue_diagrams

u = Ty("unit")
m = Ty("monoid")


def test_monoid():
    diagram = path_diagram(pathlib.Path("src/yaml/data/monoid.yaml"))
    # TODO (unit@unit);product
    with Diagram.hypergraph_equality:
        assert diagram == Box(u.name, Ty(), m) @ Box("product", m @ m, m)
