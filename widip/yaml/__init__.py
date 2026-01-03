from __future__ import annotations
from typing import Any
from discopy import closed, symmetric
from .composer import Composer, loader
from .construct import construct
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node
from ..computer import Language, Program, Data

# Pre-configured loader for standard YAML serialization classes
load_serialization_tree = loader(Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node)


def load(node: Any, computer_types: Any = None) -> symmetric.Diagram | closed.Diagram:
    """Full YAML loading pipeline.
    
    If computer_types is provided, returns the full Computer Diagram via 'shell'.
    Otherwise, returns the intermediate Semantic NodeGraph via Composer.
    """
    serialization_tree = load_serialization_tree((0, node))

    if computer_types:
        return (Composer >> construct)(serialization_tree)
        
    return Composer(serialization_tree)
