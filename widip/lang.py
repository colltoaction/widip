"""The Run language category."""

from discopy import closed, markov, symmetric
from discopy.utils import factory


class Box(
    closed.Box,
    markov.Box,
    symmetric.Box,
):
    """"""


@factory
class Ty(closed.Ty):
    def __rshift__(self, other):
        return self.factory(closed.Under(other, self))

    def __lshift__(self, other):
        return self.factory(closed.Over(self, other))

    @property
    def base(self):
        return self.inside[0].base if self.is_exp else None

    @property
    def exponent(self):
        return self.inside[0].exponent if self.is_exp else None


def Id(x=None):
    """Identity diagram over widip.lang.Ty (defaults to Ty())."""
    return closed.Diagram.id(x if x is not None else Ty())
