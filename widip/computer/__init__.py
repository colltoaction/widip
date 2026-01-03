from __future__ import annotations
from typing import Any
from discopy import closed

# Symbols are represented by ℙ
class Language(closed.Ty):
    def __init__(self, name: str = "ℙ"):
        super().__init__(name)

class Data(closed.Box):
    def __init__(self, value: Any, dom: closed.Ty = Language(), cod: closed.Ty = Language()):
        self.value = value
        content = str(value) if value else "-"
        name = f"⌜{content if len(content) < 100 else content[:97] + '...'}⌝"
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name: str, dom: closed.Ty = Language(), cod: closed.Ty = Language(), args: Any = ()):
        super().__init__(name, dom, cod)
        self.args = args

class Discard(closed.Box):
    def __init__(self, x: closed.Ty):
        super().__init__("ε", x, closed.Ty())
        self.draw_as_spider = True

from .composition import Sequential, Parallel
from .combinators import Partial

# The Computer Category
Computation = closed.Category(Language, closed.Diagram)
