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
        # Bubbles are automatically mapped by Functor.__call__ on common DisCoPy boxes.
        # However, for custom bubbles, we might need to handle them explicitly.
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

def compose(diagram: symmetric.Diagram) -> symmetric.Diagram:
    """Functor from SerializationTree to NodeGraph implementing YAML semantics."""
    return NodeGraph.from_callable(diagram)(ar_compose)
