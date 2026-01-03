from __future__ import annotations
from typing import Any
from discopy import symmetric, monoidal

# --- The Node Graph Category (Semantic) ---
Node = symmetric.Ty("Node")
NodeGraph = symmetric.Category(symmetric.Ty, symmetric.Diagram)

class Scalar(symmetric.Box):
    def __init__(self, tag: str, value: Any, dom=Node, cod=Node):
        super().__init__("Scalar", dom, cod)
        self.tag, self.value = tag, value

class Sequence(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.tag = tag

class Mapping(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.tag = tag

class Anchor(monoidal.Bubble, symmetric.Box):
    def __init__(self, name: str, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.name = name

class Alias(symmetric.Box):
    def __init__(self, name: str, dom=Node, cod=Node):
        super().__init__(name, dom, cod)
        self.name = name

class Document(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)

class Stream(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
