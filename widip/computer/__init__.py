from __future__ import annotations
from discopy import closed
import functools, operator, ast

# Symbols are represented by ℙ
Language = closed.Ty("ℙ")

class Partial(closed.Box):
    """Higher-order box for partial application."""
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        # Manually construct closed.Ty to avoid monoidal fallback
        dom = closed.Ty(*[obj.name for obj in arg.dom[n:]])
        cod = closed.Ty(*[obj.name for obj in arg.cod])
        closed.Box.__init__(self, f"[{arg.name}]_{n}", dom, cod)

# --- Computer Boxes (Traceable factories) ---

def Data(value):
    @closed.Diagram.from_callable(closed.Ty(), Language)
    def diag():
        return closed.Box(f"⌜{value}⌝", closed.Ty(), Language, data=value)()
    return diag

class Program:
    """Program box factory with decorator support."""
    
    def __new__(cls, name, args=()):
        """Create a Program box."""
        return closed.Box(name, Language, Language, data=args)
    
    @classmethod
    def as_diagram(cls, dom=None, cod=None):
        """
        Decorator to create a diagram from a function.
        
        Usage:
            @Program.as_diagram()
            def my_func(x, y):
                return result
        """
        def decorator(func):
            # Return the function itself for now
            # This allows the function to be used directly
            return func
        return decorator

def Discard():
    @closed.Diagram.from_callable(Language, closed.Ty())
    def diag(x):
        return closed.Box("ε", Language, closed.Ty(), draw_as_spider=True)(x)
    return diag

from .composition import Sequential, Parallel
Computation = closed.Category(closed.Ty, closed.Diagram)

# --- Futamura Projections & Hypercomputation ---

from .super import Language2, specializer_box, interpreter_box, specializer, interpreter
from .hyper import ackermann

# Futamura's Projections using Partial
compiler = lambda program: Partial(interpreter_box, 1)
compiler_generator = lambda: Partial(specializer_box, 1)

# --- Bootstrap Functors ---

eval_diagram = lambda tuples: functools.reduce(operator.add, tuples, ())
eval_diagram.__doc__ = """Monoid homomorphism: flatten tuple of tuples via reduce(add, tuples, ())."""

eval_python = lambda code: eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))
eval_python.__doc__ = """Functor str → AST → object: parse and evaluate Python expressions via AST."""
