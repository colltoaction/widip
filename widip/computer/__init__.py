"""
Monoidal Computer - Categorical Computability Implementation
=============================================================

Based on "Programs as Diagrams: From Categorical Computability to Computable Categories"
by Dusko Pavlovic (arXiv:2208.03817v4)
"""

from __future__ import annotations
from discopy import closed
import functools, operator, ast
from typing import Callable, Any, TypeVar, Generic
from ..core import Language, Language2, ComputerType

# =============================================================================
# § 2.1 - Core Types and Metaprogramming
# =============================================================================

def service(name: str, dom: closed.Ty, cod: closed.Ty, **kwargs):
    """Metaprogramming helper to define data services."""
    def factory(*args, **f_kwargs):
        @closed.Diagram.from_callable(dom, cod)
        def diag(*x):
            return ComputerBox(name, dom, cod, **kwargs)(*x)
        return diag
    return factory

class ComputerBox(closed.Box):
    """Base class for all computer boxes with metaprogramming enhancements."""
    def __init__(self, name: str, dom: closed.Ty, cod: closed.Ty, **kwargs):
        super().__init__(name, dom, cod, **kwargs)

    def __rshift__(self, other):
        """Metaprogramming: chain computations with >>."""
        if isinstance(other, ComputerBox):
            return self >> other
        return super().__rshift__(other)

# § 2.1 - Data Services
Copy = service("Δ", Language, Language @ Language, draw_as_spider=True)
Discard = service("ε", Language, closed.Ty(), draw_as_spider=True)
Swap = service("ς", Language @ Language, Language @ Language, draw_as_spider=True)

# Service map for ComputerType metaprogramming
service_map = {
    "Copy": Copy,
    "Discard": Discard,
    "Swap": Swap,
}

# =============================================================================
# § 2.2 - Universal Evaluators
# =============================================================================

class Eval(ComputerBox):
    """Program Evaluator {−} : ℙ × A → B"""
    def __init__(self, dom_type=Language, cod_type=Language):
        super().__init__("{−}", Language @ dom_type, cod_type)

class PartialEval(ComputerBox):
    """Partial Evaluator [−] : ℙ × A → ℙ"""
    def __init__(self):
        super().__init__("[−]", Language @ Language, Language)

# =============================================================================
# § 2.3 - Data and Programs
# =============================================================================

def Data(value: Any):
    """Encodes data as programs: ⌜value⌝."""
    @closed.Diagram.from_callable(closed.Ty(), Language)
    def diag():
        return ComputerBox(f"⌜{value}⌝", closed.Ty(), Language, data=value)()
    return diag

class Program:
    """Metaprogramming factory for programs."""
    def __new__(cls, name: str, args=()):
        return ComputerBox(name, Language, Language, data=args)
    
    @staticmethod
    def as_diagram(dom=None, cod=None):
        def decorator(func):
            return func
        return decorator

class Partial(ComputerBox):
    """Partial application [f]ₙ."""
    def __init__(self, arg: closed.Diagram, n: int = 1):
        dom = closed.Ty(*[obj.name for obj in arg.dom[n:]])
        cod = closed.Ty(*[obj.name for obj in arg.cod])
        super().__init__(f"[{arg.name}]_{n}", dom, cod)

# =============================================================================
# § 2.4 - Logic and Numbers
# =============================================================================

def constant(name: str, cod=Language, **kwargs):
    return ComputerBox(name, closed.Ty(), cod, **kwargs)

TRUE = constant("⊤", draw_as_spider=True)
FALSE = constant("⊥", draw_as_spider=True)
ZERO = constant("0")

IFTE = lambda: ComputerBox("ifte", Language @ Language @ Language, Language)
ProgramEq = lambda: ComputerBox("=?", Language @ Language, Language)

SUCC = ComputerBox("s", Language, Language)
PRED = ComputerBox("r", Language, Language)
ISZERO = ComputerBox("0?", Language, Language)

class NaturalNumber(ComputerBox):
    def __init__(self, n: int):
        super().__init__(str(n), closed.Ty(), Language, data=n)

# =============================================================================
# § 3 & 4 - Fixpoints and Recursion
# =============================================================================

class Schema(ComputerBox):
    """Metaprogramming base for recursion schemas."""
    def __init__(self, name: str, dom: closed.Ty, cod: closed.Ty, *args):
        super().__init__(name.format(*args), dom, cod)

KleeneFixpoint = lambda name: Schema("fix({})", Language, Language, name)
YCombinator = lambda: ComputerBox("Υ", Language, Language)
Induction = lambda b, q: Schema("⟦{}, {}⟧", Language, Language, b, q)
Recursion = lambda g, h: Schema("⟦{}, {}⟧", Language @ Language, Language, g, h)
Minimization = lambda p: Schema("μ{}", Language, Language, p)
WhileLoop = lambda t, b: Schema("while({}, {})", Language @ Language, Language, t, b)

# =============================================================================
# § 6 - Metaprogramming (Futamura Projections)
# =============================================================================

specializer_box = ComputerBox("specializer", Language2, Language)
interpreter_box = ComputerBox("interpreter", Language2, Language)
ackermann = ComputerBox("ackermann", Language2, Language)

class Metaprogramming:
    """Futamura projections using metaprogramming."""
    @property
    def compiler(self): return Partial(interpreter_box, 1)
    @property
    def compiler_generator(self): return Partial(specializer_box, 1)
    @property
    def compiler_compiler(self): return Partial(specializer_box, 1)

meta = Metaprogramming()

# =============================================================================
# § Categories and Bootstrap
# =============================================================================

Computation = closed.Category(closed.Ty, closed.Diagram)

def eval_diagram(tuples):
    """Monoid homomorphism: flatten tuple of tuples via reduce(add, tuples, ())."""
    return functools.reduce(operator.add, tuples, ())

def eval_python(code: str):
    """Functor str → AST → object: parse and evaluate Python expressions via AST."""
    return eval(compile(ast.parse(code, mode='eval'), '<string>', 'eval'))

def eval_yaml(source: str):
    """Functor: parse and evaluate YAML source into a diagram."""
    from ..yaml import load
    return load(source)

__all__ = [
    'Language', 'Language2', 'Computation',
    'Copy', 'Discard', 'Swap',
    'Eval', 'PartialEval',
    'Data', 'Program', 'Partial',
    'TRUE', 'FALSE', 'IFTE', 'ProgramEq',
    'ZERO', 'SUCC', 'PRED', 'ISZERO', 'NaturalNumber',
    'Induction', 'Recursion', 'Minimization', 'WhileLoop',
    'KleeneFixpoint', 'YCombinator',
    'compiler', 'compiler_generator', 'compiler_compiler',
    'specializer', 'interpreter', 'ackermann',
    'eval_diagram', 'eval_python', 'eval_yaml', 'meta'
]

# Map properties for backward compatibility
compiler = lambda: meta.compiler
compiler_generator = lambda: meta.compiler_generator
compiler_compiler = lambda: meta.compiler_compiler
specializer = lambda program, arg: specializer_box
interpreter = lambda program, arg: interpreter_box
