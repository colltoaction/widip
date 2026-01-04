from discopy import closed
from .core import Language, Language2

def _ackermann_impl(m: int, n: int) -> int:
    """Pure implementation of the Ackermann function."""
    if m == 0:
        return n + 1
    if n == 0:
        return _ackermann_impl(m - 1, 1)
    return _ackermann_impl(m - 1, _ackermann_impl(m, n - 1))

# Create ackermann as a closed.Box with type ℙ ⊗ ℙ → ℙ
ackermann = closed.Box("ackermann", Language2, Language)
