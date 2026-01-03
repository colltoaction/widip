from __future__ import annotations
import contextvars
from typing import Any
from discopy import closed, monoidal


# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

RECURSION_REGISTRY: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("recursion", default={})

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

class Swap(closed.Box):
    def __init__(self, x: closed.Ty, y: closed.Ty):
        super().__init__("σ", x @ y, y @ x)
        self.draw_as_swap = True

Computation = closed.Category()
