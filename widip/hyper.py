"""
Hypercomputation examples using primitive recursion and the Ackermann function.

The Ackermann function is a classic example of a total computable function that is not
primitive recursive, demonstrating the limits of primitive recursion.
"""

from discopy import closed
from .computer import Language

# Ackermann function: A(m, n)
# A(0, n) = n + 1
# A(m+1, 0) = A(m, 1)
# A(m+1, n+1) = A(m, A(m+1, n))

@closed.Diagram.from_callable(Language @ Language, Language)
def ackermann(m, n):
    """
    Ackermann function as a closed diagram.
    
    This is a total computable function that is not primitive recursive,
    serving as a canonical example of hypercomputation beyond primitive recursion.
    
    Type: Language @ Language → Language
    """
    return closed.Box("ackermann", Language @ Language, Language)(m, n)
