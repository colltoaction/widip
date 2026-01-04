from __future__ import annotations
from typing import Any
from discopy import frobenius

# --- The Node Graph Category (Semantic) ---
# Use frobenius.Ty for the representation category
Node = frobenius.Ty("Node")

class YamlBox(frobenius.Box):
    def __init__(self, name: str, dom=Node, cod=Node, **kwargs):
        # Normalize args
        self.kind = kwargs.pop("kind", name)
        self.tag = kwargs.get("tag", "")
        self.value = kwargs.get("value", None)
        self.nested = kwargs.get("nested", None)
        self.anchor_name = kwargs.get("anchor_name", None)
        
        super().__init__(name, dom, cod, data=kwargs)

    def __repr__(self):
        return f"YamlBox(kind={self.kind}, tag={self.tag!r}, ...)"

# --- Factories ---

def Scalar(tag, value):
    return YamlBox("Scalar", tag=tag, value=value)

def Sequence(inside, tag="", **kwargs):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Sequence", dom=dom, cod=cod, nested=inside, tag=tag, **kwargs)

def Mapping(inside, tag=""):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Mapping", dom=dom, cod=cod, nested=inside, tag=tag)

def Titi(inside, **kwargs):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Titi", dom=dom, cod=cod, nested=inside, **kwargs)

def Anchor(name, inside):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox(f"Anchor({name})", dom=dom, cod=cod, kind="Anchor", anchor_name=name, nested=inside)

def Alias(name):
    return YamlBox(name, kind="Alias", anchor_name=name)

def Document(inside):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Document", dom=dom, cod=cod, nested=inside)

def Stream(inside):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Stream", dom=dom, cod=cod, nested=inside)
