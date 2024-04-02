from discopy.frobenius import Box, Ty, Diagram, Spider, Id
import pytest

from .files import files_f
from .shell import shell_f


def test_read():
    diagram = Box("read", Ty("examples/hello-world.yaml"), Ty())
    diagram = shell_f(diagram)
    with Diagram.hypergraph_equality:
        # TODO open then read YAML
        assert diagram == \
            Box("file://./examples/hello-world.yaml", Ty(""), Ty(""))

def test_eval():
    diagram = Box("eval", Ty("lambda x: x"), Ty())
    diagram = shell_f(diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Spider(0, 1, Ty("lambda x: x")) >> \
            Box("tag:yaml.org,2002:python/eval", Ty("lambda x: x"), Ty(""))

def test_print():
    diagram = Box("print", Ty("something to print"), Ty("something to print"))
    closed_diagram = Spider(0, 1, Ty("something to print")) >> diagram
    with Diagram.hypergraph_equality:
        diagram = shell_f(diagram)
        assert diagram == \
            Spider(0, 1, Ty("something to print")) >> \
            Box("tag:yaml.org,2002:python/print", Ty("something to print"), Ty())

        closed_diagram = shell_f(closed_diagram)
        assert closed_diagram == diagram

@pytest.mark.skip(reason="shell reads YAML from stdin")
def test_shell_to_py_shell():
    shell_d = files_f(Box("file://./bin/yaml/shell.yaml", Ty(), Ty()))
    rep_d = files_f(Box("file://./bin/py/rep.yaml", Ty(), Ty()))
    shell_d.draw()
    diagram = shell_f(shell_d)
    rep_d.draw()
    diagram.draw()
    with Diagram.hypergraph_equality:
        assert diagram == \
            Id("") @ Spider(0, 1, Ty("something to print")) >> \
            Box("tag:yaml.org,2002:python/print", Ty("") @ Ty("something to print"), Ty(""))
