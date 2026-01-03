from __future__ import annotations
from typing import Any, Iterator, Callable
from itertools import batched
from discopy import symmetric, monoidal
from .. import hif

# --- Serialization Tree Category (Structural) ---
Node = symmetric.Ty("Node")
SerializationTree = symmetric.Category(symmetric.Ty, symmetric.Diagram)

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


# --- Serialization Tree Builder ---

def load_serialization_tree(node: Any) -> symmetric.Diagram:
    """Entry point to convert HIF incidences to a structural SerializationTree."""
    return _incidences_to_node(0, node)

def _incidences_to_node(index: int, node: Any) -> symmetric.Diagram:
    """Recursively traverses HIF incidences to build a structural SerializationTree."""
    data = hif.get_node_data(index, node)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")
    
    match kind:
        case "scalar":
            res = Scalar(tag, data["value"])
            
        case "sequence":
            items = [_incidences_to_node(idx, nd) for idx, nd in hif.iterate(index, node)]
            if not items:
                inside = symmetric.Id(Node)
            else:
                inside = items[0]
                for item in items[1:]:
                    inside = inside >> item
            res = Sequence(inside, tag=tag)
            
        case "mapping":
            nodes = list(hif.iterate(index, node))
            pairs = []
            for key_nd, val_nd in batched(nodes, 2):
                key = _incidences_to_node(*key_nd)
                val = _incidences_to_node(*val_nd)
                pairs.append(key >> val)
            
            if not pairs:
                inside = symmetric.Id(Node)
            else:
                inside = pairs[0]
                for p in pairs[1:]:
                    inside = inside @ p
            res = Mapping(inside, tag=tag)
            
        case "alias":
            res = Alias(anchor)
            
        case "document":
            root = hif.step(index, node, "next")
            inside = _incidences_to_node(*root) if root else symmetric.Id(Node)
            res = Document(inside)
            
        case "stream":
            docs = [_incidences_to_node(idx, nd) for idx, nd in hif.iterate(index, node)]
            if not docs:
                inside = symmetric.Id(Node)
            else:
                inside = docs[0]
                for d in docs[1:]:
                    inside = inside >> d
            res = Stream(inside)
            
        case _:
             raise ValueError(f"Unknown kind \"{kind}\" in HIF graph.")

    if anchor and kind != 'alias':
        return Anchor(anchor, res)
    return res

# --- Anchor Registry ---
import contextvars
from contextlib import contextmanager

_ANCHORS: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("anchors", default={})

def get_anchor(name: str) -> Any | None:
    return _ANCHORS.get().get(name)

@contextmanager
def register_anchor(name: str, value: Any):
    old = _ANCHORS.get()
    token = _ANCHORS.set({**old, name: value})
    try:
        yield
    finally:
        _ANCHORS.reset(token)

def set_anchor(name: str, value: Any):
    _ANCHORS.set({**_ANCHORS.get(), name: value})
