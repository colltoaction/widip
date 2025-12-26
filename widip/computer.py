"""
This module implements the computational model described in "Programs as Diagrams" (arXiv:2208.03817).
It defines the core boxes (Data, Sequential, Concurrent) representing the computation category.
"""

from discopy import closed, python, utils, symmetric


class Data(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("⌜−⌝", dom, cod)

class Sequential(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(;)", dom, cod)

class Concurrent(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(||)", dom, cod)

class Swap(closed.Box, symmetric.Swap):
    def __init__(self, left, right):
        symmetric.Swap.__init__(self, left, right)

class Copy(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Copy", dom, cod)

class Discard(closed.Box):
    def __init__(self, dom):
        super().__init__("Discard", dom, closed.Ty())

class Cast(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Cast", dom, cod)

class Eval(closed.Eval):
    def __init__(self, x):
        super().__init__(x)
        self.name = "{}"

Computation = closed.Category(closed.Ty, closed.Box)
