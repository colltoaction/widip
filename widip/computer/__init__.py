from __future__ import annotations
from typing import Any, Callable
from pathlib import Path
from discopy import closed

# Symbols are represented by ℙ
class Language(closed.Ty):
    def __init__(self, name: str = "ℙ"):
        super().__init__(name)

class Data(closed.Box):
    def __init__(self, value: Any, dom: closed.Ty = Language(), cod: closed.Ty = Language()):
        self.value = value
        content = str(value) if value else "-"
        name = f"⌜{content if len(content) < 100 else content[:97] + '...'}⌝"
        super().__init__(name, dom, cod)

class Program(closed.Box):
    def __init__(self, name: str, dom: closed.Ty = Language(), cod: closed.Ty = Language(), args: Any = ()):
        super().__init__(name, dom, cod)
        self.args = args

class Discard(closed.Box):
    def __init__(self, x: closed.Ty):
        super().__init__("ε", x, closed.Ty())
        self.draw_as_spider = True

from .composition import Sequential, Parallel
from .combinators import Partial

# The Computer Category
Computation = closed.Category(closed.Ty, closed.Diagram)

# Explicitly instantiate Language for from_callable
L = Language()

@closed.Diagram.from_callable(L, L)
def shell(diagram_source: Any) -> closed.Diagram:
    """Entry point for compiling YAML into computer diagrams (The Shell Functor)."""
    # This function is decorated, so it's treated as an arrow mapping for a functor
    # But `shell` is intended to be the COMPILER itself, which takes a source and returns a Diagram?
    # No, from_callable creates a Diagram/Hypergraph from the function logic if traced.
    # But `yaml.load` performs complex logic.
    
    # If the user wants `def shell()` as a top level from_callable, they likely imply:
    # `shell` IS the compiled diagram logic acting on inputs?
    # OR `shell` is the compiler function?
    
    # "SHELL_COMPILER" suggests it takes `diagram_source` (YAML/HIF) and returns a `Diagram`.
    # `from_callable` would mean `shell` defines a diagram.
    
    from .. import yaml
    
    # Apply the YAML loading pipeline using the local computer types
    res = yaml.load(diagram_source, computer_types=(Program, Data, Language, Computation))
    
    if isinstance(res, (closed.Box, Program, Data)):
         return closed.Id(res.dom) >> res
         
    return res

# Alias for backward compatibility if needed, but intended to replace SHELL_COMPILER
SHELL_COMPILER = shell

