from discopy import closed, monoidal, symmetric
import functools
import operator
from typing import Any

# --- Core Types ---
# Use fixed Ob instance
ℙ_OB = closed.cat.Ob("ℙ")
Language = closed.Ty(ℙ_OB)
Language2 = Language.tensor(Language)

class Data(closed.Box):
    def __init__(self, name: Any, dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(str(name), dom, cod)

class Program(closed.Box):
    def __init__(self, name: str, args=None, dom=None, cod=None):
        if dom is None: dom = Language
        if cod is None: cod = Language
        super().__init__(name, dom, cod)
        self.args = args or []

class Partial(closed.Box):
    def __init__(self, name: str, dom=None, cod=None):
        super().__init__(str(name), dom or Language, cod or Language)

# --- Algebraic Operations ---
class Copy(closed.Box):
    """Copying data (Δ)."""
    def __init__(self, x=None, n=2):
        x = x or Language
        # Use power operator for types to ensure flat closed.Ty
        super().__init__("Δ", x, x ** n)
        self.n = n

class Merge(closed.Box):
    """Merging data (μ)."""
    def __init__(self, x=None, n=2):
        x = x or Language
        # Use power operator for types to ensure flat closed.Ty
        super().__init__("μ", x ** n, x)
        self.n = n

class Discard(closed.Box):
    """Discarding data (ε)."""
    def __init__(self, x=None):
        x = x or Language
        super().__init__("ε", x, closed.Ty())

# --- Core Combinator Diagrams ---
# Helper to wrap a box in a diagram by composing with identity
def box_to_diag(box):
    return box >> closed.Id(box.cod)

# Define as simple diagram objects
copy = box_to_diag(Copy(Language, 2))
merge = box_to_diag(Merge(Language, 2))
discard = box_to_diag(Discard(Language))

# eval_diagram is an alias for merge in the monoidal computer context
eval_diagram = merge

def eval_diagram_fn(x, y):
    """Functional version of eval_diagram."""
    return Merge(Language, 2)(x, y)

def eval_python(code: str):
    """Dynamic evaluator."""
    return eval(code)

class Titi:
    """Titi service objects."""
    read_stdin = Program("read_stdin", dom=closed.Ty(), cod=Language)
    printer = Program("print", dom=Language, cod=closed.Ty())

service_map = {
    "read_stdin": Titi.read_stdin,
    "print": Titi.printer
}

class Computation:
    """Stub for Computation category."""
    pass
