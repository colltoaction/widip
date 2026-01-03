from __future__ import annotations
from typing import Any
from discopy import closed
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias

# Note: We decouple from specific computer implementations by returning generic boxes
# The caller will ensure the target category has the correct primitive types.
# However, we still need to import Language/Program to know what to construct.
# To truly decouple, we could accept a factory or mapping, but for now we follow
# the project structure where widip.computer is the standard target.
# If strict decoupling is needed, the Constructor definition should move out of here,
# or take the target types as arguments.
# Assuming the user wants to remove direct imports of `computer`:

def constructor(Program, Data, Language, Computation):
    """Factory for the Constructor Functor to avoid hardcoded dependencies."""

    def ar_construct(box: Any) -> closed.Diagram:
        """Arrow mapping for the construct functor (NodeGraph -> Computer)."""
        if isinstance(box, Scalar):
            args = (box.value,) if box.value else ()
            if hasattr(box, 'tag') and box.tag:
                return Program(box.tag, Language ** len(box.dom), Language ** len(box.cod), args)
            return Data(box.value, Language ** len(box.dom), Language ** len(box.cod))
            
        if isinstance(box, (Sequence, Mapping)):
            # Functors automatically recurse into bubbles.
            # But we need to ensure the recursive call uses the same functor (composition).
            # DisCoPy's Functor.__call__ handles this if the box is a Bubble.
            if hasattr(box, 'tag') and box.tag:
                return Program(box.tag, Language ** len(box.dom), Language ** len(box.cod), (box.inside,))
            return box.inside
            
        if isinstance(box, Alias):
            return Program(box.name, Language, Language)
            
        if isinstance(box, Anchor):
            return box.inside

        return closed.Id(Language ** len(box.dom))

    def ob_construct(ty: Any) -> closed.Ty:
        """Object mapping for the construct functor."""
        return Language ** len(ty)

    # The Constructor Functor (NodeGraph -> Computer)
    return closed.Functor(ob=ob_construct, ar=ar_construct, cod=Computation)
