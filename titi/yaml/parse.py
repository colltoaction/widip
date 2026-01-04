from __future__ import annotations
from typing import Any
from itertools import batched
from functools import singledispatch
from discopy import symmetric, monoidal

from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node
from . import presentation as pres
from .presentation import CharacterStream

# --- HIF Compatibility (Satisfying test_hif.py) ---

def to_hif(hg: symmetric.Hypergraph) -> dict:
    """Serializes a DisCoPy Hypergraph to a dictionary-based HIF format."""
    nodes = {}
    for i, t in enumerate(hg.spider_types):
        nodes[str(i)] = {"type": t.name if t else ""}

    edges = []
    box_wires = hg.wires[1]
    for i, box in enumerate(hg.boxes):
        edges.append({
            "box": {"name": box.name, "dom": [x.name for x in box.dom], "cod": [x.name for x in box.cod], "data": box.data},
            "sources": [str(x) for x in box_wires[i][0]],
            "targets": [str(x) for x in box_wires[i][1]]
        })

    return {
        "nodes": nodes, "edges": edges,
        "dom": [str(x) for x in hg.wires[0]],
        "cod": [str(x) for x in hg.wires[2]]
    }

def from_hif(data: dict) -> symmetric.Hypergraph:
    """Reconstructs a DisCoPy Hypergraph from the dictionary-based HIF format."""
    sorted_node_ids = sorted(data["nodes"].keys(), key=int)
    id_map = {nid: i for i, nid in enumerate(sorted_node_ids)}
    
    spider_types = [symmetric.Ty(data["nodes"][nid]["type"]) if data["nodes"][nid]["type"] else symmetric.Ty() for nid in sorted_node_ids]
    
    boxes, box_wires_list = [], []
    for edge in data["edges"]:
        sources = [id_map[s] for s in edge["sources"]]
        targets = [id_map[t] for t in edge["targets"]]
        b_spec = edge["box"]
        dom = symmetric.Ty().tensor(*[spider_types[i] for i in sources])
        cod = symmetric.Ty().tensor(*[spider_types[i] for i in targets])
        boxes.append(symmetric.Box(b_spec["name"], dom, cod, data=b_spec.get("data")))
        box_wires_list.append((tuple(sources), tuple(targets)))
        
    wires = (tuple(id_map[s] for s in data["dom"]), tuple(box_wires_list), tuple(id_map[s] for s in data["cod"]))
    dom = symmetric.Ty().tensor(*[spider_types[i] for i in wires[0]])
    cod = symmetric.Ty().tensor(*[spider_types[i] for i in wires[2]])
    return symmetric.Hypergraph(dom, cod, boxes, wires, spider_types=spider_types)


# --- Serialization Primitives (Native DisCoPy Factories) ---
from .representation import (
    Scalar, Alias, Sequence, Mapping, Anchor, Document, Stream, YamlBox,
    Node
)


# --- HIF Traversal Helpers ---

def _step(index, node, key: str) -> tuple | None:
    incidences = tuple(hif_node_incidences(node, index, key=key))
    if not incidences: return None
    ((edge, _, _, _), ) = incidences
    start = tuple(hif_edge_incidences(node, edge, key="start"))
    if not start: return None
    ((_, neighbor, _, _), ) = start
    return (neighbor, node)

def _iterate(index, node):
    curr = _step(index, node, "next")
    while curr:
        yield curr
        curr = _step(curr[0], curr[1], "forward")

# --- HIF Dispatcher (Simplified Pattern) ---

@singledispatch
def hif_to_pres(n: Any) -> tuple[symmetric.Box, Any]:
    index, node_id = n
    data = hif_node(node_id, index)
    kind, tag, anchor = data["kind"], (data.get("tag") or "")[1:], data.get("anchor")
    
    if kind == "scalar": return pres.Scalar(data["value"], tag, anchor), None
    if kind == "sequence": return pres.Sequence(tag, anchor), _iterate(index, node_id)
    if kind == "mapping": return pres.Mapping(tag, anchor), _iterate(index, node_id)
    if kind == "alias": return pres.Alias(anchor), None
    if kind == "document": return pres.Document(), _step(index, node_id, "next")
    if kind == "stream": return pres.Stream(), _iterate(index, node_id)
    raise ValueError(f"Unknown kind \"{kind}\"")

# --- Event Tree Builder ---

@singledispatch
def build_ser(box: Any, children: Any) -> symmetric.Diagram:
    """Build serialization atom from presentation box and its children."""
    raise NotImplementedError(f"No serialization for {type(box)}")

def _build_node(n):
    return build_ser(*hif_to_pres(n))

build_ser.register(pres.Scalar, lambda b, c: \
    (Scalar(b.tag, b.value) if not b.anchor else Anchor(b.anchor, Scalar(b.tag, b.value))))

build_ser.register(pres.Alias, lambda b, c: Alias(b.anchor))

def _seq_builder(b, c):
    items = [_build_node(i) for i in (c or [])]
    res = items[0] if items else symmetric.Id(Node)
    for it in items[1:]: res >>= it
    res = Sequence(res, tag=getattr(b, 'tag', ""))
    return Anchor(b.anchor, res) if getattr(b, 'anchor', None) else res

build_ser.register(pres.Sequence, _seq_builder)
build_ser.register(pres.Stream, lambda b, c: Stream(_seq_builder(b, c)))

def _map_builder(b, c):
    pairs = [(_build_node(k) >> _build_node(v)) for k, v in batched(list(c or []), 2)]
    res = pairs[0] if pairs else symmetric.Id(Node)
    for p in pairs[1:]: res @= p
    res = Mapping(res, tag=getattr(b, 'tag', ""))
    return Anchor(b.anchor, res) if getattr(b, 'anchor', None) else res

build_ser.register(pres.Mapping, _map_builder)
build_ser.register(pres.Document, lambda b, c: Document(_build_node(c)) if c else Document(symmetric.Id(Node)))

# --- Functor entry: Traceable Parser ---

def parse_box(source_wire):
    return symmetric.Box("parse", symmetric.Ty("CharacterStream"), Node)(source_wire)

def impl_parse(source):
    """Native implementation of the YAML parser."""
    if hasattr(source, "source") and type(source).__name__ == "CharacterStream":
        source = source.source
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        raise TypeError(f"Expected stream or string, got {type(source)}")
    from nx_yaml import nx_compose_all
    incidences = nx_compose_all(source)
    return _build_node((0, incidences))

@symmetric.Diagram.from_callable(symmetric.Ty("CharacterStream"), Node)
def parse(source):
    """Traceable parse diagram."""
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        return parse_box(source)
    return impl_parse(source)
