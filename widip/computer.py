"""
This module implements the computational model described in "Programs as Diagrams" (arXiv:2208.03817).
It defines the core boxes (Data, Sequential, Concurrent) representing the computation category.
"""

from discopy import closed, python


class Data(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("⌜−⌝", dom, cod)

class Sequential(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(;)", dom, cod)

class Concurrent(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(||)", dom, cod)

Computation = closed.Category(closed.Ty, closed.Box)


class Process(python.Function):
    def then(self, other):
        # TODO thunk
        bridge_pipe = lambda *args: other(*utils.tuplify(self(*args)))
        return Process(
            bridge_pipe,
            self.dom,
            other.cod,
        )


Widish = closed.Category(python.Ty, Process)
