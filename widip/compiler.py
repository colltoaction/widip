from functools import reduce
from discopy import closed, monoidal
from . import computer
from . import yaml
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
            # construct Program @ Data(value) >> Eval
            # This ensures dom is empty, allowing pipe inputs to pass as extra args (Stdin)
            # Use Data for tag to pass name without executing
            prog = computer.Data(value=ar.tag, dom=closed.Ty(), cod=computer.Language)
            data = computer.Data(value=ar.value, dom=closed.Ty(), cod=computer.Language)
            term = (prog @ data) @ computer.Id(computer.Language)
            return term >> computer.Eval(computer.Language @ computer.Language, computer.Language)
        else:
            return computer.Data(value=ar.value, dom=closed.Ty(), cod=computer.Language)

    if isinstance(ar, yaml.Sequence):
        # Recurse into the bubble contents
        diag = SHELL_COMPILER(ar.arg)
        if ar.tag:
             static_args = extract_static_args(diag)
             if static_args is not None:
                 return computer.Program(ar.tag, args=static_args, dom=computer.Language, cod=computer.Language)
             return computer.Program(ar.tag, args=(diag,), dom=computer.Language, cod=computer.Language)
        return diag

    if isinstance(ar, yaml.Mapping):
        diag = SHELL_COMPILER(ar.arg)
        if ar.tag:
            static_args = extract_static_args(diag)
            if static_args is not None:
                return computer.Program(ar.tag, args=static_args, dom=computer.Language, cod=computer.Language)
            return computer.Program(ar.tag, args=(diag, ), dom=computer.Language, cod=computer.Language)
        return diag

    if isinstance(ar, yaml.Anchor):
        anchors = computer.RECURSION_REGISTRY.get().copy()
        anchors[ar.name] = ar.arg
        computer.RECURSION_REGISTRY.set(anchors)
        return computer.Program(ar.name, args=(SHELL_COMPILER(ar.arg), ), dom=computer.Language, cod=computer.Language)

    if isinstance(ar, yaml.Alias):
        return computer.Program(ar.name, dom=computer.Language, cod=computer.Language)

    if isinstance(ar, yaml.Copy):
        return computer.Copy(SHELL_COMPILER(ar.dom), ar.n)
    if isinstance(ar, yaml.Merge):
        return computer.Merge(SHELL_COMPILER(ar.cod), ar.n)
    if isinstance(ar, yaml.Stream):
        return SHELL_COMPILER(ar.arg)
    if isinstance(ar, yaml.Discard):
        return computer.Discard(SHELL_COMPILER(ar.dom))
    if isinstance(ar, yaml.Swap):
        return computer.Swap(SHELL_COMPILER(ar.dom[0:1]), SHELL_COMPILER(ar.dom[1:2]))

    return ar

class ShellFunctor(closed.Functor):
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
            # Ensure we return a Diagram to avoid TypeErrors in the closed factory
            if isinstance(res, (monoidal.Box, closed.Box)):
                return computer.Computation.ar.id(res.dom) >> res
            return res

        super().__init__(
            ob_map,
            ar_map,
            dom=yaml.Yaml,
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
