from __future__ import annotations
import sys
import contextvars
from collections.abc import Callable
from typing import Any
from discopy import closed, monoidal


# We use closed.Ty for the objects because they support exponential types (<<, >>)
# But we stay in a monoidal category for the arrows to simplify composition.
Language = closed.Ty("IO")

RECURSION_REGISTRY: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("recursion", default={})

class Eval(monoidal.Box):
    def __init__(self, base, exponent):
        super().__init__("eval", (exponent << base) @ base, exponent)
        self.base = base
        self.exponent = exponent

class Curry(monoidal.Box):
    def __init__(self, arg, n=1, left=True):
        if left:
             dom = arg.dom[:n]
             cod = arg.cod << arg.dom[n:]
        else:
             dom = arg.dom[len(arg.dom)-n:]
             cod = arg.cod >> arg.dom[:len(arg.dom)-n]
        super().__init__("curry", dom, cod)
        self.arg = arg
        self.n = n
        self.left = left

class Data(monoidal.Box):
    def __init__(self, dom=None, cod=None, value=None):
        if dom is None: dom = monoidal.Ty()
        if cod is None: cod = Language
        self.value = value
        name = f"⌜{value}⌝" if value else "⌜-⌝"
        super().__init__(name, dom, cod)

class Program(monoidal.Box):
    def __init__(self, name, args=(), dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)
        self.args = args

class Copy(monoidal.Box):
    def __init__(self, x, n=2):
        super().__init__(f"Copy({x}, {n})", x, x ** n)
        self.n = n

class Merge(monoidal.Box):
    def __init__(self, x, n=2):
        name = f"Merge({x}" + ("" if n == 2 else f", {n}") + ")"
        super().__init__(name, x ** n, x)
        self.n = n

class Exec(monoidal.Box):
    def __init__(self, dom, cod):
        super().__init__("exec", dom, cod)

class Discard(monoidal.Box):
    def __init__(self, x):
        super().__init__(f"Discard({x})", x, monoidal.Ty())

class Swap(monoidal.Box):
    def __init__(self, x, y):
        super().__init__(f"Swap({x}, {y})", x @ y, y @ x)

Computation = monoidal.Category()
