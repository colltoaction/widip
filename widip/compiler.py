from discopy import closed

from computer import *
from .yaml import *


def compile_ar(ar):
    if isinstance(ar, Scalar):
        if ar.tag == "exec":
            return Exec(ar.dom, ar.cod)
        if ar.tag:
            return Program(ar.tag, dom=ar.dom, cod=ar.cod).uncurry()
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Sequence):
        inner_diagram = ar.args[0]
        inside_compiled = SHELL_COMPILER(inner_diagram)

        if ar.dom[:1] == Language:
            return inside_compiled

        if ar.n == 2:
            return inside_compiled >> Pair(inside_compiled.cod, ar.cod)

        return inside_compiled >> Sequential(inside_compiled.cod, ar.cod)

    if isinstance(ar, Mapping):
        inner_diagram = ar.args[0]
        inside_compiled = SHELL_COMPILER(inner_diagram)
        return inside_compiled >> Concurrent(inside_compiled.cod, ar.cod)

    if isinstance(ar, Alias):
        return Data(ar.dom, ar.cod) >> Copy(ar.cod, 2) >> closed.Id(ar.cod) @ Discard(ar.cod)
    if isinstance(ar, Anchor):
        return Copy(ar.dom, 2) >> closed.Id(ar.dom) @ Discard(ar.dom)
    return ar


class ShellFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: ob,
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
