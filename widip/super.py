from __future__ import annotations
from discopy import closed
from .computer import Program, Language, Partial

# --- Super-Computer Diagrams ---

@closed.Diagram.from_callable(Language @ Language, Language)
def specializer(program, arg):
    """Partial evaluator / Specializer diagram."""
    return closed.Box("specializer", Language @ Language, Language)(program, arg)

@closed.Diagram.from_callable(Language @ Language, Language)
def interpreter(program, arg):
    """Interpreter diagram representation."""
    return closed.Box("interpreter", Language @ Language, Language)(program, arg)

# Futamura's Projections
compiler = lambda program: Partial(interpreter, 1)(program)
compiler_generator = lambda: Partial(specializer, 1)(interpreter)
