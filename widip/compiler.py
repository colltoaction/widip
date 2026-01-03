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
        return computer.Copy(SHELL_COMPILER(ar.dom), ar.n)
    if isinstance(ar, LoaderMerge):
        return computer.Merge(SHELL_COMPILER(ar.cod), ar.n)
    if isinstance(ar, LoaderDiscard):
        return computer.Discard(SHELL_COMPILER(ar.dom))
    if isinstance(ar, yaml.Label):
        return closed.Id(closed.Ty())
    if isinstance(ar, LoaderSwap):
        return computer.Swap(SHELL_COMPILER(ar.dom[0:1]), SHELL_COMPILER(ar.dom[1:2]))

    return ar

class ShellFunctor(symmetric.Functor):
    def __init__(self):
        def ob_map(ob):
            # Handle Ty objects - iterate through contents
            if hasattr(ob, "inside"):
                if not ob:
                    return closed.Ty()
                return closed.Ty().tensor(*[ob_map(o) for o in ob.inside])
            
            # Handle atomic objects by name
            name = getattr(ob, "name", None)
            if name == "":
                return computer.Language
            if name == "IO":
                return computer.Language
                
            # Fallback for already mapped types or objects
            if ob == computer.Language:
                return computer.Language
                
            return closed.Ty()

        def ar_map(ar):
            res = compile_ar(ar)
            # Wrap result in closed.Diagram to ensure factory compatibility
            if isinstance(res, closed.Box):
                return closed.Diagram.id(res.dom) >> res
            if isinstance(res, closed.Diagram):
                return res
            # For other types, try to wrap
            if hasattr(res, 'dom') and hasattr(res, 'cod'):
                return closed.Diagram.id(closed.Ty()) >> closed.Box(str(res), res.dom, res.cod)
            return res

        super().__init__(
            ob_map,
            ar_map,
            cod=computer.Computation
        )

SHELL_COMPILER = ShellFunctor()


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    diagram = SHELL_COMPILER(diagram)
    return diagram
