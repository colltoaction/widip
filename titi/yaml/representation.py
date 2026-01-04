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

# --- Compose Implementation Functions ---

def comp_seq(box, compose): return Sequence(compose(box.nested), tag=box.tag)
def comp_map(box, compose): return Mapping(compose(box.nested), tag=box.tag)
def comp_doc(box, compose): return Document(compose(box.nested))
def comp_str(box, compose): return Stream(compose(box.nested))
def comp_anc(box, compose): return Anchor(box.anchor_name, compose(box.nested))
def comp_sca(box): return Scalar(box.tag, box.value)
def comp_ali(box): return Alias(box.anchor_name)
def comp_tit(box, compose): return Titi(compose(box.nested))
