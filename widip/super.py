from __future__ import annotations
from discopy import closed
from .computer import Program, Language

# --- Super-Computer Primitives ---

class Partial(closed.Box):
    """Higher-order box for partial application."""
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        name = f"[{arg.name}]_{n}"
        dom, cod = arg.dom[n:], arg.cod
        super().__init__(name, dom, cod)

interpreter_box = Program("interpreter", Language ** 2, Language)
specializer_box = Program("specializer", Language ** 2, Language)

@closed.Diagram.from_callable(Language ** 2, Language)
def specializer(program, arg):
    """Partial evaluator / Specializer diagram."""
    return specializer_box(program, arg)

@closed.Diagram.from_callable(Language ** 2, Language)
def interpreter(program, arg):
    """Interpreter diagram representation."""
    return interpreter_box(program, arg)

# Futamura's Projections
compiler = lambda program: Partial(interpreter, 1)(program)
compiler_generator = lambda: Partial(specializer, 1)(interpreter)
