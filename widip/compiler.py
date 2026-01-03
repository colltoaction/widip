from functools import reduce
from discopy import closed, monoidal, symmetric
from . import computer
from . import yaml
from .loader import to_symmetric
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
        if ar.tag:
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

    if isinstance(ar, yaml.Copy):
        return computer.Copy(SHELL_COMPILER(ar.dom), ar.n)
    if isinstance(ar, yaml.Merge):
        return computer.Merge(SHELL_COMPILER(ar.cod), ar.n)
    if isinstance(ar, yaml.Discard):
        return computer.Discard(SHELL_COMPILER(ar.dom))
    if isinstance(ar, yaml.Label):
         return closed.Id(closed.Ty())
    if isinstance(ar, yaml.Swap):
        return computer.Swap(SHELL_COMPILER(ar.dom[0:1]), SHELL_COMPILER(ar.dom[1:2]))

    return ar

def SHELL_COMPILER(ar):
    if isinstance(ar, yaml.Scalar):
        res = compile_ar(ar)
        if isinstance(res, (monoidal.Box, closed.Box)):
            return closed.Diagram(
                (monoidal.Layer(closed.Ty(), res, closed.Ty()), ),
                res.dom, res.cod)
        return res

    if isinstance(ar, (yaml.Sequence, yaml.Mapping)):
        inside = SHELL_COMPILER(ar.inside)
        if ar.tag:
             static_args = extract_static_args(inside)
             if static_args is not None:
                 res = computer.Program(ar.tag, args=static_args, dom=computer.Language, cod=computer.Language)
             else:
                 res = computer.Program(ar.tag, args=(inside,), dom=computer.Language, cod=computer.Language)
        else:
             res = inside
        
        if isinstance(res, (monoidal.Box, closed.Box)):
            return closed.Diagram(
                (monoidal.Layer(closed.Ty(), res, closed.Ty()), ),
                res.dom, res.cod)
        return res

    if isinstance(ar, symmetric.Diagram):
        res = closed.Diagram.id(SHELL_COMPILER(ar.dom))
        for box, offset in ar.boxes_and_offsets:
            mapped_box = SHELL_COMPILER(box)
            if not isinstance(mapped_box, closed.Diagram):
                mapped_box = closed.Diagram((monoidal.Layer(closed.Ty(), mapped_box, closed.Ty()),), mapped_box.dom, mapped_box.cod)
            
            left = closed.Id(res.cod[:offset])
            right = closed.Id(res.cod[offset + len(mapped_box.dom):])
            res = res >> (left @ mapped_box @ right)
        return res

    if isinstance(ar, yaml.Ty):
        if not ar:
            return closed.Ty()
        return reduce(lambda x, y: x @ y, [SHELL_COMPILER(ob) for ob in ar.inside])
    
    if isinstance(ar, yaml.Node):
        return computer.Language

    # Handle atomic objects/types
    res = compile_ar(ar)
    if isinstance(res, (monoidal.Box, closed.Box)):
         return closed.Diagram((monoidal.Layer(closed.Ty(), res, closed.Ty()),), res.dom, res.cod)
    return res

def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    return SHELL_COMPILER(to_symmetric(diagram))
