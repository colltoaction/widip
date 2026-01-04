"""Hypercomputation - Functions beyond primitive recursion."""

from discopy import closed
from .super import Language2, Language

# Ackermann function: total computable but not primitive recursive
ackermann = closed.Box("ackermann", Language2, Language)
