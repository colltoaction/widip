from __future__ import annotations
from discopy import closed
from .computer import Program, Language, Partial

# --- Super-Computer Diagrams ---

@closed.Diagram.from_callable(Language @ Language, Language)
def specializer(program, arg):
    """Partial evaluator / Specializer diagram."""
    return Program("specializer")(program, arg)

@closed.Diagram.from_callable(Language @ Language, Language)
def interpreter(program, arg):
    """Interpreter diagram representation."""
    return Program("interpreter")(program, arg)

# Futamura's Projections
compiler = lambda program: Partial(interpreter, 1)(program)
compiler_generator = lambda: Partial(specializer, 1)(interpreter)
