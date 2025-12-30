from discopy import closed

from .computer import *
from .yaml import *


def compile_ar(ar):
    if isinstance(ar, Scalar):
        if ar.tag:
            prog = Program(ar.tag)
            data = Data(closed.Ty(), closed.Ty(ar.value))
            return (prog @ data) >> Eval(data.cod, ar.cod)
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Sequence):
        if ar.dom[:1] == Language:
            return Eval(ar.dom[1:], ar.cod)
        if ar.n == 2:
            return Pair(ar.dom, ar.cod)
        return Sequential(ar.dom, ar.cod)
    if isinstance(ar, Mapping):
        return closed.Id(ar.dom)
    if isinstance(ar, Alias):
        return Data(ar.dom, ar.cod) >> Copy(ar.cod, 2) >> closed.Id(ar.cod) @ Discard(ar.cod)
    if isinstance(ar, Anchor):
        return Copy(ar.dom, 2) >> closed.Id(ar.dom) @ Discard(ar.dom)
    return ar


class ShellFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: ob,
            self.compile_box,
            dom=Yaml,
            cod=Computation
        )

    def __call__(self, diagram):
        if isinstance(diagram, Trace):
            return Trace(self(diagram.arg))
        return super().__call__(diagram)

    def compile_box(self, ar):
        return compile_ar(ar)

SHELL_COMPILER = ShellFunctor()


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
