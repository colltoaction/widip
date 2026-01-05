from __future__ import annotations
from typing import Any
from discopy import closed, symmetric, frobenius
from .representation import Scalar, Sequence, Mapping, Anchor, Alias, Document, Stream
from ..core import Language, Copy, Merge, Discard, Program, Data, Titi

# Create diagram instances for copy, merge, discard
copy = Copy(Language, 2) >> closed.Id(Language ** 2)
merge = Merge(Language, 2) >> closed.Id(Language)
discard = Discard(Language) >> closed.Id(closed.Ty())

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

    # Debug
    # print(f"DEBUG: construct_box kind={kind!r} name={name!r} tag={tag!r}", file=__import__('sys').stderr)

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
        
        # Ensure core codomain is Ty() before passing to final Data box
        if len(core.cod) > 0:
            core = core >> Discard(core.cod)
        
        return core >> Data("")

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
        if not tag:
            if value is None or value == "":
                return closed.Id(Language)
            return Data(value)
        # Fall through to default tag handling if tagged

    # Special: Treat untagged sequences as pipelines (prefer >>)
    is_seq = kind == "Sequence" and not tag
    has_inside = hasattr(nested, 'inside') or isinstance(nested, list)
    if is_seq and has_inside:
          items = nested.inside if hasattr(nested, 'inside') else nested
          return sequential_compose(items)
    
    if kind == "Stream":
          items = nested.inside if hasattr(nested, 'inside') else nested
          return Program("stream", (items,))

    if nested is None:
         inside = closed.Id(Language)
    else:
         inside = computer.yaml.construct_functor(nested)

    if kind == "Mapping" and not tag:
        # Raw tensor representation for untagged mappings
        return inside

    # Trace back algebraic ops
    if kind == "Δ": return copy
    if kind == "μ": return merge
    if kind == "ε": return discard

    if tag and kind not in ["Titi"]:
        if tag.lower() == "data":
             # If inside is Data box, we want its name. 
             # nested for a tagged scalar is the Scalar box. 
             # inside is already construct_functor(nested) -> Data(val)
             if hasattr(inside, 'name'):
                  return Data(inside.name)
             return Data(value)
             
        # Default: create Program with tag and args
        args = extract_args(box)
        return Program(tag, args)

    return inside

def sequential_compose(items: list) -> closed.Diagram:
    """
    Helper to compose a list of items.
    Prefer strict sequential composition (>>) for pipelines.
    Fall back to 'Accumulative Tap' only if domains/codomains don't match
    or if multiple outputs are desired (though usually we want to see everything).
    """
    import computer
    from ..core import Language, Discard, make_copy, make_merge, Copy, Merge
    from discopy import closed
    
    res = None
    if not items: return closed.Id(Language)
    
    # Edge case: If 1 item and it's a Program, just return it directly (unwrap)
    if len(items) == 1:
        return computer.yaml.construct_functor(items[0])

    for layer in items:
        layer_diag = computer.yaml.construct_functor(layer)
        if res is None:
            res = layer_diag
        else:
            n_res = len(res.cod)
            n_layer = len(layer_diag.dom)
            
            # --- PIPE First ---
            if n_res == n_layer and n_res > 0:
                 # Standard pipeline: echo 1 >> awk ...
                 res = res >> layer_diag
            # --- TAP Second (Accumulative) ---
            elif n_res == 1 and n_layer == 1:
                 # If they COULD pipe but we want to see both? 
                 # Actually, most users expect pipelines in sequences. 
                 # But some might expect "log-like" behavior. 
                 # Given the current tests, "Accumulative Tap" was intended for untagged seqs.
                 # Let's keep it as a fallback or explicit if it was the previous behavior.
                 res = make_copy(2) >> (res @ layer_diag) >> make_merge(2)
            # --- TENSOR Third ---
            elif n_layer == 0:
                res = res @ layer_diag
            elif n_res == 0:
                res = res >> layer_diag
            elif n_res < n_layer:
                if n_res == 1:
                    res = res >> make_copy(n_layer) >> layer_diag
                else: res = res >> layer_diag
            elif n_res > n_layer:
                if n_layer == 1:
                    res = res >> make_merge(n_res) >> layer_diag
                else:
                    extra = n_res - n_layer
                    res = res >> (closed.Id(Language ** n_layer) @ Discard(Language ** extra)) >> layer_diag
    return res
