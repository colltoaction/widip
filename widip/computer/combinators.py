from __future__ import annotations
from discopy import closed

class Partial(closed.Box):
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        name = f"Part({arg.name}, {n})"
        dom, cod = arg.dom[n:], arg.cod
        super().__init__(name, dom, cod)
