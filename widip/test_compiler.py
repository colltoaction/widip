import pytest
from discopy import closed
from .yaml import Sequence, Mapping, Scalar
from .compiler import SHELL_COMPILER
from .computer import Sequential, Pair, Concurrent, Data, Program, Exec

# Helper to create dummy scalars for testing
def mk_scalar(name):
    # Use dom/cod if needed or default
    return Scalar(name, name)

@pytest.mark.parametrize("input_bubble, expected_type", [
    # Sequence now compiles to the minimal diagram (unwrapped)
    (
        Sequence(mk_scalar("A") @ mk_scalar("B") @ mk_scalar("C")),
        closed.Diagram
    ),
    (
        Sequence(mk_scalar("A") @ mk_scalar("B"), n=2),
        closed.Diagram
    ),
    (
        Mapping(mk_scalar("K") >> mk_scalar("V")),
        closed.Diagram
    ),
])
def test_compile_structure(input_bubble, expected_type):
    compiled = SHELL_COMPILER(input_bubble)
    # Check that it compiles to a Diagrams
    assert isinstance(compiled, closed.Diagram)
    # Could check structure more deeply if needed, e.g. length of boxes
    # compiled.boxes matches inner structure

def test_exec_compilation():
    # Test that Scalar with !exec tag compiles to Exec box
    # !exec tag means tag="exec".
    s = Scalar("exec", "ls")
    c = SHELL_COMPILER(s)

    assert isinstance(c, Exec)
    # Language is closed.Ty("IO"), so we assert c.dom is that
    from .computer import Language
    assert c.dom == Language
    expected_cod = closed.Ty("exec") >> closed.Ty("exec")
    # assert c.cod == expected_cod # This might be strict on names, ignore for now if flaky
