import pytest
from discopy import closed
from widip.computer import Partial, Language, specializer, compiler, compiler_generator, interpreter_box, specializer_box

def test_specializer_structure():
    assert isinstance(specializer, closed.Diagram)

def test_compiler_structure():
    source = "some_source"
    res = compiler(source)
    assert isinstance(res, Partial)
    assert res.arg == interpreter_box
    assert res.n == 1

def test_compiler_generator_structure():
    res = compiler_generator()
    assert isinstance(res, Partial)
    assert res.arg == specializer_box
    assert res.n == 1
