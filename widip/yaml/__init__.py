from __future__ import annotations
from typing import Any
from discopy import closed
from .loader import load as load_serialization_tree
from .composer import Composer
from .construct import constructor
from ..computer import Program, Data, Language, Computation

def load(node: Any) -> closed.Diagram:
    """Full YAML loading pipeline: HIF -> Serialization -> NodeGraph -> Computer."""
    serialization_tree = load_serialization_tree(node)
    
    # Create the Constructor functor using the active Computer implementation
    Constructor = constructor(Program, Data, Language, Computation)
    
    # Pipeline composition: Serialization -> (Composer) -> NodeGraph -> (Constructor) -> Computer
    
    node_graph = Composer(serialization_tree)
    return Constructor(node_graph)
