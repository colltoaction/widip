"""
This module implements the computational model described in "Programs as Diagrams" (arXiv:2208.03817).
It defines the core boxes (Data, Sequential, Concurrent) representing the computation category.
"""

from discopy import closed, symmetric, markov, traced


Language = closed.Ty("IO")

class Eval(closed.Box):
    def __init__(self, A, B):
        drawing_name = "{}" + f": {A} -> {B}"
        super().__init__("", Language @ A, B, drawing_name=drawing_name)

class Program(closed.Box):
    def __init__(self, name, args=None, dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)
        self.args = args or ()

class Constant(closed.Box):
    def __init__(self, name="Γ", dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)

class Data(closed.Box):
    def __init__(self, dom=None, cod=None, value=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__("⌜-⌝", dom, cod)
        self.value = value

class Sequential(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(;)", dom, cod)

class Concurrent(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("(||)", dom, cod)

class Pair(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("⌈−,−⌉", dom, cod)

class Cast(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("Cast", dom, cod)

class Swap(closed.Box):
    def __init__(self, left, right):
        closed.Box.__init__(self, "σ", left @ right, right @ left)
        self.left, self.right = left, right

class Copy(closed.Box):
    def __init__(self, x, n=2):
        name = f"Copy({x}" + ("" if n == 2 else f", {n}") + ")"
        closed.Box.__init__(self, name, x, x ** n)
        self.n = n

class Discard(closed.Box):
    def __init__(self, dom):
        name = f"Discard({dom})"
        closed.Box.__init__(self, name, dom, closed.Ty())

class Trace(closed.Box):
    def __init__(self, arg, left=False):
        dom = arg.dom[:-1] if not left else arg.dom[1:]
        cod = arg.cod[:-1] if not left else arg.cod[1:]
        closed.Box.__init__(self, "Trace", dom, cod)
        self.arg = arg
        self.left = left

class Exec(closed.Box):
    def __init__(self, dom, cod):
        super().__init__("exec", dom, cod)

class Merge(closed.Box):
    def __init__(self, dom):
        name = f"Merge({dom})"
        # Merge multiple IO wires into one IO wire
        # Assuming cod is Language (IO)
        closed.Box.__init__(self, name, dom, Language)

Computation = closed.Category(closed.Ty, closed.Diagram)
