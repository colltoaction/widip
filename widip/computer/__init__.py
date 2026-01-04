from __future__ import annotations
from discopy import closed

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

class Partial(closed.Box):
    """Higher-order box for partial application."""
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        # Manually construct closed.Ty to avoid monoidal fallback
        dom = closed.Ty(*[obj.name for obj in arg.dom[n:]])
        cod = closed.Ty(*[obj.name for obj in arg.cod])
        super().__init__(f"[{arg.name}]_{n}", dom, cod)

# --- Computer Boxes (Traceable factories) ---

def Data(value):
    @closed.Diagram.from_callable(closed.Ty(), Language)
    def diag():
        return closed.Box(f"⌜{value}⌝", closed.Ty(), Language, data=value)()
    return diag

def Program(name, args=()):
    @closed.Diagram.from_callable(Language, Language)
    def diag(x):
        return closed.Box(name, Language, Language, data=args)(x)
    return diag

def Discard():
    @closed.Diagram.from_callable(Language, closed.Ty())
    def diag(x):
        return closed.Box("ε", Language, closed.Ty(), draw_as_spider=True)(x)
    return diag

from .composition import Sequential, Parallel
Computation = closed.Category(closed.Ty, closed.Diagram)
