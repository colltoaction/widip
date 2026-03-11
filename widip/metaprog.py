"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""
from discopy.monoidal import Ty

from .computer import *


class Computation(Box):
    """
    An eval box with distinguished X-indexing
    """
    def __init__(self, name, X, A, B):
        self.name, self.X, self.A, self.B = name, X, A, B
        super().__init__(name, X @ A, B)

    def specialize(self):
        return Eval(self.B << self.X @ self.A)


class Program(monoidal.Bubble, Box):
    """
    Fig 6.1: F:f→f
    A computation f encoded such that f = {F}.
    """
    def __init__(self, f: Computation):
        self.f = f
        arg = (
            Box(f.name, f.X, f.B << f.A) @ f.A
            >> Eval(f.B << f.A))
        monoidal.Bubble.__init__(self, arg, dom=f.X @ f.A, cod=f.cod)

    def specialize(self):
        return self.f

class Metaprogram(monoidal.Bubble, Box):
    """
    Fig 6.1: ℱ:I->(F->F)
    A program F encoded such that F = {ℱ}.
    """
    def __init__(self, F: Program):
        self.F, f = F, F.f
        arg = (
            Box(f.name, Ty(), f.B << f.A << f.X) @ f.X @ f.A
            >> Eval(f.B << f.A << f.X) @ f.A
            >> Eval(f.B << f.A))
        monoidal.Bubble.__init__(self, arg, dom=f.X @ f.A, cod=f.cod)

    def specialize(self):
        return self.F

class ProgramFunctor(Functor):
    """
    Evaluates programs.
    Preserves computer boxes and metaprograms.
    """
    def __call__(self, other):
        if isinstance(other, Program):
            other = other.specialize()
        return Functor.__call__(self, other)


class MetaprogramFunctor(Functor):
    """
    Evaluates metaprograms.
    Preserves computer boxes and programs.
    """
    def __call__(self, other):
        if isinstance(other, Metaprogram):
            return other.specialize()
        return Functor.__call__(self, other)
