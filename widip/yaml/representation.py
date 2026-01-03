from __future__ import annotations
from typing import Any
from discopy import symmetric, monoidal

# --- The Node Graph Category (Semantic) ---
Node = symmetric.Ty("Node")

NodeGraph = symmetric.Category(Node, symmetric.Diagram)

# --- Semantic Boxes (Constructs) ---

class ScalarBox(symmetric.Box):
    def __init__(self, tag: str, value: Any, dom=Node, cod=Node):
        super().__init__("Scalar", dom, cod)
        self.tag, self.value = tag, value

class SequenceBox(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.tag = tag

class MappingBox(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.tag = tag

class AnchorBox(monoidal.Bubble, symmetric.Box):
    def __init__(self, name: str, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)
        self.name = name

class AliasBox(symmetric.Box):
    def __init__(self, name: str, dom=Node, cod=Node):
        super().__init__(name, dom, cod)
        self.name = name

class DocumentBox(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)

class StreamBox(monoidal.Bubble, symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(inside, dom, cod)


# --- Factories ---

def Scalar(tag: str, value: Any):
    return ScalarBox(tag, value)

def Sequence(inside: symmetric.Diagram, tag: str = ""):
    return SequenceBox(inside, tag)

def Mapping(inside: symmetric.Diagram, tag: str = ""):
    return MappingBox(inside, tag)

def Anchor(name: str, inside: symmetric.Diagram):
    return AnchorBox(name, inside)

def Alias(name: str):
    return AliasBox(name)

def Document(inside: symmetric.Diagram):
    return DocumentBox(inside)

def Stream(inside: symmetric.Diagram):
    return StreamBox(inside)
