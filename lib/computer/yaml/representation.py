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
from ..core import Copy, Merge, Discard, Program
from discopy import monoidal

def Scalar(tag, value):
    return YamlBox("Scalar", tag=tag, value=value)

def Sequence(inside, tag="", **kwargs):
    # Sequence is categorical composition: item1 >> item2 >> ...
    if not inside:
        return frobenius.Id(Node)
    
    if isinstance(inside, list):
        # Compose all items
        diag = inside[0]
        for item in inside[1:]:
            diag = diag >> item
        
        # If tagged, wrap in a Tagged box (or Program if applicable)
        if tag:
             return YamlBox(tag, dom=diag.dom, cod=diag.cod, nested=diag, kind="Tagged", tag=tag)
        return diag
    
    # If single item (shouldn't happen with correct usage but for safety)
    return inside

def Mapping(inside, tag=""):
    # Mapping is parallel execution: Δ >> (v1 @ v2 @ ...) >> μ
    # inside is a list of VALUE diagrams (keys are structurally implicit in wires or ignored)
    
    if not inside:
        return Data("") # Empty mapping usually implies empty data or None
    
    n = len(inside)
    if n == 1:
        # Optimization: Single item map is just execution of that item
        diag = inside[0]
    else:
        # Tensor product of all items
        tensor = inside[0]
        for item in inside[1:]:
            tensor = tensor @ item
        
        # Wrap with Copy and Merge
        # Note: We assume inputs/outputs are singular 'Node' types or compatible.
        # This topological mapping forces the parallel structure.
        diag = Copy(Node, n) >> tensor >> Merge(Node, n)

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
