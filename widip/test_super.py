import pytest
from discopy import closed
from widip.super import specializer, compiler, compiler_generator, interpreter_box, specializer_box
from widip.computer import Partial, Language

def test_specializer_structure():
    # specializer is a Diagram (because of the decorator), so it's not callable as a python function with arbitrary args
    # to perform logic. It is a Diagram structure.
    # To test the logic, we should probably look at what I implemented as `compiler` or `_specializer_impl`
    # or how `specializer` is used.

    # In my implementation of `widip/super.py`, `specializer` is a decorated function that returns a Diagram.
    # But `compiler` uses `_specializer_impl` which returns a Partial box.

    # If the test wants to verify "specializer" logic, it should use the logic function.
    # But `specializer` symbol imported is the Diagram generator.

    # Actually, `specializer` is the Diagram object?
    # No, `from_callable` returns a function that generates a diagram?
    # Wait, in DisCoPy, `from_callable` returns a decorator.
    # The decorated function returns a Hypergraph (or Diagram).

    # If I call `specializer(x, y)`, it constructs a diagram where x and y are inputs.
    # But `x` and `y` must be Diagrams/Spiders.

    # "Diagram object is not callable" error means `specializer` IS a Diagram object.
    # Why?
    # Because `from_callable` EXECUTES the function immediately to build the diagram if no args are supplied?
    # No, `from_callable(dom, cod)(func)` returns a `Diagram` (or Hypergraph converted to Diagram).

    # Ah! `from_callable` doesn't return a factory function. It returns the Diagram!
    # "The arguments passed to it are the input wires".
    # It runs the function ONCE with symbolic inputs to trace it and build the diagram.

    # So `specializer` IS a `closed.Diagram`.
    assert isinstance(specializer, closed.Diagram)

    # So we cannot call it like `specializer(diag, arg)`.
    # That explains the error.

    # The "logic" of specialization is implemented in `compiler` function and `compiler_generator`.

def test_compiler_structure():
    # compiler is a python function in my implementation
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
