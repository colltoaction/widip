from functools import reduce
from discopy import closed, monoidal
from . import computer
from . import yaml


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
            term = (prog @ data) @ closed.Id(computer.Language)
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
        return computer.Copy(computer.Language, ar.n)
    if isinstance(ar, yaml.Merge):
        return computer.Merge(computer.Language, ar.n)
    if isinstance(ar, yaml.Discard):
        return computer.Discard(computer.Language)
    if isinstance(ar, yaml.Swap):
        return computer.Swap(computer.Language, computer.Language)

    return ar

class ShellFunctor(closed.Functor):
    def __init__(self):
        def ob_map(ob):
            if ob == yaml.Node:
                return computer.Language
            return closed.Ty()

        super().__init__(
            ob_map,
            compile_ar,
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
