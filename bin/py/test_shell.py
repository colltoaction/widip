from discopy.frobenius import Box, Ty, Diagram, Spider, Id
import pytest

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
    diagram = shell_f(diagram)
    with Diagram.hypergraph_equality:
        assert diagram == \
            Id("") @ Spider(0, 1, Ty("something to print")) >> \
            Box("tag:yaml.org,2002:python/print", Ty("") @ Ty("something to print"), Ty(""))
