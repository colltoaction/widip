from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from computer.core import Language, copy, merge, discard, Copy, Merge

# Ensure Language is the base closed.Ty
L = Language

def make_copy(n):
    if n <= 1: return closed.Id(Language ** n)
    return Copy(Language, n) >> closed.Id(Language ** n)

def make_merge(n):
    if n <= 1: return closed.Id(Language ** n)
    return Merge(Language, n) >> closed.Id(Language)

# Helper to extract static arguments
def extract_args(box):
    """Recursively extract static arguments from boxes, following representation kinds."""
    if hasattr(box, 'kind') and box.kind == "Scalar":
        return (str(getattr(box, 'value', '')),)
    
    nested = getattr(box, 'nested', None)
    if nested is not None: 
        if hasattr(nested, 'boxes'):
            args = []
            for b in nested.boxes:
                # If it's a Scalar box, we want its value
                if hasattr(b, 'kind') and b.kind == "Scalar":
                    args.append(str(getattr(b, 'value', '')))
                elif hasattr(b, 'name') and b.name not in ["Δ", "μ", "ε"]:
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
        # Match inside domain
        n_in = len(inside.dom)
        if n_in == 0:
            start = start >> Discard()
        elif n_in > 1:
            start = start >> make_copy(n_in)
        
        # Match inside codomain to printer
        n_out = len(inside.cod)
        if n_out == 0:
            core = start >> inside
        else:
            if n_out > 1:
                inside = inside >> make_merge(n_out)
            core = start >> inside >> Titi.printer
        
        return Discard() >> core >> Data("")

    # 2. Handle Anchor
    if kind == "Anchor" or (kind and kind.startswith("Anchor(")):
        anchor_name = anchor_name or name.split("(")[1].split(")")[0]
        inside = titi.yaml.construct_functor(nested)
        return Program("anchor", (anchor_name, inside))

    # 3. Handle Alias
    if kind == "Alias":
        return Program("alias", (anchor_name,))

    # 4. Handle Scalar (Leaf)
    if kind == "Scalar":
        if tag:
            args = (value,) if value is not None else ()
            if tag == "id": return closed.Id(Language)
            if tag == "xargs": return Program("xargs", (value,))
            return Program(tag, args)
        if value is None or value == "":
            return closed.Id(Language)
        return Data(value)

    # 5. Handle Containers (Sequence / Mapping / Document / Stream)
    if nested is None:
        return closed.Id(Language)

    inside = titi.yaml.construct_functor(nested)
    
    if kind == "Mapping":
        n = len(inside.dom)
        if n > 0:
            target_dom = Language ** n
            if inside.dom != target_dom:
                inside = closed.Diagram(inside.inside, target_dom, inside.cod)
            # fan out input if it's a mapping
            inside = make_copy(n) >> inside 
            
            n_out = len(inside.cod)
            if n_out > 1:
                inside = inside >> make_merge(n_out)
            elif n_out == 0:
                inside = inside >> Data("")

    # Trace back algebraic ops
    if kind == "Δ": return copy
    if kind == "μ": return merge
    if kind == "ε": return discard

    if tag and kind not in ["Titi"]:
        return Program(tag, (inside,))

    return inside
