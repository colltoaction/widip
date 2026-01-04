from __future__ import annotations
from discopy import closed

# Use ASCII for compatibility and ensure it's a closed.Ty
Language = closed.Ty("P")
Language2 = Language @ Language

class ComputerMetaclass(type):
    def __getattr__(cls, name: str):
        from .computer import service_map
        if name in service_map:
            return service_map[name]()
        raise AttributeError(f"Computer has no service '{name}'")

class Computer(metaclass=ComputerMetaclass):
    """
    User-facing interface for the Monoidal Computer.
    """
    pass
