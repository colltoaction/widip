import pytest
from discopy import closed
from widip.computer import Partial, Language
from widip.computer.super import specializer, specializer_box, interpreter_box

def test_specializer_structure():
    # specializer is now a function decorated with @Program.as_diagram()
    assert callable(specializer)

def test_compiler_structure():
    from widip.computer.super import specializer_box, interpreter_box
    source = "some_source"
    res = Partial(interpreter_box, 1)
    assert isinstance(res, Partial)
    assert res.arg == interpreter_box
    assert res.n == 1

def test_compiler_generator_structure():
    from widip.computer.super import specializer_box
    res = Partial(specializer_box, 1)
    assert isinstance(res, Partial)
    assert res.arg == specializer_box
    assert res.n == 1
