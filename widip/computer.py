"""
This module implements the computational model described in "Programs as Diagrams" (arXiv:2208.03817).
It defines the core boxes (Data, Sequential, Concurrent) representing the computation category.
"""

from discopy import closed, symmetric, markov, python, utils


class Data(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("⌜−⌝", dom, cod)

class Sequential(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(;)", dom, cod)

class Concurrent(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(||)", dom, cod)

class Cast(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Cast", dom, cod)

class Swap(closed.Box, symmetric.Swap):
    def __init__(self, left, right):
        symmetric.Swap.__init__(self, left, right)
        self.name = "σ"

class Copy(closed.Box, markov.Copy):
    def __init__(self, x, n=2):
        if len(x) == 1:
            markov.Copy.__init__(self, x, n)
        else:
            name = f"Copy({x}" + ("" if n == 2 else f", {n}") + ")"
            closed.Box.__init__(self, name, dom=x, cod=x ** n)
            
        self.n = n

class Discard(closed.Box, markov.Discard):
    def __init__(self, dom):
        if len(dom) == 1:
            markov.Discard.__init__(self, dom)
        else:
            name = f"Discard({dom})"
            closed.Box.__init__(self, name, dom=dom, cod=closed.Ty())

Computation = closed.Category(closed.Ty, closed.Box)


class Process(python.Function):
    def __init__(self, inside, dom, cod):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    def then(self, other):
        bridge_pipe = lambda *args: other(*utils.tuplify(self(*args)))
        return Process(
            bridge_pipe,
            self.dom,
            other.cod,
        )
    
    @classmethod
    def eval(cls, base, exponent, left=True):
        def func(f, *x):
             return f(*x)
        return Process(
            func,
            (exponent << base) @ base,
            exponent
        )

Widish = closed.Category(python.Ty, Process)
