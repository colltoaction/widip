from __future__ import annotations
from typing import Any
from itertools import batched
from functools import singledispatch
from discopy import symmetric

from .serialization import (
    Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node
)
from .presentation import CharacterStream

# Helper for building the event tree (Serialization Diagram) from HIF
def _build_event_tree(n: Any) -> symmetric.Diagram:
    """Recursively build SerializationTree from HIF nodes."""
    index, node_id = n
    data = CharacterStream.get_node_data(index, node_id)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")
    
    match kind:
        case "scalar":
            res = Scalar(tag, data["value"])
        case "sequence":
            items = [_build_event_tree(i) for i in CharacterStream.iterate(index, node_id)]
            inside = items[0] if items else symmetric.Id(Node)
            for item in items[1:]:
                 inside = inside >> item
            res = Sequence(inside, tag=tag)
        case "mapping":
            nodes = list(CharacterStream.iterate(index, node_id))
            pairs = []
            for key_nd, val_nd in batched(nodes, 2):
                key = _build_event_tree(key_nd)
                val = _build_event_tree(val_nd)
                pairs.append(key >> val)
            inside = pairs[0] if pairs else symmetric.Id(Node)
            for p in pairs[1:]:
                 inside = inside @ p
            res = Mapping(inside, tag=tag)
        case "alias":
            res = Alias(anchor)
        case "document":
            root = CharacterStream.step(index, node_id, "next")
            inside = _build_event_tree(root) if root else symmetric.Id(Node)
            res = Document(inside)
        case "stream":
            docs = [_build_event_tree(d) for d in CharacterStream.iterate(index, node_id)]
            inside = docs[0] if docs else symmetric.Id(Node)
            for d in docs[1:]:
                 inside = inside >> d
            res = Stream(inside)
        case _:
            raise ValueError(f"Unknown kind \"{kind}\" in HIF graph.")

    if anchor and kind != 'alias':
        return Anchor(anchor, res)
    return res

# ----------------------------------------------------------------------
# Functor implementation with Single Dispatch for input type handling
# ----------------------------------------------------------------------

@singledispatch
def _parse_impl(box) -> Any:
    """Dispatch logic for extracting source from input box/object."""
    # Default fallback: assume the box IS the source
    return box

@_parse_impl.register
def _parse_character_stream(box: CharacterStream) -> Any:
    return box.source

@_parse_impl.register
def _parse_box(box: symmetric.Box) -> Any:
    # Generic box fallback? Or should we check for .value?
    if hasattr(box, 'value'):
        return box.value
    return box # Treat box itself as source?

# Note: singledispatch dispatches on the *type of the first argument*.
# So parse(box) -> _parse_impl(box).

@symmetric.Diagram.from_callable(symmetric.Ty("CharacterStream"), Node)
def parse(box: Any) -> symmetric.Diagram:
    """Parse functor: Source (CharacterStream Box) -> Serialization Tree (Diagram)."""
    try:
        from nx_yaml import nx_compose_all
    except ImportError:
        raise ImportError("nx_yaml is required for YAML parsing.")

    source = _parse_impl(box)

    # 1. Parse source to HIF inputs
    incidences = nx_compose_all(source)
    
    # 2. Build Serialization Tree
    return _build_event_tree((0, incidences))
