from __future__ import annotations
from typing import Any, TypeVar, Generic
from discopy import closed, monoidal, symmetric
from . import yaml, loader

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

T = TypeVar("T")

class Data(closed.Box, Generic[T]):
    """Represents a data value in the computation."""
    def __init__(self, value: T, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty()):
        self.value = value
        content = str(value) if value else "-"
        name = f"⌜{content if len(content) < 100 else content[:97] + '...'}⌝"
        super().__init__(name, dom, cod)

class Program(closed.Box):
    """Represents an executable program or command."""
    def __init__(self, name: str, dom: closed.Ty = closed.Ty(), cod: closed.Ty = closed.Ty(), args: Any = ()):
        super().__init__(name, dom, cod)
        self.args = args

class Discard(closed.Box):
    """Represents the discard effect (ε)."""
    def __init__(self, x: closed.Ty):
        super().__init__("ε", x, closed.Ty())
        self.draw_as_spider = True

class Partial(closed.Box):
    """Represents partial application of a program."""
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        name = f"[{arg.name}]_{n}"
        dom, cod = arg.dom[n:], arg.cod
        super().__init__(name, dom, cod)


# --- Sequential and Parallel Boxes (Programs as Diagrams) ---
# Notation follows Dusko's paper: → for sequential, ⊗ for parallel

class Sequential(closed.Box):
    """Represents (→) sequential composition: A → B → C."""
    def __init__(self, left: closed.Diagram, right: closed.Diagram):
        self.left, self.right = left, right
        name = f"{left.dom}→{left.cod}→{right.cod}"
        super().__init__(name, left.dom, right.cod)


class Parallel(closed.Box):
    """Represents (⊗) tensor composition: A⊗U → B⊗V."""
    def __init__(self, top: closed.Diagram, bottom: closed.Diagram):
        self.top, self.bottom = top, bottom
        name = f"({top.dom}→{top.cod})⊗({bottom.dom}→{bottom.cod})"
        super().__init__(name, top.dom @ bottom.dom, top.cod @ bottom.cod)


Computation = closed.Category(closed.Ty, closed.Diagram)
