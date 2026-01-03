from typing import Any
from discopy import symmetric

from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node

class CharacterStream(symmetric.Box):
    """Represents a source stream (string or file-like) of characters (HIF source)."""
    
    def __init__(self, source: Any):
        self.source = source
        super().__init__("CharacterStream", symmetric.Ty(), symmetric.Ty("CharacterStream"))

    @staticmethod
    def get_node_data(index, node) -> dict:
        """Returns the data associated with the node at the cursor's position."""
        return hif_node(node, index)

    @staticmethod
    def step(index, node, key: str) -> tuple | None:
        """Advances the cursor along a specific edge key (e.g., 'next', 'forward')."""
        incidences = tuple(hif_node_incidences(node, index, key=key))
        if not incidences:
            return None
        ((edge, _, _, _), ) = incidences
        start = tuple(hif_edge_incidences(node, edge, key="start"))
        if not start:
            return None
        ((_, neighbor, _, _), ) = start

        return (neighbor, node)

    @staticmethod
    def iterate(index, node):
        """Yields a sequence of (index, node) by following 'next' then 'forward' edges."""
        curr = CharacterStream.step(index, node, "next")
        while curr:
            yield curr
            curr = CharacterStream.step(curr[0], curr[1], "forward")
