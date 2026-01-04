from __future__ import annotations
from discopy import closed

class ComputerType(closed.Ty):
    """
    Metaprogramming-enabled type system for the Monoidal Computer.
    """
    def __getattr__(self, name: str):
        from .computer import service_map
        if name in service_map:
            return service_map[name]()
        raise AttributeError(f"Type '{self}' has no computer service '{name}'")

# The program type ℙ (Language)
Language = ComputerType("ℙ")
Language2 = Language @ Language
