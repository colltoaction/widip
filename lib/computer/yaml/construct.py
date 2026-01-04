from __future__ import annotations
from typing import Any
from discopy import closed
from . import representation as ren
from computer import Program, Data, Titi, Discard
from ..core import Language, copy, merge, discard, Copy, Merge

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
        val = getattr(box, 'value', None)
        if not val: return ()
        return (str(val),)
    
    nested = getattr(box, 'nested', None)
    if nested is not None: 
        args = []
        # If nested is a diagram, iterate its boxes
        if hasattr(nested, 'boxes'):
            for b in nested.boxes:
                if hasattr(b, 'kind'):
                    args.extend(extract_args(b))
        # If nested is a single box or object
        elif hasattr(nested, 'kind'):
             args.extend(extract_args(nested))
             
        return tuple(args)
    return ()

def construct_box(box) -> closed.Diagram:
    import computer.yaml
    
    tag = getattr(box, 'tag', None)
    value = getattr(box, 'value', None)
    nested = getattr(box, 'nested', None)
    name = getattr(box, 'name', None)
    kind = getattr(box, 'kind', name)
    anchor_name = getattr(box, 'anchor_name', None)

    # 1. Handle Titi Special Case
    if kind == "Titi" or tag == "titi":
        inside = computer.yaml.construct_functor(nested)
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
        inside = computer.yaml.construct_functor(nested)
        return Program("anchor", (anchor_name, inside))

    # 3. Handle Alias
    if kind == "Alias":
        return Program("alias", (anchor_name,))

    # 4. Handle Scalar (Leaf)
    if kind == "Scalar":
        if tag:
            args = (value,) if value else ()
            if tag == "id": return closed.Id(Language)
            if tag == "xargs": return Program("xargs", (value,))
            if tag == "Data": return Data(value)
            # Handle Partial specially
            if tag == "Partial":
                 from computer import Partial
                 return Partial(value)
            return Program(tag, args)
        if value is None or value == "":
            return closed.Id(Language)
        return Data(value)

    # Special: Treat untagged sequences as accumulative pipelines (print taps)
    if kind == "Sequence" and not tag and hasattr(nested, 'inside'):
          res = None
          for layer in nested.inside:
               layer_diag = computer.yaml.construct_functor(layer)
               if res is None:
                    res = layer_diag
               else:
                    # Accumulative Tap: res >> copy >> (printer @ next_layer)
                    n_res = len(res.cod)
                    from computer import Copy, Merge
                    tap = closed.Id(Language ** n_res)
                    if n_res > 1:
                        tap = Merge(Language, n_res) >> closed.Id(Language)
                    
                    if n_res > 0:
                        cp = Copy(res.cod, 2) >> closed.Id(res.cod ** 2)
                        res = res >> cp >> ( (tap >> Program("print", cod=closed.Ty())) @ closed.Id(res.cod) )
                    
                    res = res >> layer_diag
          return res or closed.Id(Language)

    inside = computer.yaml.construct_functor(nested)
    
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
        if tag == "seq": return inside
        args = extract_args(box)
        return Program(tag, args)

    return inside
