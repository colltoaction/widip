import pathlib
import yaml
from discopy.frobenius import Box, Ty, Spider, Diagram, Id, Functor, Category, Hypergraph as H
from discopy import python

from bin.py.files import dir_diagram


def test_dir():
    diagram = dir_diagram(pathlib.Path("src/data/nat"))
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("nat", Ty(""), Ty("")) \
            >> Box("plus", Ty(""), Ty(""))