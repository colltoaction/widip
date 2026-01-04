from __future__ import annotations
from typing import Any
from discopy import symmetric

# --- The Node Graph Category (Semantic) ---
Node = symmetric.Ty("Node")
NodeGraph = symmetric.Category(Node, symmetric.Diagram)

# --- Generic Semantic Box ---

class YamlBox(symmetric.Box):
    def __init__(self, name: str, dom=Node, cod=Node, **kwargs):
        # We store all metadata in data, including tag and nested content
        # This unifies the interface. 
        # structure of data: {"kind": name, "tag": tag, "value": value, "nested": nested}
        # But symmetric.Box.data is often expected to be hashable or simple.
        # DisCoPy preserves whatever we pass.
        # Let's use kwargs as the data dict for simplicity, but strictly we should pass it to super.
        
        # Normalize args
        self.kind = kwargs.pop("kind", name)
        self.tag = kwargs.get("tag", "")
        self.value = kwargs.get("value", None)
        self.nested = kwargs.get("nested", None)
        self.anchor_name = kwargs.get("anchor_name", None) # For Anchor/Alias
        
        # We can pass `self` attributes as data, or a frozen dict/tuple
        super().__init__(name, dom, cod, data=kwargs)

    def __repr__(self):
        return f"YamlBox(kind={self.kind}, tag={self.tag!r}, ...)"

# --- Factories ---

def Scalar(tag, value):
    return YamlBox("Scalar", tag=tag, value=value)

def Sequence(inside, tag="", **kwargs):
    return YamlBox("Sequence", nested=inside, tag=tag, **kwargs)

def Mapping(inside, tag=""):
    return YamlBox("Mapping", nested=inside, tag=tag)

def Titi(inside, **kwargs):
    return YamlBox("Titi", nested=inside, **kwargs)

def Anchor(name, inside):
    return YamlBox(f"Anchor({name})", kind="Anchor", anchor_name=name, nested=inside)

def Alias(name):
    return YamlBox(name, kind="Alias", anchor_name=name)

def Document(inside):
    return YamlBox("Document", nested=inside)

def Stream(inside):
    return YamlBox("Stream", nested=inside)


# --- Generic Composition ---

def comp_box(box, compose):
    """Generic composer for YamlBox."""
    nested = compose(box.nested) if box.nested else None
    return YamlBox(
        box.name, box.dom, box.cod,
        kind=box.kind,
        tag=box.tag,
        value=box.value,
        nested=nested,
        anchor_name=box.anchor_name
    )

# Additional composition helpers expected by compose_dispatch

def comp_sca(box, compose):
    """Compose scalar boxes – return the box unchanged (scalar is leaf)."""
    return box

def comp_ali(box, compose):
    """Compose alias boxes – return the box unchanged."""
    return box

def comp_str(box, compose):
    """Compose string (scalar) boxes – alias for comp_sca for compatibility."""
    return box

def comp_seq(box, compose):
    """Compose sequence boxes – recursively compose nested content."""
    nested = compose(box.nested) if box.nested else None
    return Sequence(nested, tag=box.tag)

def comp_map(box, compose):
    """Compose mapping boxes – recursively compose nested content."""
    nested = compose(box.nested) if box.nested else None
    return Mapping(nested, tag=box.tag)

def comp_doc(box, compose):
    """Compose document boxes – recursively compose nested content."""
    nested = compose(box.nested) if box.nested else None
    return Document(nested)

def comp_stream(box, compose):
    """Compose stream boxes – recursively compose nested content."""
    nested = compose(box.nested) if box.nested else None
    return Stream(nested)

