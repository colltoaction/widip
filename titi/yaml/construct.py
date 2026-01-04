from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from computer.core import Language, copy, merge, discard

# Language is now a Ty instance
L = Language

# Helper to extract static arguments
def extract_args(box):
    """Recursively extract static arguments from boxes."""
    name = getattr(box, 'name', '')
    if name == "Scalar":
        return (str(getattr(box, 'value', '')),)
    
    nested = getattr(box, 'nested', None)
    if nested is not None: 
        if hasattr(nested, 'boxes'):
            args = []
            for b in nested.boxes:
                if hasattr(b, 'name') and b.name not in ["Δ", "μ", "ε"]:
                    args.append(b.name)
            return tuple(args)
        
        args = []
        try:
            if hasattr(nested, 'kind'):
                 args.extend(extract_args(nested))
        except Exception: pass
        return tuple(args)
    return ()

def construct_box(box) -> closed.Diagram:
    import titi.yaml
    
    tag = getattr(box, 'tag', None)
    value = getattr(box, 'value', None)
    nested = getattr(box, 'nested', None)
    name = getattr(box, 'name', None)
    kind = name 
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
    if tag:
        try:
            args = extract_args(box)
            if args:
                return Program(tag, args)
        except Exception: 
            pass

    if nested is None:
        return closed.Id(Language)

    # Core Logic: All nested things must be mapped to Language category
    inside = titi.yaml.construct_functor(nested)
    
    # Mapping and algebraic operations
    if kind == "Mapping":
        n = len(inside.dom)
        if n > 0:
            # Note: make_copy or similar here if needed, 
            # but usually Mapping just tensor components
            pass

    # Trace back algebraic ops if they appeared in representation
    if name == "Δ": return copy
    if name == "μ": return merge
    if name == "ε": return discard

    if tag:
        return Program(tag, (inside,))

    return inside
