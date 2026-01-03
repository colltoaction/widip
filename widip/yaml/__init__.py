from __future__ import annotations
from typing import Any
from discopy import closed, symmetric
from .composer import Composer, loader
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node
from .parse import parse
from .construct import construct
from ..computer import Language

# Standard serialization loader factory
_loader_factory = loader(Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node)

def load(node: Any) -> symmetric.Diagram:
    """Load YAML HIF into Semantic NodeGraph diagram."""
    # Pipeline: HIF Node -> Serialization Tree -> Semantic NodeGraph
    return _loader_factory((0, node)) >> Composer

# Expose a diagram.from_callable for the full pipeline (Shell/Compiler)
@closed.Diagram.from_callable(Language, Language)
def shell(diagram_source: Any) -> closed.Diagram:
    """The Shell Functor: HIF -> Semantic -> Computer."""
    # Pipeline: HIF -> Semantic
    # Note: diagram_source might be HIF node iterator (incidences) OR raw python object if pre-parsed?
    # load() expects HIF node from nx_yaml.
    # We call load() to get Semantic.
    semantic = load(diagram_source)
    # Pipeline: Semantic -> Computer (Process-ready)
    return construct(semantic)

# Alias for external use
compiler = shell
