import pytest
from discopy import closed
from .yaml import Sequence, Mapping, Scalar
from .compiler import SHELL_COMPILER
from .computer import Sequential, Pair, Concurrent, Data, Program, Exec, Eval

# Helper to create dummy scalars for testing
def mk_scalar(name):
    return Scalar(name, name)

@pytest.mark.parametrize("input_bubble, expected_box_type", [
    # Case 1: Sequence (List) -> Sequential
    (
        Sequence(mk_scalar("A") @ mk_scalar("B") @ mk_scalar("C")),
        Sequential
    ),

    # Case 2: Sequence (Pair, n=2) -> Pair
    (
        Sequence(mk_scalar("A") @ mk_scalar("B")),
        Pair
    ),

    # Case 3: Mapping -> Concurrent
    (
        Mapping(mk_scalar("K") @ mk_scalar("V")),
        Concurrent
    ),
])
def test_compile_structure(input_bubble, expected_box_type):
    compiled = SHELL_COMPILER(input_bubble)
    last_box = compiled.boxes[-1]
    assert isinstance(last_box, expected_box_type)
    inner_compiled = SHELL_COMPILER(input_bubble.args[0])
    assert compiled == inner_compiled >> last_box

def test_exec_compilation():
    # Test that Scalar with !exec tag compiles to Exec box
    # !exec tag means tag="exec".
    s = Scalar("exec", "ls")
    c = SHELL_COMPILER(s)

    assert isinstance(c, Exec)
    assert c.dom == closed.Ty("ls")
    expected_cod = closed.Ty("exec") >> closed.Ty("exec")
    assert c.cod == expected_cod

@pytest.mark.parametrize("tag, name", [
    ("cat", "file.txt"),
    ("echo", "hello"),
])
def test_program_compilation(tag, name):
    s = Scalar(tag, name)
    c = SHELL_COMPILER(s)
    # !cmd compiles to a Diagram involving Program and Eval
    assert isinstance(c, closed.Diagram)
    # It should contain a Program box with name=tag
    boxes = c.boxes
    programs = [b for b in boxes if isinstance(b, Program)]
    assert len(programs) >= 1
    assert programs[0].name == tag

    # It should contain Eval box (implied by execution)
    evals = [b for b in boxes if isinstance(b, Eval)]
    assert len(evals) >= 1

def test_tr_compilation():
    # Test the specific case from aoc2025
    s = Scalar("tr", "{LR, -+}")
    c = SHELL_COMPILER(s)
    assert isinstance(c, closed.Diagram)
    programs = [b for b in c.boxes if isinstance(b, Program)]
    assert len(programs) >= 1
    assert programs[0].name == "tr"
    # Check if arguments are handled?
    # Arguments usually flow via wires or Data boxes.
    # If "{LR, -+}" is the value of Scalar.
    # It might be in the domain type or a Data box.
    # Let's inspect domain
    # dom should reflect the input value
    assert c.dom == closed.Ty("{LR, -+}")
