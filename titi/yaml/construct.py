from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from computer.core import Language
from computer.common import TitiBox

# Language is now a Ty instance
L = Language

def CopyBox():
    return TitiBox("Δ", Language, Language @ Language, data=(), draw_as_spider=True)

def make_copy(n):
    if n <= 1: return closed.Id(Language)
    if n == 2: return CopyBox()
    return CopyBox() >> (closed.Id(Language) @ make_copy(n - 1))

# Helper to extract static arguments
def extract_args(box):
    """Recursively extract static arguments from boxes."""
    # Check for Scalar kind (name="Scalar")
    if getattr(box, 'name', '') == "Scalar":
        return (str(box.value),)
    
    if hasattr(box, 'nested'): 
        # Best effort traversal of nested diagram to find Scalars
        args = []
        nested = box.nested
        if hasattr(nested, 'boxes'):
            for b in nested.boxes:
                args.extend(extract_args(b))
        elif hasattr(nested, 'inside'): # Layers
             for b in nested.boxes:
                 args.extend(extract_args(b))
        return tuple(args)
    return ()

def construct_box(box) -> closed.Diagram:
    import titi.yaml
    
    tag = getattr(box, 'tag', None)
    value = getattr(box, 'value', None)
    nested = getattr(box, 'nested', None)
    name = getattr(box, 'name', None) # Kind is in name usually
    kind = name 
    
    # Handle specific kinds if name is explicit (Anchors/Aliases might have specialized names)
    # YamlBox sets kind=name passed to __init__.
    # Anchor sets name="Anchor(x)", but we stored anchor_name in attributes.
    anchor_name = getattr(box, 'anchor_name', None)

    # 1. Handle Titi Special Case
    if kind == "Titi" or tag == "titi":
        inside = titi.yaml.construct_functor(nested)
        start = Titi.read_stdin
        if not inside.dom: start = start >> Discard()
        return start >> inside >> Titi.printer

    # 2. Handle Anchor
    if kind == "Anchor" or (kind and kind.startswith("Anchor(")):
        inside = titi.yaml.construct_functor(nested)
        return Program("anchor", (anchor_name, inside))

    # 3. Handle Alias
    if kind == "Alias":
        return Program("alias", (anchor_name,))

    # 4. Handle Scalar (Leaf)
    if kind == "Scalar" or (nested is None and value is not None):
        if tag:
            args = (value,) if value is not None else ()
            return Program(tag, args)
        if value is None or value == "":
            return closed.Id(Language)
        return Data(value)

    # 5. Handle Container (Sequence / Mapping / Document / Stream)
    # Try to extract static args first if tagged
    if tag:
        try:
            args = extract_args(box)
            if args:
                return Program(tag, args)
        except Exception: 
            pass # Fallback to generic wrapping

    if nested is None:
        # Fallback for unexpected empty nested boxes that aren't Scalar/Alias
        return closed.Id(Language)

    inside = titi.yaml.construct_functor(nested)
    
    # Implicit Input Copying for Mappings
    if kind == "Mapping":
        n = len(inside.dom)
        if n > 1:
            inside = make_copy(n) >> inside

    # 6. Handle Tags on Containers (Generic Program Wrapper fallback)
    if tag:
        return Program(tag, (inside,))

    return inside
