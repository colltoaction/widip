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
from discopy import monoidal

def Scalar(tag, value):
    return YamlBox("Scalar", tag=tag, value=value)

def Sequence(inside, tag="", **kwargs):
    # Sequence is a container for items
    return YamlBox("Sequence", nested=inside, tag=tag, **kwargs)

def Mapping(inside, tag="", **kwargs):
    if not inside:
        return YamlBox("Mapping", nested=inside, tag=tag, **kwargs)
    
    n = len(inside)
    # Tensor product of all items
    tensor = inside[0]
    for item in inside[1:]:
        tensor = tensor @ item
    
    # Wrap with Copy and Merge
    # Use frobenius.Box to match category of tensor
    copy_box = frobenius.Box("Δ", Node, Node ** n)
    merge_box = frobenius.Box("μ", Node ** n, Node)
    diag = copy_box >> tensor >> merge_box

    if tag:
         return YamlBox(tag, dom=diag.dom, cod=diag.cod, nested=diag, kind="Tagged", tag=tag)
    
    return diag

def Titi(inside, **kwargs):
    # Titi endofunctor wraps everything into a single I/O stream handler
    return YamlBox("Titi", dom=Node, cod=Node, nested=inside, **kwargs)

def Anchor(name, inside):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox(f"Anchor({name})", dom=dom, cod=cod, kind="Anchor", anchor_name=name, nested=inside)

def Alias(name):
    # Alias is a placeholder for any node
    return YamlBox(name, dom=Node, cod=Node, kind="Alias", anchor_name=name)

def Document(inside):
    dom = getattr(inside, 'dom', Node)
    cod = getattr(inside, 'cod', Node)
    return YamlBox("Document", dom=dom, cod=cod, nested=inside, kind="Document")

def Stream(inside):
    # Stream executes documents sequentially but ensures independent contexts (e.g. anchors)
    # We keep it as a box to allow exec.py to handle context clearing.
    dom = getattr(inside[0], 'dom', Node) if inside else Node
    cod = getattr(inside[-1], 'cod', Node) if inside else Node
    return YamlBox("Stream", dom=dom, cod=cod, nested=inside, kind="Stream")
