from discopy import closed
from .core import Language, Language2

def ackermann_impl(m: int, n: int) -> int:
    """Pure implementation of the Ackermann function."""
    if m == 0:
        return n + 1
    if n == 0:
        return ackermann_impl(m - 1, 1)
    return ackermann_impl(m - 1, ackermann_impl(m, n - 1))
