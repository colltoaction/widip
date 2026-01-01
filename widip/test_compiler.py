import pytest
from discopy import closed
from .yaml import Sequence, Mapping, Scalar
from .compiler import SHELL_COMPILER
from .computer import Sequential, Pair, Concurrent, Data, Program, Exec

# Helper to create dummy scalars for testing
def mk_scalar(name):
    return Scalar(name, name)

# def test_compile_structure(input_bubble, expected_box_type):
#     # We now use direct composition, so structure boxes (Sequential/Pair) are not produced.
#     pass

def test_exec_compilation():
    # Test that Scalar with !exec tag compiles to Exec box
    # !exec tag means tag="exec".
    s = Scalar("exec", "ls")
    c = SHELL_COMPILER(s)

    assert isinstance(c, Exec)
    # New logic forces IO domain/codomain
    io_ty = closed.Ty("IO")
    assert c.dom == io_ty
    assert c.cod == io_ty
