from __future__ import annotations
from typing import Any
from discopy import closed, symmetric, monoidal
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream
from .. import computer

def construct(diagram: symmetric.Diagram) -> closed.Diagram:
    """Functor from NodeGraph to Computer implementation.
    
    This stage transforms YAML semantic nodes into Programs as Diagrams.
    """
    from ..computer import Data, Program, Language, Discard
    from ..computer.composition import Sequential, Parallel

    def ar(box: Any) -> closed.Diagram:
        if isinstance(box, Scalar):
            args = (box.value,) if box.value else ()
            if box.tag:
                return Program(box.tag, Language, Language, args)
            return Data(box.value, Language, Language)
            
        if isinstance(box, (Sequence, Mapping)):
            # Bubbles are recursively handled by the functor
            inside = construct(box.inside)
            if box.tag:
                return Program(box.tag, Language, Language, (inside,))
            return inside
            
        if isinstance(box, Alias):
            return Program(box.name, Language, Language)
            
        if isinstance(box, Anchor):
            # Anchors are structural markers; here we just recurse
            return construct(box.inside)

        # Handle structural boxes (Copy/Merge/Discard) by mapping to computer equivalents
        # Note: In NodeGraph, these should already be semantic boxes or symmetric identities.
        return closed.Id(Language ** len(box.dom))

    # Ob mapping: everything maps to a sequence of symbol wires
    ob = lambda x: Language ** len(x)
    cod = closed.Category()

    return closed.Functor(ob=ob, ar=ar, cod=cod)(diagram)
