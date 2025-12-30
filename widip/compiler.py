from discopy import closed
from .computer import Data, Sequential, Concurrent, Cast, Swap, Copy, Discard, Computation, Program, Pair
from .yaml import Scalar, Sequence, Mapping, Yaml


def compile_ar(ar):
    if isinstance(ar, Scalar):
        if ar.tag:
            return Program(ar.tag, dom=ar.dom, cod=ar.cod).uncurry()
        return Data(ar.dom, ar.cod)
    if isinstance(ar, Sequence):
        if ar.n == 2:
            return Pair(ar.dom, ar.cod)
        return Sequential(ar.dom, ar.cod)
    if isinstance(ar, Mapping):
        return Concurrent(ar.dom, ar.cod)
    if isinstance(ar, Cast):
        return ar
    if isinstance(ar, Swap):
        return ar
    if isinstance(ar, Copy):
        return ar
    if isinstance(ar, Discard):
        return ar
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
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
