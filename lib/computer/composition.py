from __future__ import annotations
from discopy import closed

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
