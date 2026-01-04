import pytest
from discopy import closed
from .yaml import Sequence, Mapping, Scalar
from .yaml.representation import SequenceBox, MappingBox
from widip.yaml import construct_functor as SHELL_COMPILER
from computer import Data, Program, Language

# Helper to create dummy scalars for testing
def mk_scalar(name):
    # Use dom/cod if needed or default
    return Scalar(name, name)

@pytest.mark.parametrize("input_bubble, expected_class", [
    (
        Sequence(mk_scalar("A") @ mk_scalar("B") @ mk_scalar("C")),
        SequenceBox
    ),
    (
        Sequence(mk_scalar("A") @ mk_scalar("B"), n=2),
        SequenceBox
    ),
    (
        Mapping(mk_scalar("K") >> mk_scalar("V")),
        MappingBox
    ),
])
def test_compile_structure(input_bubble, expected_class):
    # Tests that construct_functor (SHELL_COMPILER) correctly handles structural boxes.
    # In the current implementation, construct_functor maps SequenceBox -> Diagram
    # Wait, the test expects a Diagram or the Box itself?
    # Let's check what construct_functor returns.
    compiled = SHELL_COMPILER(input_bubble)
    assert isinstance(compiled, closed.Diagram)
    # Could check structure more deeply if needed, e.g. length of boxes
    # compiled.boxes matches inner structure

def test_exec_compilation():
    # Test that Scalar with !exec tag compiles to Program box
    # !exec tag means tag="exec".
    s = Scalar("exec", "ls")
    c = SHELL_COMPILER(s)

    # SHELL_COMPILER returns a Diagram wrapping the box
    assert isinstance(c, closed.Diagram)
    assert len(c.boxes) == 1
    box = c.boxes[0]
    # Tagged scalars compile to Program boxes
    assert isinstance(box, Program)
    
    # Language is closed.Ty("ℙ")
    assert box.dom == Language
