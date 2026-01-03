from functools import reduce
from discopy import closed, monoidal, symmetric
from . import computer
from . import yaml
from .loader import Copy as LoaderCopy, Merge as LoaderMerge, Discard as LoaderDiscard, Swap as LoaderSwap
import sys


def extract_static_args(diag):
    # Check if all boxes are plumbing or data
    if all(isinstance(box, (computer.Data, computer.Copy, computer.Swap, computer.Discard)) for box in diag.boxes):
        return tuple(box.value for box in diag.boxes if isinstance(box, computer.Data))
    return None

def compile_ar(ar):
    if isinstance(ar, yaml.Scalar):
        if ar.tag == "exec":
            return computer.Exec(computer.Language, computer.Language)
        elif ar.tag:
            # Use Program box directly for tagged scalars
            # This avoids type mismatches with Eval and handles static args correctly
            args = (ar.value,) if ar.value else ()
            return computer.Program(ar.tag, args=args, dom=computer.Language, cod=computer.Language)
        else:
            return computer.Data(value=ar.value, dom=closed.Ty(), cod=computer.Language)

    if isinstance(ar, yaml.Sequence):
        # Recurse into the bubble contents
        diag = SHELL_COMPILER(ar.inside)
        if ar.tag:
             static_args = extract_static_args(diag)
             if static_args is not None:
                 return computer.Program(ar.tag, args=static_args, dom=computer.Language, cod=computer.Language)
             return computer.Program(ar.tag, args=(diag,), dom=computer.Language, cod=computer.Language)
        return diag

    if isinstance(ar, yaml.Mapping):
        diag = SHELL_COMPILER(ar.inside)
        if ar.tag:
            static_args = extract_static_args(diag)
            if static_args is not None:
                return computer.Program(ar.tag, args=static_args, dom=computer.Language, cod=computer.Language)
            return computer.Program(ar.tag, args=(diag, ), dom=computer.Language, cod=computer.Language)
        return diag

    if isinstance(ar, yaml.Anchor):
        anchors = computer.RECURSION_REGISTRY.get().copy()
        anchors[ar.name] = ar.inside
        computer.RECURSION_REGISTRY.set(anchors)
        return computer.Program(ar.name, args=(SHELL_COMPILER(ar.inside), ), dom=computer.Language, cod=computer.Language)

    if isinstance(ar, yaml.Alias):
        return computer.Program(ar.name, dom=computer.Language, cod=computer.Language)

    if isinstance(ar, LoaderCopy):
        return computer.Copy(map_ob(ar.dom), ar.n)
    if isinstance(ar, LoaderMerge):
        return computer.Merge(map_ob(ar.cod), ar.n)
    if isinstance(ar, LoaderDiscard):
        return computer.Discard(map_ob(ar.dom))
    if isinstance(ar, yaml.Label):
        return closed.Id(closed.Ty())
    if isinstance(ar, LoaderSwap):
        return computer.Swap(map_ob(ar.dom[0:1]), map_ob(ar.dom[1:2]))

    return ar

def map_ob(ob):
    """Map symmetric.Ty to closed.Ty"""
    if hasattr(ob, "inside"):
        if not ob:
            return closed.Ty()
        return closed.Ty().tensor(*[map_ob(o) for o in ob.inside])
    
    name = getattr(ob, "name", None)
    if name in ("", "IO", "node"):
        return computer.Language
    if ob == computer.Language:
        return computer.Language
    return closed.Ty()


def SHELL_COMPILER(diagram):
    """Transform a symmetric.Diagram to a closed.Diagram with compiled boxes"""
    # First check if it's a diagram with boxes (iterate through them)
    if hasattr(diagram, 'boxes') and hasattr(diagram, 'offsets'):
        boxes = diagram.boxes
        offsets = diagram.offsets
        
        # Empty diagram or identity
        if not boxes:
            return closed.Diagram.id(map_ob(diagram.dom))
        
        result = closed.Diagram.id(map_ob(diagram.dom))
        
        for box, offset in zip(boxes, offsets):
            # Compile the box using compile_ar directly
            compiled = compile_ar(box)
            
            if isinstance(compiled, closed.Diagram):
                compiled_box = compiled
            elif isinstance(compiled, closed.Box):
                compiled_box = closed.Diagram.id(compiled.dom) >> compiled
            else:
                # Fallback: wrap in closed.Box
                compiled_box = closed.Diagram.id(map_ob(box.dom)) >> closed.Box(str(box), map_ob(box.dom), map_ob(box.cod))
            
            # Get the identity for left/right padding
            left_ty = result.cod[:offset]
            right_ty = result.cod[offset + len(compiled_box.dom):]
            
            left_id = closed.Diagram.id(left_ty)
            right_id = closed.Diagram.id(right_ty)
            
            # Compose: result >> (left_id @ compiled_box @ right_id)
            layer = left_id @ compiled_box @ right_id
            result = result >> layer
        
        return result
    
    # Handle atomic boxes 
    res = compile_ar(diagram)
    if isinstance(res, closed.Diagram):
        return res
    if isinstance(res, closed.Box):
        return closed.Diagram.id(res.dom) >> res
    # Handle tuple returns or other types
    if isinstance(res, tuple):
        # Tuples might be multiple results - take first element
        if res and isinstance(res[0], (closed.Diagram, closed.Box)):
            return SHELL_COMPILER(res[0])
        return closed.Diagram.id(closed.Ty())
    # Fallback: wrap in closed.Box if it has dom/cod
    if hasattr(diagram, 'dom') and hasattr(diagram, 'cod'):
        return closed.Diagram.id(map_ob(diagram.dom)) >> closed.Box(str(diagram), map_ob(diagram.dom), map_ob(diagram.cod))
    # Last resort: identity
    return closed.Diagram.id(closed.Ty())


