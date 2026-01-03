from __future__ import annotations
from .loader import load_serialization_tree
from .composer import compose
from .construct import construct

def load(node: Any) -> Any:
    """Full YAML loading pipeline: HIF -> Serialization -> NodeGraph -> Computer."""
    serialization_tree = load_serialization_tree(node)
    node_graph = compose(serialization_tree)
    return construct(node_graph)
