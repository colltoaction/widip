"""Hypercomputation features for computer module

Provides hypercomputation capabilities (infinite computations, oracles, etc.).
"""

from .core import Data, Program

def ackermann(m, n):
    """Ackermann function - classic example of primitive recursive function
    
    Args:
        m: First parameter
        n: Second parameter
        
    Returns:
        Ackermann(m, n)
    """
    if m == 0:
        return n + 1
    elif n == 0:
        return ackermann(m - 1, 1)
    else:
        return ackermann(m - 1, ackermann(m, n - 1))

class Oracle(Program):
    """Oracle for hypercomputation - can solve undecidable problems"""
    def __init__(self, problem):
        self.problem = problem
        super().__init__(f"Oracle[{problem}]")

__all__ = ['ackermann', 'Oracle']
