from __future__ import annotations
import contextvars
from contextlib import contextmanager
from typing import Any
from pathlib import Path
from discopy import closed, monoidal, symmetric
from . import yaml, loader

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

# Anchor registry using ContextVar for async safety
_ANCHORS: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("anchors", default={})

def get_anchor(name: str) -> Any | None:
    """Get a registered anchor by name."""
    return _ANCHORS.get().get(name)

@contextmanager
def register_anchor(name: str, value: Any):
    """Context manager to register an anchor and clean up after."""
    old = _ANCHORS.get().copy()
    new = old.copy()
    new[name] = value
    token = _ANCHORS.set(new)
    try:
        yield
    finally:
        _ANCHORS.reset(token)

def set_anchor(name: str, value: Any):
    """Set an anchor value (used during compilation)."""
    anchors = _ANCHORS.get().copy()
    anchors[name] = value
    _ANCHORS.set(anchors)

class Eval(closed.Eval):
    def __init__(self, base: closed.Ty, exponent: closed.Ty):
        super().__init__(base, exponent)

class Curry(closed.Curry):
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        super().__init__(arg, n, left)

class Data(closed.Box):
    def __init__(self, value: Any, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty()):
        self.value = value
        content = str(value) if value else "-"
        name = f"⌜{content if len(content) < 100 else content[:97] + '...'}⌝"
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name: str, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty(), args: Any = ()):
        super().__init__(name, dom, cod)
        self.args = args

class Copy(closed.Box):
    def __init__(self, x: closed.Ty, n: int = 2):
        super().__init__("Δ", x, x ** n)
        self.draw_as_spider = True

class Merge(closed.Box):
    def __init__(self, x: closed.Ty, n: int = 2):
        super().__init__("μ", x ** n, x)
        self.draw_as_spider = True

class Discard(closed.Box):
    def __init__(self, x: closed.Ty):
        super().__init__("ε", x, closed.Ty())
        self.draw_as_spider = True

class Partial(closed.Box):
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        name = f"Part({arg.name}, {n})"
        dom, cod = arg.dom[n:], arg.cod
        super().__init__(name, dom, cod)

class Swap(closed.Box):
    def __init__(self, x: closed.Ty, y: closed.Ty):
        super().__init__("σ", x @ y, y @ x)
        self.draw_as_swap = True


# --- Sequential and Parallel Boxes (Programs as Diagrams) ---
# Notation follows Dusko's paper: → for sequential, ⊗ for parallel

class Sequential(closed.Box):
    """Represents (→) sequential composition: A → B → C.
    
    From Dusko's paper Sec 2.2:
    (F→G) evaluates to the composite functions A {F} B {G} C
    """
    def __init__(self, left: closed.Diagram, right: closed.Diagram):
        self.left, self.right = left, right
        name = f"{left.dom}→{left.cod}→{right.cod}"
        super().__init__(name, left.dom, right.cod)


class Parallel(closed.Box):
    """Represents (⊗) tensor composition: A⊗U → B⊗V.
    
    From Dusko's paper Sec 2.2:
    (F ⊗ T) evaluates to the parallel tensor of functions
    """
    def __init__(self, top: closed.Diagram, bottom: closed.Diagram):
        self.top, self.bottom = top, bottom
        name = f"({top.dom}→{top.cod})⊗({bottom.dom}→{bottom.cod})"
        super().__init__(name, top.dom @ bottom.dom, top.cod @ bottom.cod)


Computation = closed.Category()
