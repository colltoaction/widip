from __future__ import annotations
from typing import Any
from itertools import batched
from functools import singledispatch
from discopy import symmetric

from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node
from . import presentation as pres
from .presentation import CharacterStream
from . import serialization as ser

# ----------------------------------------------------------------------
# Logic: HIF -> Presentation Box -> Serialization Diagram
# ----------------------------------------------------------------------

def _hif_to_presentation(n: Any) -> tuple[symmetric.Box, Any]:
    """Convert HIF node to Presentation Box and children iterator."""
    index, node_id = n
    data = hif_node(node_id, index)
    tag = (data.get("tag") or "")[1:]
    kind = data["kind"]
    anchor = data.get("anchor")
    
    match kind:
        case "scalar":
            return pres.Scalar(data["value"], tag, anchor), None
        case "sequence":
            return pres.Sequence(tag, anchor), _iterate(index, node_id)
        case "mapping":
            return pres.Mapping(tag, anchor), _iterate(index, node_id)
        case "alias":
            return pres.Alias(anchor), None
        case "document":
            return pres.Document(), _step(index, node_id, "next")
        case "stream":
            return pres.Stream(), _iterate(index, node_id)
        case _:
            raise ValueError(f"Unknown kind \"{kind}\" in HIF graph.")

def _step(index, node, key: str) -> tuple | None:
    incidences = tuple(hif_node_incidences(node, index, key=key))
    if not incidences:
        return None
    ((edge, _, _, _), ) = incidences
    start = tuple(hif_edge_incidences(node, edge, key="start"))
    if not start:
        return None
    ((_, neighbor, _, _), ) = start
    return (neighbor, node)

def _iterate(index, node):
    curr = _step(index, node, "next")
    while curr:
        yield curr
        curr = _step(curr[0], curr[1], "forward")

@singledispatch
def _to_serialization(box: symmetric.Box, inside: symmetric.Diagram) -> symmetric.Diagram:
    """Convert Presentation Box + Inside Diagram to Serialization Diagram."""
    raise NotImplementedError(f"No translation for {type(box)}")

@_to_serialization.register
def _(box: pres.Scalar, _):
    res = ser.Scalar(box.tag, box.value)
    if box.anchor:
        return ser.Anchor(box.anchor, res)
    return res

@_to_serialization.register
def _(box: pres.Sequence, inside):
    res = ser.Sequence(inside, tag=box.tag)
    if box.anchor:
        return ser.Anchor(box.anchor, res)
    return res

@_to_serialization.register
def _(box: pres.Mapping, inside):
    res = ser.Mapping(inside, tag=box.tag)
    if box.anchor:
        return ser.Anchor(box.anchor, res)
    return res

@_to_serialization.register
def _(box: pres.Alias, _):
    return ser.Alias(box.anchor)

@_to_serialization.register
def _(box: pres.Document, inside):
    return ser.Document(inside)

@_to_serialization.register
def _(box: pres.Stream, inside):
    return ser.Stream(inside)


def _build_event_tree(n: Any) -> symmetric.Diagram:
    """Recursively build SerializationTree from HIF nodes."""
    box, children_iter = _hif_to_presentation(n)
    
    inside = symmetric.Id(ser.Node)
    
    if isinstance(box, pres.Document):
        # Document has single child (root)
        if children_iter:
            inside = _build_event_tree(children_iter)
    elif isinstance(box, pres.Mapping):
         # Mapping children come in pairs (key, value)
         nodes = list(children_iter)
         pairs = []
         for key_nd, val_nd in batched(nodes, 2):
             k = _build_event_tree(key_nd)
             v = _build_event_tree(val_nd)
             pairs.append(k >> v)
         if pairs:
             inside = pairs[0]
             for p in pairs[1:]:
                 inside = inside @ p
    elif children_iter:
        # Sequence or Stream: sequential composition
        items = [_build_event_tree(i) for i in children_iter]
        if items:
            inside = items[0]
            for item in items[1:]:
                inside = inside >> item

    return _to_serialization(box, inside)

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

@symmetric.Diagram.from_callable(symmetric.Ty("CharacterStream"), ser.Node)
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
