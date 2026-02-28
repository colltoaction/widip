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
    closed.Ty,
):
    def __rshift__(self, other):
        return self.factory(closed.Under(self, other))

    def __lshift__(self, other):
        return self.factory(closed.Over(self, other))


def Id(x=None):
    """Identity diagram over widip.lang.Ty (defaults to Ty())."""
    return closed.Diagram.id(x if x is not None else Ty())
