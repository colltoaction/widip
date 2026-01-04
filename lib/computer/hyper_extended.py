"""
Extended Hypercomputation for the Monoidal Computer

This module implements hypercomputational functions that go beyond
primitive recursion, including:
- Ackermann function (grows faster than any primitive recursive function)
- Busy Beaver function (uncomputable)
- Ordinal hierarchies
- Transfinite recursion

These demonstrate the monoidal computer's ability to represent
and reason about computation at the limits of computability.
"""

from __future__ import annotations
from typing import Any
from discopy import closed
from .core import Language, Language2, Program, Data, Copy, Merge
from .hyper import ackermann_impl
import sys


# Increase recursion limit for Ackermann computation
sys.setrecursionlimit(10000)


# --- Busy Beaver Function ---

def busy_beaver_impl(n: int) -> int:
    """
    Busy Beaver function BB(n): the maximum number of steps that an
    n-state Turing machine can execute before halting.
    
    This function is uncomputable - we can only compute it for small n.
    
    Known values:
    - BB(1) = 1
    - BB(2) = 6
    - BB(3) = 21
    - BB(4) = 107
    - BB(5) >= 47,176,870
    - BB(6) > 10^36,534
    """
    known_values = {
        1: 1,
        2: 6,
        3: 21,
        4: 107,
        5: 47176870,  # Lower bound
    }
    
    if n in known_values:
        return known_values[n]
    else:
        raise ValueError(f"BB({n}) is unknown/uncomputable")


# --- Ordinal Hierarchies ---

class OrdinalNotation:
    """
    Representation of ordinals using Cantor Normal Form.
    
    An ordinal α can be written as:
    α = ω^β₁·c₁ + ω^β₂·c₂ + ... + ω^βₙ·cₙ
    where β₁ > β₂ > ... > βₙ and cᵢ are natural numbers.
    """
    
    def __init__(self, terms: list[tuple[Any, int]]):
        """
        Initialize ordinal from list of (exponent, coefficient) pairs.
        
        Args:
            terms: List of (β, c) where β is an ordinal and c is a coefficient
        """
        self.terms = terms
    
    def __str__(self) -> str:
        if not self.terms:
            return "0"
        
        parts = []
        for exp, coef in self.terms:
            if exp == 0:
                parts.append(str(coef))
            elif coef == 1:
                parts.append(f"ω^{exp}")
            else:
                parts.append(f"ω^{exp}·{coef}")
        
        return " + ".join(parts)
    
    def __lt__(self, other: 'OrdinalNotation') -> bool:
        """Ordinal comparison."""
        # Lexicographic comparison on terms
        for (e1, c1), (e2, c2) in zip(self.terms, other.terms):
            if e1 != e2:
                return e1 < e2
            if c1 != c2:
                return c1 < c2
        return len(self.terms) < len(other.terms)
    
    @staticmethod
    def omega() -> 'OrdinalNotation':
        """The first infinite ordinal ω."""
        return OrdinalNotation([(1, 1)])
    
    @staticmethod
    def epsilon_0() -> 'OrdinalNotation':
        """ε₀ = ω^ω^ω^... (first fixed point of α ↦ ω^α)."""
        # Represented symbolically
        return OrdinalNotation([("ε₀", 1)])


# --- Fast-Growing Hierarchy ---

def fast_growing(alpha: int, n: int) -> int:
    """
    Fast-growing hierarchy f_α(n).
    
    - f₀(n) = n + 1
    - f_{α+1}(n) = f_α^n(n) (apply f_α n times)
    - f_λ(n) = f_{λ[n]}(n) for limit ordinals λ
    
    This hierarchy eventually dominates all computable functions.
    """
    if alpha == 0:
        return n + 1
    
    # For finite ordinals, use simple recursion
    result = n
    for _ in range(n):
        result = fast_growing(alpha - 1, result)
    return result


# --- Transfinite Recursion ---

def transfinite_recursion(
    base_case: Any,
    successor_fn: callable,
    limit_fn: callable,
    ordinal: OrdinalNotation
) -> Any:
    """
    Perform transfinite recursion up to a given ordinal.
    
    Args:
        base_case: Value at ordinal 0
        successor_fn: Function to compute value at α+1 from value at α
        limit_fn: Function to compute value at limit ordinal λ from sequence
        ordinal: Target ordinal
    
    Returns:
        Value computed at the given ordinal
    """
    if not ordinal.terms:  # ordinal = 0
        return base_case
    
    # For simplicity, only handle finite ordinals in this implementation
    if len(ordinal.terms) == 1 and ordinal.terms[0][0] == 0:
        # Finite ordinal n
        n = ordinal.terms[0][1]
        result = base_case
        for _ in range(n):
            result = successor_fn(result)
        return result
    
    # For infinite ordinals, would need limit_fn
    raise NotImplementedError("Infinite ordinals not yet implemented")


# --- Goodstein Sequences ---

def goodstein_sequence(n: int, max_steps: int = 100) -> list[int]:
    """
    Goodstein sequence starting from n.
    
    Despite starting with any positive integer, all Goodstein sequences
    eventually reach 0. However, this can take an astronomically long time.
    
    The proof requires transfinite induction up to ε₀.
    """
    def hereditary_base_n(num: int, base: int) -> list[int]:
        """Convert number to hereditary base-n notation."""
        if num == 0:
            return []
        result = []
        while num > 0:
            result.append(num % base)
            num //= base
        return result
    
    sequence = [n]
    current = n
    base = 2
    
    for _ in range(max_steps):
        if current == 0:
            break
        
        # Convert to hereditary base, bump base, subtract 1
        base += 1
        # Simplified: just subtract 1 (full implementation would do hereditary conversion)
        current = max(0, current - 1)
        sequence.append(current)
    
    return sequence


# --- Hypercomputation Combinators ---

def iterate_omega(f: closed.Diagram) -> closed.Diagram:
    """
    Iterate a function ω times (transfinitely).
    
    This is a symbolic representation - actual execution would require
    a limit process.
    """
    # Create a symbolic box representing ω-iteration
    omega_iter = closed.Box("ω-iterate", f.cod, f.cod)
    return f >> omega_iter


def diagonal(f: closed.Diagram) -> closed.Diagram:
    """
    Diagonalization: apply a function to its own encoding.
    
    This is the key to constructing undecidable problems and
    self-referential structures.
    """
    # Copy the function, then apply it to itself
    copy = Copy(Language, 2)
    merge = Merge(Language, 2)
    
    # f @ f >> merge gives f(f)
    return (f @ f) >> merge


__all__ = [
    'ackermann_impl',
    'busy_beaver_impl',
    'OrdinalNotation',
    'fast_growing',
    'transfinite_recursion',
    'goodstein_sequence',
    'iterate_omega',
    'diagonal',
]
