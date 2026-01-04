from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from discopy import closed, python, symmetric
from .asyncio import run_command, unwrap
from contextlib import contextmanager

T = TypeVar("T")
Process = python.Function

# --- Execution Context ---
_EXEC_CTX = __import__('contextvars').ContextVar("exec_ctx")

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: Any):
        self.hooks, self.executable, self.loop = hooks, executable, loop

# --- Leaf Execution ---

def exec_box(box: closed.Box) -> Process:
    """Executes a leaf box (Data or Program)."""
    # Use generic types for python category
    dom = any_ty(len(box.dom))
    cod = any_ty(len(box.cod))
    
    if hasattr(box, 'data') and not isinstance(box.data, tuple): # Data box
        async def data_fn(*args): return box.data
        return Process(data_fn, dom, cod)
    
    # Program box or structural box
    async def prog_fn(*args):
        ctx = _EXEC_CTX.get()
        args_data = box.data if hasattr(box, 'data') and isinstance(box.data, tuple) else ()
        stdin_val = args[0] if args else None
        if len(args) > 1: stdin_val = args
        return await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
    return Process(prog_fn, dom, cod)

def any_ty(n: int):
    """Returns a tensor of n object types."""
    res = python.Ty()
    for _ in range(n): res @= python.Ty(object)
    return res

def exec_swap(box: symmetric.Swap) -> Process:
    return Process(lambda a, b: (b, a), any_ty(2), any_ty(2))

# --- Dispatcher ---

def exec_dispatch(box: Any) -> Process:
    if isinstance(box, (closed.Box, symmetric.Box)):
        if isinstance(box, symmetric.Swap): return exec_swap(box)
        return exec_box(box)
    return Process.id(any_ty(getattr(box, 'dom', closed.Ty())))

def exec_functor(diag: closed.Diagram) -> Process:
    """Manual functor implementation to avoid DisCoPy version issues."""
    from discopy.closed import Functor
    # Map Language to Any in the python category
    f = Functor(ob={closed.Ty("P"): object}, ar=exec_dispatch, cod=python.Category())
    return f(diag)

async def execute(diag: closed.Diagram, hooks: dict, executable: str, loop: Any, stdin: Any = None):
    ctx = ExecContext(hooks, executable, loop)
    token = _EXEC_CTX.set(ctx)
    try:
        proc = exec_functor(diag)
        # Pass stdin to the process if it's expected
        arg = (stdin,) if proc.dom else ()
        res = await unwrap(loop, proc(*arg))
        return res
    finally:
        _EXEC_CTX.reset(token)

@contextmanager
def widip_runner(hooks: Dict[str, Callable], executable: str = "python3", loop: Any = None):
    """Context manager for the execution environment."""
    ctx = ExecContext(hooks, executable, loop)
    def runner(diag: closed.Diagram, stdin: Any = None):
        return execute(diag, hooks, executable, loop, stdin)
    yield runner, loop

# Legacy alias for tests
compile_exec = exec_functor

__all__ = ['execute', 'ExecContext', 'exec_dispatch', 'Process', 'widip_runner', 'compile_exec']
