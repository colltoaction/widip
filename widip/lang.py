"""The Run language category"""

from discopy import closed, markov, monoidal, symmetric
from discopy.utils import factory

class Box(
    closed.Box,
    markov.Box,
    symmetric.Box
):
    """"""

@factory
class Ty(
    monoidal.Ty,
):
    """"""
    def __rshift__(self, other):
        return closed.Ty(*self.inside) >> closed.Ty(*other.inside)
