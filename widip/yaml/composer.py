from __future__ import annotations
from typing import Any
from discopy import symmetric
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream
from .representation import NodeGraph, Scalar as SemanticScalar, Sequence as SemanticSequence, Mapping as SemanticMapping, Anchor as SemanticAnchor, Alias as SemanticAlias

def ar_compose(box: Any) -> symmetric.Diagram:
    """Arrow mapping for the compose functor."""
    if isinstance(box, Scalar):
        return SemanticScalar(box.tag, box.value)
    if isinstance(box, Alias):
        return SemanticAlias(box.name)
    if isinstance(box, Anchor):
        return SemanticAnchor(box.name, box.inside)
    if isinstance(box, Sequence):
        return SemanticSequence(box.inside, tag=box.tag)
    if isinstance(box, Mapping):
        return SemanticMapping(box.inside, tag=box.tag)
    if isinstance(box, Document):
        return box.__class__(box.inside)
    if isinstance(box, Stream):
        return box.__class__(box.inside)
    return box

# The Composer Functor (SerializationTree -> NodeGraph)
# Using identity for objects as both are symmetric categories over Node.
Composer = symmetric.Functor(ob=lambda x: x, ar=ar_compose, cod=NodeGraph)

