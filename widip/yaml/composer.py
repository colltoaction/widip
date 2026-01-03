from __future__ import annotations
from typing import Any
from itertools import batched
from discopy import symmetric

from .serialization import (
    Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream
)
from .. import hif
from .representation import (
    NodeGraph, Node,
    Scalar as SemanticScalar,
    Sequence as SemanticSequence,
    Mapping as SemanticMapping,
    Anchor as SemanticAnchor,
    Alias as SemanticAlias,
    Document as SemanticDocument,
    Stream as SemanticStream
)


def loader(Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node):
    """Factory for the HIF-to-SerializationTree loader."""

    def build(n: Any) -> symmetric.Diagram:
        """Arrow mapping converting HIF nodes to SerializationTree diagrams."""
        index, node_id = n
        data = hif.get_node_data(index, node_id)
        tag = (data.get("tag") or "")[1:]
        kind = data["kind"]
        anchor = data.get("anchor")
        
        match kind:
            case "scalar":
                res = Scalar(tag, data["value"])
            case "sequence":
                items = [build(i) for i in hif.iterate(index, node_id)]
                if not items:
                    inside = symmetric.Id(Node)
                else:
                    inside = items[0]
                    for item in items[1:]:
                        inside = inside >> item
                res = Sequence(inside, tag=tag)
            case "mapping":
                nodes = list(hif.iterate(index, node_id))
                pairs = []
                for key_nd, val_nd in batched(nodes, 2):
                    key = build(key_nd)
                    val = build(val_nd)
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
                root = hif.step(index, node_id, "next")
                inside = build(root) if root else symmetric.Id(Node)
                res = Document(inside)
            case "stream":
                docs = [build(d) for d in hif.iterate(index, node_id)]
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

    return build


# The Composer Functor (SerializationTree -> NodeGraph)
# Implemented using a top-level function decorated with @NodeGraph.from_callable
# This handles the transformation from structural elements to semantic elements.

@symmetric.Diagram.from_callable(Node(), Node())
def compose(box: Any) -> symmetric.Diagram:
    """Functorial mapping: Serialization Tree -> Semantic Node Graph."""
    
    # Recursive composition for bubbles
    if isinstance(box, Sequence):
        return SemanticSequence(compose(box.inside), tag=box.tag)
        
    if isinstance(box, Mapping):
        return SemanticMapping(compose(box.inside), tag=box.tag)
        
    if isinstance(box, Document):
        return SemanticDocument(compose(box.inside))
        
    if isinstance(box, Stream):
        return SemanticStream(compose(box.inside))
        
    if isinstance(box, Anchor):
        return SemanticAnchor(box.name, compose(box.inside))

    # Atomic boxes
    if isinstance(box, Scalar):
        return SemanticScalar(box.tag, box.value)
        
    if isinstance(box, Alias):
        return SemanticAlias(box.name)
        
    # Generic wire/structure fallback
    # Since from_callable traces, we might get generic objects if we don't match
    return box

# Export 'compose' as the Composer functor
Composer = compose
