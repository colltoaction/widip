from discopy.frobenius import Box, Ty, Diagram, Spider
import pytest

from .files import files_f


def test_file():
    file_diagram = Box("file://./src/data/nat.yaml", Ty(""), Ty(""))
    diagram = files_f(file_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("0", Ty(), Ty("")) \
            @ Box("succ", Ty(""), Ty(""))

def test_hello_world():
    file_diagram = Box("file://./examples/hello-world.yaml", Ty(""), Ty(""))
    diagram = files_f(file_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("print", Ty("Hello world!"), Ty("Hello world!"))

@pytest.mark.skip(reason="too hard for now")
def test_dir():
    dir_diagram = Box("file://./src/data/nat", Ty(""), Ty(""))
    diagram = files_f(dir_diagram)
    with Diagram.hypergraph_equality:
        diagram.draw()
        assert diagram == \
            Box("0", Ty(), Ty("")) \
            @ Box("succ", Ty(""), Ty("")) \
            >> Spider(2, 1, Ty(""))