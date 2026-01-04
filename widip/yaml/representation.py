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

Scalar = lambda tag, val: ScalarBox(tag, val)
Sequence = lambda inside, tag="": SequenceBox(inside, tag)
Mapping = lambda inside, tag="": MappingBox(inside, tag)
Anchor = lambda name, inside: AnchorBox(name, inside)
Alias = lambda name: AliasBox(name)
Document = lambda inside: DocumentBox(inside)
Stream = lambda inside: StreamBox(inside)

# --- Compose Implementation Functions ---

def comp_seq(box, compose): return Sequence(compose(box.inside), tag=box.tag)
def comp_map(box, compose): return Mapping(compose(box.inside), tag=box.tag)
def comp_doc(box, compose): return Document(compose(box.inside))
def comp_str(box, compose): return Stream(compose(box.inside))
def comp_anc(box, compose): return Anchor(box.name, compose(box.inside))
def comp_sca(box): return Scalar(box.data[0], box.data[1])
def comp_ali(box): return Alias(box.data)
