from functools import reduce
from discopy import closed
from .computer import *
from .yaml import *


def extract_static_args(diag):
    # Check if all boxes are plumbing or data
    if all(isinstance(box, (Data, Copy, Swap, Discard)) for box in diag.boxes):
        return tuple(box.value for box in diag.boxes if isinstance(box, Data))
    return None

def compile_ar(ar):
    if isinstance(ar, Scalar):
        if ar.tag == "exec":
            return Exec(Language, Language)
        if ar.tag:
            # construct Program @ Data(value) >> Eval
            # This ensures dom is empty, allowing pipe inputs to pass as extra args (Stdin)
            # Use Data for tag to pass name without executing
            prog = Data(value=ar.tag, dom=closed.Ty(), cod=Language)
            data = Data(value=ar.value, dom=closed.Ty(), cod=Language)
            term = (prog @ data) @ closed.Id(Language)
            return term >> Eval(Language @ Language, Language)
        else:
            return Data(value=ar.value, dom=Language, cod=Language)

    # ... (Sequence and Mapping logic remains similar but recursively compiled)

    if isinstance(ar, Sequence):
        # We rely on the functor to recurse, but we might need to be careful about types
        args_diag = tuple(SHELL_COMPILER(x) for x in ar.args)
        # ... logic ...
        if ar.tag:
             combined = reduce(lambda a, b: a >> b, args_diag)
             static_args = extract_static_args(combined)
             if static_args is not None:
                 return Program(ar.tag, args=static_args, dom=Language, cod=Language)
             return Program(ar.tag, args=args_diag, dom=Language, cod=Language)
        return args_diag[0] if args_diag else Discard(Language)

    if isinstance(ar, Mapping):
        ob = SHELL_COMPILER(ar.args[0])
        if ar.tag:
            static_args = extract_static_args(ob)
            if static_args is not None:
                return Program(ar.tag, args=static_args, dom=Language, cod=Language)
            return Program(ar.tag, args=(ob, ), dom=Language, cod=Language)
        return ob
    if isinstance(ar, Anchor):
        from .yaml import RECURSION_REGISTRY
        anchors = RECURSION_REGISTRY.get().copy()
        anchors[ar.name] = ar.args[0]
        RECURSION_REGISTRY.set(anchors)
        return Program(ar.name, args=(SHELL_COMPILER(ar.args[0]), ), dom=Language, cod=Language)
    if isinstance(ar, Alias):
        return Program(ar.name, dom=Language, cod=Language)
    if isinstance(ar, Copy):
        return Copy(Language, ar.n)
    if isinstance(ar, Discard):
        return Discard(Language)
    if isinstance(ar, Swap):
        return Swap(Language, Language)
    return ar

class ShellFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: Language, 
            compile_ar,
            dom=Yaml,
            cod=Computation
        )

SHELL_COMPILER = ShellFunctor()


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    diagram = SHELL_COMPILER(diagram)
    return diagram
