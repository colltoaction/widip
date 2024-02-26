import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from files import compose_graph_file
from composing import compose_entry

u = Ty("unit")


def test_monoid():
    diagram = compose_graph_file(pathlib.Path("src/yaml/data/monoid.yaml"))
    with Diagram.hypergraph_equality:
        assert diagram == Box("unit", Ty(), Ty("")) @ Box("product", Ty("") @ Ty(""), Ty(""))
