from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from functools import singledispatch
from contextvars import ContextVar
from discopy import closed, python, symmetric
import widip.computer as comp

T = TypeVar("T")

# --- Process Definition ---

class Process(python.Function):
    """Wrapped function for composition."""
    def __init__(self, inside: Callable[..., Any], dom: closed.Ty, cod: closed.Ty):
        self.inside = inside
        self.dom, self.cod = dom, cod

    def __call__(self, *args): return self.inside(*args)

    @classmethod
    def from_callable(cls, diagram: closed.Diagram):
        def decorator(func):
            F = closed.Functor(ob=lambda x: x, ar=func, cod=python.Category(closed.Ty, Process))
            return F(diagram)
        return decorator

# --- Execution Context ---

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: Any):
        self.hooks, self.executable, self.loop = hooks, executable, loop

_EXEC_CTX: ContextVar[ExecContext] = ContextVar("exec_ctx")


# --- Execution Dispatcher ---

@singledispatch
def exec_dispatch(box: Any) -> Process:
    """Fallback identity process."""
    async def id_fn(*args): return args
    return Process(id_fn, box.dom, box.cod)

from . import exec as _exec

# Direct registrations using imported implementations
exec_dispatch.register(closed.Box, _exec.exec_box)
exec_dispatch.register(symmetric.Swap, _exec.exec_swap)
exec_dispatch.register(closed.Diagram, _exec.exec_diagram)

# Top-level API
def execute(diag: closed.Diagram, hooks: Dict[str, Callable], executable: str, loop: Any) -> Process:
    token = _EXEC_CTX.set(ExecContext(hooks, executable, loop))
    try: return exec_dispatch(diag)
    finally: _EXEC_CTX.reset(token)
