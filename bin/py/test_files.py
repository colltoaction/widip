from discopy.frobenius import Box, Ty, Diagram
import pytest

from .shell import shell_f


@pytest.mark.skip(reason="TODO stable test dir")
def test_dir():
    dir_diagram = Box("read", Ty("src/data/nat"), Ty())
    diagram = shell_f(dir_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("nat", Ty(""), Ty("")) \
            >> Box("plus", Ty(""), Ty(""))

def test_file():
    file_diagram = Box("read", Ty("src/data/nat.yaml"), Ty())
    diagram = shell_f(file_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("0", Ty(), Ty("nat")) \
            @ Box("succ", Ty("nat"), Ty("nat"))