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
    # TODO re-enable type checking
    type_checking = False


Widish = closed.Category(python.Ty, Process)
