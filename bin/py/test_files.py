from discopy.frobenius import Box, Ty, Diagram

from .files import files_f


def test_dir():
    dir_diagram = Box("src/data/nat", Ty(), Ty())
    diagram = files_f(dir_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("nat", Ty(""), Ty("")) \
            >> Box("plus", Ty(""), Ty(""))

def test_file():
    file_diagram = Box("src/data/nat.yaml", Ty(), Ty())
    diagram = files_f(file_diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Box("0", Ty(), Ty("")) \
            @ Box("succ", Ty(""), Ty(""))