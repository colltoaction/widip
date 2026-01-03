from __future__ import annotations
from typing import Any
from discopy import closed, symmetric
from .composer import Composer, loader
from .construct import construct
from .serialization import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node

# Pre-configured loader for standard YAML serialization classes
load_serialization_tree = loader(Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream, Node)

def load(node: Any, computer_types: Any = None) -> symmetric.Diagram | closed.Diagram:
    """Full YAML loading pipeline: HIF -> Serialization -> NodeGraph -> Computer.
    
    If 'computer_types' is provided (ignored for now as we hardcode in construct), 
    the result is constructed into that computer category.
    Otherwise, the result is the intermediate NodeGraph semantic diagram.
    """
    
    # 1. Load HIF to Serialization Tree
    serialization_tree = load_serialization_tree((0, node))
    
    # 2. Compose Serialization Tree to Node Graph (Semantic analysis)
    node_graph = Composer(serialization_tree)
    
    if computer_types is None:
        return node_graph
    
    # 3. Construct Computer Diagram from Node Graph
    return construct(node_graph)
