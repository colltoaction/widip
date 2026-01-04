"""Futamura Projections - Super-Computer for meta-compilation."""

from discopy import closed
from . import Language, Program

# Two-argument Language type
Language2 = closed.Ty("ℙ", "ℙ")

# Core boxes
specializer_box = closed.Box("specializer", Language2, Language)
interpreter_box = closed.Box("interpreter", Language2, Language)

@Program.as_diagram()
def specializer(program, arg):
    """Partial evaluator / Specializer."""
    return specializer_box

@Program.as_diagram()
def interpreter(program, arg):
    """Interpreter for meta-compilation."""
    return interpreter_box
