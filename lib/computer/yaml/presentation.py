from typing import Any
"""
DEPRECATED: YAML Presentation Boxes

This module is deprecated in favor of the C-based lex/yacc parser.
Use `lib.computer.parser_bridge.YAMLParserBridge` instead.

These boxes are kept for backward compatibility with existing code
that uses nx_yaml, but new code should use the compiled parser.
"""

import warnings
from discopy import symmetric
from nx_hif.hif import hif_node_incidences, hif_edge_incidences, hif_node

class CharacterStream(symmetric.Box):
    """Represents a source stream (string or file-like) of characters (HIF source)."""
    
    def __init__(self, source: Any):
        self.source = source
        super().__init__("CharacterStream", symmetric.Ty(), symmetric.Ty("CharacterStream"))

Index = symmetric.Ty("Index")
Node = symmetric.Ty("Node")
Cursor = Index @ Node
Key = symmetric.Ty("Key")
Data = symmetric.Ty("Data")

class GetNodeData(symmetric.Box):
    """Returns the data associated with the node at the cursor's position."""
    def __init__(self):
        super().__init__("get_node_data", Cursor, Data)

class Step(symmetric.Box):
    """Advances the cursor along a specific edge key (e.g., 'next', 'forward')."""
    def __init__(self):
        super().__init__("step", Cursor @ Key, Cursor)

class Iterate(symmetric.Box):
    """Yields a sequence of (index, node) by following 'next' then 'forward' edges."""
    def __init__(self):
        super().__init__("iterate", Cursor, Cursor)


# --- Presentation Boxes ---

class Scalar(symmetric.Box):
    def __init__(self, value: Any, tag: str = "", anchor: str | None = None):
        name = f"Scalar({value})"
        self.value = value
        self.tag = tag
        self.anchor = anchor
        super().__init__(name, symmetric.Ty(), symmetric.Ty("Scalar"))

class Sequence(symmetric.Box):
    def __init__(self, tag: str = "", anchor: str | None = None):
        self.tag = tag
        self.anchor = anchor
        super().__init__("Sequence", symmetric.Ty(), symmetric.Ty("Sequence"))

class Mapping(symmetric.Box):
    def __init__(self, tag: str = "", anchor: str | None = None):
        self.tag = tag
        self.anchor = anchor
        super().__init__("Mapping", symmetric.Ty(), symmetric.Ty("Mapping"))

class Alias(symmetric.Box):
    def __init__(self, anchor: str):
        self.anchor = anchor
        super().__init__(f"Alias({anchor})", symmetric.Ty(), symmetric.Ty("Alias"))

class Document(symmetric.Box):
    def __init__(self):
        super().__init__("Document", symmetric.Ty(), symmetric.Ty("Document"))

class Stream(symmetric.Box):
    def __init__(self):
        super().__init__("Stream", symmetric.Ty(), symmetric.Ty("Stream"))

class Anchor(symmetric.Box):
    def __init__(self, anchor: str):
        self.anchor = anchor
        super().__init__(f"Anchor({anchor})", symmetric.Ty(), symmetric.Ty("Anchor"))
