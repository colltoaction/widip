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
        self.args = args or []
        super().__init__(name, dom, cod, data=self.args)

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

def make_copy(n: int, x=None):
    return Copy(x, n)

def make_merge(n: int, x=None):
    return Merge(x, n)

# --- Core Combinator Diagrams ---
# Note: copy, merge, discard are now defined in services.yaml
# Kept here for backwards compatibility as class definitions

def eval_diagram_fn(x, y):
    """Functional version of eval_diagram."""
    return Merge(Language, 2)(x, y)

def eval_python(code: str):
    """Dynamic evaluator."""
    return eval(code)

class Titi:
    """Titi service objects - now defined in services.yaml."""
    # These are kept for backwards compatibility but should use YAML definitions
    read_stdin = Program("read_stdin", dom=closed.Ty(), cod=Language)
    printer = Program("print", dom=Language, cod=closed.Ty())

service_map = {
    "read_stdin": Titi.read_stdin,
    "print": Titi.printer
}

class Computation:
    """Stub for Computation category."""
    pass
