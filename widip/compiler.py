from __future__ import annotations
from typing import Any, Callable
from pathlib import Path
from discopy import closed
from . import computer, yaml

def SHELL_COMPILER(diagram_source: Any, compiler_fn: Callable, path: str | None = None) -> closed.Diagram:
    """Entry point for compiling YAML into computer diagrams."""
    
    # Apply the YAML loading pipeline
    res = yaml.load(diagram_source)
    
    # Ensure it's a closed diagram
    if isinstance(res, (closed.Box, computer.Program, computer.Data)):
         res = closed.Id(res.dom) >> res
    
    if path is not None and __debug__:
        from .drawing import diagram_draw
        diagram_draw(Path(path).with_suffix(".shell.yaml"), res)
    
    return res
