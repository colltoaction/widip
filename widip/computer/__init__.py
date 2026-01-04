"""
Monoidal Computer - Categorical Computability Implementation
=============================================================

Based on "Programs as Diagrams: From Categorical Computability to Computable Categories"
by Dusko Pavlovic (arXiv:2208.03817v4)

This module implements the theoretical framework of monoidal computers where:
- Programs are elements of type ℙ (Language)
- Computations are morphisms in a monoidal category
- Program evaluation is a universal natural operation
- All computable functions are programmable

Core Concepts:
--------------
1. **Monoidal Computer** (Ch. 2): A symmetric monoidal category with:
   - Data services (copying Δ, deletion ε)
   - Program type ℙ with decidable equality
   - Universal program evaluators {−} : ℙ × A → B

2. **Fixpoints** (Ch. 3): Every computable function has fixpoints
   - Kleene fixpoints: g(Γ, y) = {Γ}y (Fundamental Theorem)
   - Y-combinators for constructing fixpoints
   - Systems of program equations (Smullyan fixpoints)

3. **Recursion & Induction** (Ch. 4): Computing by counting
   - Natural numbers as programs
   - Induction: ⟦b, q⟧ : ℕ → B
   - Recursion: ⟦g, h⟧ : ℕ × A → B
   - Search & minimization: μn.(ϕₙ(x) = 0)

4. **Undecidability** (Ch. 5): Rice's Theorem
   - Decidable extensional predicates are constant
   - Halting problem is undecidable
   - No general decision procedure for program properties

5. **Metaprogramming** (Ch. 6): Programs computing programs
   - Compilation and supercompilation
   - Futamura projections (3 levels)
   - Hypercomputation (Ackermann function)
"""

from __future__ import annotations
from discopy import closed
import functools, operator, ast
from typing import Callable, Any

# =============================================================================
# § 2.1 - Core Types and Data Services
# =============================================================================

# The program type ℙ (Language) - represents all programs
Language = closed.Ty("ℙ")

def Copy():
    """
    Copying Δ : A → A × A (data service)
    Allows duplicating values for reuse in computations.
    Ref: Section 1.2, equation (1.1)
    """
    @closed.Diagram.from_callable(Language, Language @ Language)
    def diag(x):
        return closed.Box("Δ", Language, Language @ Language, draw_as_spider=True)(x)
    return diag

def Discard():
    """
    Deletion ε : A → I (data service)
    Allows discarding unused values.
    Ref: Section 1.2, equation (1.1)
    """
    @closed.Diagram.from_callable(Language, closed.Ty())
    def diag(x):
        return closed.Box("ε", Language, closed.Ty(), draw_as_spider=True)(x)
    return diag

def Swap():
    """
    Twist ς : A × B → B × A
    Reorders data in products.
    Ref: Section 1.1.3, Figure 1.4
    """
    @closed.Diagram.from_callable(Language @ Language, Language @ Language)
    def diag(x, y):
        return closed.Box("ς", Language @ Language, Language @ Language, draw_as_spider=True)(x, y)
    return diag

# =============================================================================
# § 2.2 - Program Evaluation (Universal Evaluators)
# =============================================================================

class Eval(closed.Box):
    """
    Program Evaluator {−} : ℙ × A → B
    
    Universal property: For any g : X × A → B, there exists G : X → ℙ such that
        g(x, a) = {G(x)}(a)
    
    This is the "running" surjection from Fig. 3 and equation (2.2).
    Ref: Section 2.2.1, Definition
    """
    def __init__(self, dom_type=Language, cod_type=Language):
        self.dom_type = dom_type
        self.cod_type = cod_type
        closed.Box.__init__(self, "{−}", Language @ dom_type, cod_type)

class PartialEval(closed.Box):
    """
    Partial Evaluator [−] : ℙ × A → ℙ
    
    Satisfies: {[Γ](y)}(a) = {Γ}(y, a)
    Used for specialization and metaprogramming.
    Ref: Section 2.2.2, Figure 2.5
    """
    def __init__(self):
        closed.Box.__init__(self, "[−]", Language @ Language, Language)

# =============================================================================
# § 2.3 - Data and Programs
# =============================================================================

def Data(value):
    """
    Data encoding ⌜−⌝ : A → ℙ
    
    Encodes data as programs. Every type A is a retract of ℙ.
    Ref: Section 2.3.1, equation (2.6)
    """
    @closed.Diagram.from_callable(closed.Ty(), Language)
    def diag():
        return closed.Box(f"⌜{value}⌝", closed.Ty(), Language, data=value)()
    return diag

class Program:
    """
    Program box factory with decorator support.
    
    Programs are elements of ℙ. Types are idempotents on ℙ.
    Ref: Section 2.3.2, equations (2.8-2.9)
    """
    
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
            return func
        return decorator

class Partial(closed.Box):
    """
    Partial application [f]ₙ : Aₙ₊₁ × ... × Aₘ → B
    
    For f : A₁ × ... × Aₘ → B, partially applies first n arguments.
    Ref: Section 6.2.2, Futamura projections
    """
    def __init__(self, arg: closed.Diagram, n: int = 1, left: bool = True):
        self.arg, self.n, self.left = arg, n, left
        dom = closed.Ty(*[obj.name for obj in arg.dom[n:]])
        cod = closed.Ty(*[obj.name for obj in arg.cod])
        closed.Box.__init__(self, f"[{arg.name}]_{n}", dom, cod)

# =============================================================================
# § 2.4 - Logic and Equality
# =============================================================================

# Truth values (Section 2.4.1)
TRUE = closed.Box("⊤", closed.Ty(), Language, draw_as_spider=True)
FALSE = closed.Box("⊥", closed.Ty(), Language, draw_as_spider=True)

def IFTE():
    """
    Branching: if-then-else
    
    ifte(b, x, y) = x if b = ⊤, else y
    Ref: Section 2.4.1, equation (2.12)
    """
    return closed.Box("ifte", Language @ Language @ Language, Language)

def ProgramEq():
    """
    Program equality (=?) : ℙ × ℙ → 𝔹
    
    Decidable predicate capturing program equality.
    Ref: Section 2.4.2, equation (2.13)
    """
    return closed.Box("=?", Language @ Language, Language)

# =============================================================================
# § 3 - Fixpoints (Fundamental Theorem of Computation)
# =============================================================================

class KleeneFixpoint(closed.Box):
    """
    Kleene Fixpoint: For g : ℙ × A → B, constructs Γ : ℙ such that
        g(Γ, y) = {Γ}(y)
    
    The Fundamental Theorem of Computation (Kleene's Second Recursion Theorem).
    Ref: Section 3.3, Theorem and Figure 3.6
    """
    def __init__(self, func_name: str):
        self.func_name = func_name
        closed.Box.__init__(self, f"fix({func_name})", Language, Language)

class YCombinator(closed.Box):
    """
    Y-Combinator Υ : ℙ → ℙ
    
    Constructs Kleene fixpoints: {Υ(p)}(x) = {p}({Υ(p)}, x)
    Ref: Section 3.4.1, equation (3.17)
    """
    def __init__(self):
        closed.Box.__init__(self, "Υ", Language, Language)

def Quine():
    """
    Polymorphic Quine: A program that outputs its own text.
    
    {Q}(x) = Q
    Ref: Section 3.3.1
    """
    return closed.Box("quine", Language, Language)

# =============================================================================
# § 4 - Numbers and Recursion
# =============================================================================

# Natural numbers (Section 4.2)
ZERO = closed.Box("0", closed.Ty(), Language)
SUCC = closed.Box("s", Language, Language)  # Successor: n ↦ n+1
PRED = closed.Box("r", Language, Language)  # Predecessor: n ↦ n-1
ISZERO = closed.Box("0?", Language, Language)  # Zero test

class NaturalNumber(closed.Box):
    """
    Natural number as a program.
    
    Numbers are built by counting: n = sⁿ(0)
    Ref: Section 4.2.3, equations (4.5-4.7)
    """
    def __init__(self, n: int):
        self.n = n
        closed.Box.__init__(self, str(n), closed.Ty(), Language, data=n)

class Induction(closed.Box):
    """
    Induction schema ⟦b, q⟧ : ℕ → B
    
    Defined by:
        ⟦b, q⟧(0) = b
        ⟦b, q⟧(n+1) = q(⟦b, q⟧(n))
    
    Ref: Section 4.3.2, equations (4.13-4.14)
    """
    def __init__(self, base_name: str, step_name: str):
        self.base_name = base_name
        self.step_name = step_name
        closed.Box.__init__(self, f"⟦{base_name}, {step_name}⟧", Language, Language)

class Recursion(closed.Box):
    """
    Recursion schema ⟦g, h⟧ : ℕ × A → B
    
    Defined by:
        ⟦g, h⟧(0, x) = g(x)
        ⟦g, h⟧(n+1, x) = hₙ(⟦g, h⟧(n, x), x)
    
    Ref: Section 4.3.4, equations (4.18-4.19)
    """
    def __init__(self, base_name: str, step_name: str):
        self.base_name = base_name
        self.step_name = step_name
        closed.Box.__init__(self, f"⟦{base_name}, {step_name}⟧", Language @ Language, Language)

class Minimization(closed.Box):
    """
    Unbounded search / Minimization μn.(ϕₙ(x) = 0)
    
    Searches for the smallest n such that ϕₙ(x) = 0.
    May diverge if no such n exists.
    Ref: Section 4.4.1, equation (4.24)
    """
    def __init__(self, predicate_name: str):
        self.predicate_name = predicate_name
        closed.Box.__init__(self, f"μ{predicate_name}", Language, Language)

class WhileLoop(closed.Box):
    """
    While loop: while t(x, b) do h(x, b)
    
    Iterates h while predicate t holds.
    Ref: Section 4.4.2
    """
    def __init__(self, test_name: str, body_name: str):
        self.test_name = test_name
        self.body_name = body_name
        closed.Box.__init__(self, f"while({test_name}, {body_name})", Language @ Language, Language)

# =============================================================================
# § 6 - Metaprogramming and Supercompilation
# =============================================================================

from .composition import Sequential, Parallel

# Two-argument Language type
Language2 = Language @ Language

# Core boxes for metaprogramming
specializer_box = closed.Box("specializer", Language2, Language)
interpreter_box = closed.Box("interpreter", Language2, Language)

# Ackermann function: total computable but not primitive recursive
ackermann = closed.Box("ackermann", Language2, Language)

@Program.as_diagram()
def specializer(program, arg):
    """Partial evaluator / Specializer."""
    return specializer_box

@Program.as_diagram()
def interpreter(program, arg):
    """Interpreter for meta-compilation."""
    return interpreter_box

# Futamura's Three Projections (Section 6.2.2)

def compiler(program):
    """
    First Futamura Projection: Compilation by partial evaluation
    
    C₁(X) = [H]_L(X)
    
    Compiles high-level program X to low-level by partially evaluating
    the interpreter H on X.
    Ref: Section 6.2.2, Figure 6.3, equation (1)
    """
    return Partial(interpreter_box, 1)

def compiler_generator():
    """
    Second Futamura Projection: Compiler generator
    
    C₂ = [S]_L(H)
    
    Generates a compiler by partially evaluating the specializer S
    on the interpreter H.
    Ref: Section 6.2.2, Figure 6.4, equation (3)
    """
    return Partial(specializer_box, 1)

def compiler_compiler():
    """
    Third Futamura Projection: Compiler-compiler
    
    C₃ = [S]_L(S)
    
    Generates a compiler generator by partially evaluating the
    specializer S on itself.
    Ref: Section 6.2.2, Figure 6.5, equation (5)
    """
    return Partial(specializer_box, 1)

# =============================================================================
# § Composition and Categories
# =============================================================================

Computation = closed.Category(closed.Ty, closed.Diagram)

# =============================================================================
# =============================================================================
# § Bootstrap Functors (Evaluation)
# =============================================================================

from .py import eval_python
from .yaml import eval_yaml as eval_diagram

# =============================================================================
# § Public API
# =============================================================================

__all__ = [
    # Core types
    'Language', 'Language2', 'Computation',
    
    # Data services (§2.1)
    'Copy', 'Discard', 'Swap',
    
    # Program evaluation (§2.2)
    'Eval', 'PartialEval',
    
    # Data and programs (§2.3)
    'Data', 'Program', 'Partial',
    
    # Logic (§2.4)
    'TRUE', 'FALSE', 'IFTE', 'ProgramEq',
    
    # Fixpoints (§3)
    'KleeneFixpoint', 'YCombinator', 'Quine',
    
    # Numbers and recursion (§4)
    'ZERO', 'SUCC', 'PRED', 'ISZERO', 'NaturalNumber',
    'Induction', 'Recursion', 'Minimization', 'WhileLoop',
    
    # Metaprogramming (§6)
    'compiler', 'compiler_generator', 'compiler_compiler',
    'specializer', 'interpreter', 'ackermann',
    
    # Composition
    'Sequential', 'Parallel',
    
    # Evaluation
    'eval_diagram', 'eval_python',
]

