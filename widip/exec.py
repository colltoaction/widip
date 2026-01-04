from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from discopy import closed, python, symmetric
from .asyncio import run_command

T = TypeVar("T")

# --- Execution Context ---

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: Any):
        self.hooks, self.executable, self.loop = hooks, executable, loop

_EXEC_CTX = __import__('contextvars').ContextVar("exec_ctx")

# --- Dispatch Item Implementations ---

def exec_box(box: closed.Box) -> Process:
    """Executes a leaf box (Data or Program)."""
    if hasattr(box, 'data') and not isinstance(box.data, tuple): # Data box
        async def data_fn(*args): return box.data
        return Process(data_fn, box.dom, box.cod)
    
    # Program box or structural box
    import widip
    ctx = widip._EXEC_CTX.get()
    async def prog_fn(*args):
        args_data = box.data if hasattr(box, 'data') and isinstance(box.data, tuple) else ()
        stdin_val = args[0] if args else None
        if len(args) > 1: stdin_val = args
        return await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
    return Process(prog_fn, box.dom, box.cod)

def exec_swap(box: symmetric.Swap) -> Process:
    async def swap_fn(a, b): return (b, a)
    return Process(swap_fn, box.dom, box.cod)

# Compatibility
compile_exec = lambda diag, **kwargs: __import__('widip').exec_dispatch(diag)
