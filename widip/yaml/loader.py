from __future__ import annotations
from typing import Any
from itertools import batched
from discopy import symmetric
from .. import hif
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream

def load(node: Any) -> symmetric.Diagram:
    """Functorial mapping from HIF incidences to a structural SerializationTree."""
    
    # We use from_callable to build the diagram structural tree recursively.
    # The 'node' here is the current HIF node (index, node_id).
    
    @symmetric.Diagram.from_callable(symmetric.Ty("Node"), symmetric.Ty("Node"))
    def build(n: Any) -> symmetric.Diagram:
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
                    inside = symmetric.Id(symmetric.Ty("Node"))
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
                    inside = symmetric.Id(symmetric.Ty("Node"))
                else:
                    inside = pairs[0]
                    for p in pairs[1:]:
                        inside = inside @ p
                res = Mapping(inside, tag=tag)
            case "alias":
                res = Alias(anchor)
            case "document":
                root = hif.step(index, node_id, "next")
                inside = build(root) if root else symmetric.Id(symmetric.Ty("Node"))
                res = Document(inside)
            case "stream":
                docs = [build(d) for d in hif.iterate(index, node_id)]
                if not docs:
                    inside = symmetric.Id(symmetric.Ty("Node"))
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

    return build((0, node))
