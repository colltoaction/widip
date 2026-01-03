import pytest
from discopy import closed
from .yaml import Sequence, Mapping, Scalar
from .computer import SHELL_COMPILER
from .computer import Data, Program, Language

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
    # SHELL_COMPILER takes (diagram, compiler, path)
    compiled = SHELL_COMPILER(input_bubble, SHELL_COMPILER, None)
    # Check that it compiles to a Diagrams
    assert isinstance(compiled, closed.Diagram)
    # Could check structure more deeply if needed, e.g. length of boxes
    # compiled.boxes matches inner structure

def test_exec_compilation():
    # Test that Scalar with !exec tag compiles to Program box
    # !exec tag means tag="exec".
    s = Scalar("exec", "ls")
    c = SHELL_COMPILER(s, SHELL_COMPILER, None)

    # SHELL_COMPILER returns a Diagram wrapping the box
    assert isinstance(c, closed.Diagram)
    assert len(c.boxes) == 1
    box = c.boxes[0]
    # Tagged scalars compile to Program boxes
    assert isinstance(box, Program)
    
    # Language is closed.Ty("ℙ")
    assert box.dom == Language
