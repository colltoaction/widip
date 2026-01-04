from __future__ import annotations
from typing import Any
from itertools import batched
from discopy import frobenius, monoidal, closed

# Import the C-based parser bridge
from ..parser_bridge import YAMLParserBridge

# --- HIF Compatibility (Satisfying test_hif.py) ---
# Keep HIF serialization for compatibility

from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node
from . import presentation as pres
from .presentation import CharacterStream

def to_hif(hg: frobenius.Hypergraph) -> dict:
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

def from_hif(data: dict) -> frobenius.Hypergraph:
    """Reconstructs a DisCoPy Hypergraph from the dictionary-based HIF format."""
    sorted_node_ids = sorted(data["nodes"].keys(), key=int)
    id_map = {nid: i for i, nid in enumerate(sorted_node_ids)}
    
    spider_types = [frobenius.Ty(data["nodes"][nid]["type"]) if data["nodes"][nid]["type"] else frobenius.Ty() for nid in sorted_node_ids]
    
    boxes, box_wires_list = [], []
    for edge in data["edges"]:
        sources = [id_map[s] for s in edge["sources"]]
        targets = [id_map[t] for t in edge["targets"]]
        b_spec = edge["box"]
        dom = frobenius.Ty().tensor(*[spider_types[i] for i in sources])
        cod = frobenius.Ty().tensor(*[spider_types[i] for i in targets])
        boxes.append(frobenius.Box(b_spec["name"], dom, cod, data=b_spec.get("data")))
        box_wires_list.append((tuple(sources), tuple(targets)))
        
    wires = (tuple(id_map[s] for s in data["dom"]), tuple(box_wires_list), tuple(id_map[s] for s in data["cod"]))
    dom = frobenius.Ty().tensor(*[spider_types[i] for i in wires[0]])
    cod = frobenius.Ty().tensor(*[spider_types[i] for i in wires[2]])
    return frobenius.Hypergraph(dom, cod, boxes, wires, spider_types=spider_types)


# --- Serialization Primitives (Native DisCoPy Factories) ---
from .representation import (
    Scalar, Alias, Sequence, Mapping, Anchor, Document, Stream, YamlBox,
    Node
)


# --- Parser Implementation using C lex/yacc ---

# Global parser instance (lazy initialization)
_parser_instance = None

def get_parser() -> YAMLParserBridge:
    """Get or create the global parser instance."""
    global _parser_instance
    if _parser_instance is None:
        try:
            _parser_instance = YAMLParserBridge()
        except FileNotFoundError:
            # Parser not built yet - fall back to nx_yaml
            return None
    return _parser_instance


def parse_box(source_wire):
    """Create a parse box for categorical composition."""
    return frobenius.Box("parse", frobenius.Ty("CharacterStream"), Node)(source_wire)


def impl_parse(source) -> closed.Diagram:
    """
    Native implementation of the YAML parser using C lex/yacc.
    
    This replaces the old nx_yaml implementation with the compiled parser,
    enabling metacompilation and supercompilation.
    """
    # Extract source string
    if hasattr(source, "source") and type(source).__name__ == "CharacterStream":
        source = source.source
    
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        raise TypeError(f"Expected stream or string, got {type(source)}")
    
    # Convert to string if needed
    if hasattr(source, 'read'):
        source_str = source.read()
        if isinstance(source_str, bytes):
            source_str = source_str.decode('utf-8')
    elif isinstance(source, bytes):
        source_str = source.decode('utf-8')
    else:
        source_str = str(source)
    
    # Try C parser first
    parser = get_parser()
    if parser is not None:
        try:
            # Use the C-based lex/yacc parser
            return parser.parse(source_str)
        except Exception as e:
            # Fall back to nx_yaml if C parser fails
            print(f"Warning: C parser failed ({e}), falling back to nx_yaml")
    
    # Fallback: use nx_yaml (old implementation)
    try:
        from nx_yaml import nx_compose_all
        
        # HIF-based parsing (old path)
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

        def hif_to_pres(n: Any) -> tuple[frobenius.Box, Any]:
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

        def _seq_builder(b, c):
            items = [_build_node(i) for i in (c or [])]
            res = items[0] if items else frobenius.Id(Node)
            for it in items[1:]: res >>= it
            res = Sequence(res, tag=getattr(b, 'tag', ""))
            return Anchor(b.anchor, res) if getattr(b, 'anchor', None) else res

        def _map_builder(b, c):
            pairs = [(_build_node(k) >> _build_node(v)) for k, v in batched(list(c or []), 2)]
            res = pairs[0] if pairs else frobenius.Id(Node)
            for p in pairs[1:]: res @= p
            res = Mapping(res, tag=getattr(b, 'tag', ""))
            return Anchor(b.anchor, res) if getattr(b, 'anchor', None) else res

        def build_ser(box: Any, children: Any) -> frobenius.Diagram:
            if isinstance(box, pres.Scalar):
                return Scalar(box.tag, box.value) if not box.anchor else Anchor(box.anchor, Scalar(box.tag, box.value))
            if isinstance(box, pres.Alias):
                return Alias(box.anchor)
            if isinstance(box, pres.Sequence):
                return _seq_builder(box, children)
            if isinstance(box, pres.Mapping):
                return _map_builder(box, children)
            if isinstance(box, pres.Document):
                return Document(_build_node(children)) if children else Document(frobenius.Id(Node))
            if isinstance(box, pres.Stream):
                return Stream(_seq_builder(box, children))
            raise NotImplementedError(f"No serialization for {type(box)}")

        def _build_node(n):
            return build_ser(*hif_to_pres(n))
        
        incidences = nx_compose_all(source_str)
        return _build_node((0, incidences))
    
    except ImportError:
        raise ImportError("Neither C parser nor nx_yaml available. Build the parser with parse.yaml")


@frobenius.Diagram.from_callable(frobenius.Ty("CharacterStream"), Node)
def parse(source):
    """
    Traceable parse diagram using C lex/yacc parser.
    
    This is the main entry point for YAML parsing in the monoidal computer.
    It uses the compiled C parser for performance and enables metacompilation.
    """
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        return parse_box(source)
    return impl_parse(source)


# --- Metacompilation Support ---

def supercompile_parser() -> closed.Diagram:
    """
    Apply supercompilation to the parser itself using Futamura projections.
    
    This demonstrates the monoidal computer's self-metacompilation capability.
    """
    from ..super_extended import Supercompiler
    from ..parser_bridge import YAMLParserBridge
    
    parser = YAMLParserBridge()
    # The parser is already compiled C code, but we can represent it
    # as a categorical diagram for further optimization
    parser_diag = closed.Box("yaml_parser", closed.Ty("YAML"), closed.Ty("AST"))
    
    sc = Supercompiler()
    return sc.supercompile(parser_diag)


__all__ = ['parse', 'impl_parse', 'to_hif', 'from_hif', 'supercompile_parser']
