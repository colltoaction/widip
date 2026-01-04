from __future__ import annotations
from typing import Any
from discopy import symmetric, monoidal

# --- The Node Graph Category (Semantic) ---
Node = symmetric.Ty("Node")

NodeGraph = symmetric.Category(Node, symmetric.Diagram)

# --- Semantic Boxes (Constructs) ---

class ScalarBox(symmetric.Box):
    def __init__(self, tag: str, value: Any, dom=Node, cod=Node):
        super().__init__("Scalar", dom, cod, data=(tag, value))
        self.tag, self.value = tag, value

class SequenceBox(symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node, **kwargs):
        super().__init__("Sequence", dom, cod, data=inside)
        self.tag, self.nested = tag, inside

class MappingBox(symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, tag="", dom=Node, cod=Node, **kwargs):
        super().__init__("Mapping", dom, cod, data=inside)
        self.tag, self.nested = tag, inside

class TitiBox(symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, **kwargs):
        super().__init__("Titi", Node, Node, data=inside)
        self.nested = inside

class AnchorBox(symmetric.Box):
    def __init__(self, name: str, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__(f"Anchor({name})", dom, cod, data=inside)
        self.name, self.nested = name, inside

class AliasBox(symmetric.Box):
    def __init__(self, name: str, dom=Node, cod=Node):
        super().__init__(name, dom, cod, data=name)
        self.name = name

class DocumentBox(symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__("Document", dom, cod, data=inside)
        self.nested = inside

class StreamBox(symmetric.Box):
    def __init__(self, inside: symmetric.Diagram, dom=Node, cod=Node):
        super().__init__("Stream", dom, cod, data=inside)
        self.nested = inside

# --- Factories ---

Scalar = lambda tag, val: ScalarBox(tag, val)
Sequence = lambda inside, tag="", *args, **kwargs: SequenceBox(inside, tag, *args, **kwargs)
Mapping = lambda inside, tag="": MappingBox(inside, tag)
Titi = lambda inside, *args, **kwargs: TitiBox(inside, **kwargs)
Anchor = lambda name, inside: AnchorBox(name, inside)
Alias = lambda name: AliasBox(name)
Document = lambda inside: DocumentBox(inside)
Stream = lambda inside: StreamBox(inside)

# --- Compose Implementation Functions ---

def comp_seq(box, compose): return Sequence(compose(box.nested), tag=box.tag)
def comp_map(box, compose): return Mapping(compose(box.nested), tag=box.tag)
def comp_doc(box, compose): return Document(compose(box.nested))
def comp_str(box, compose): return Stream(compose(box.nested))
def comp_anc(box, compose): return Anchor(box.name, compose(box.nested))
def comp_sca(box): return Scalar(box.data[0], box.data[1])
def comp_ali(box): return Alias(box.data)
