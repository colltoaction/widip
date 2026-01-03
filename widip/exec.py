from __future__ import annotations
from typing import Any, TypeVar
from discopy import closed, symmetric
import widip.computer as comp
from .asyncio import run_command

# Import types/context from the package
import widip

def exec_box(box: closed.Box) -> widip.Process:
    """Executes a leaf box (Data or Program)."""
    if hasattr(box, 'data') and not isinstance(box.data, tuple): # Data box
        async def data_fn(*args): return box.data
        return widip.Process(data_fn, box.dom, box.cod)
    
    # Program box or structural box
    ctx = widip._EXEC_CTX.get()
    async def prog_fn(*args):
        args_data = box.data if hasattr(box, 'data') and isinstance(box.data, tuple) else ()
        stdin_val = args[0] if args else None
        if len(args) > 1: stdin_val = args
        return await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
    return widip.Process(prog_fn, box.dom, box.cod)

def exec_swap(box: symmetric.Swap) -> widip.Process:
    async def swap_fn(a, b): return (b, a)
    return widip.Process(swap_fn, box.dom, box.cod)

def exec_diagram(box: closed.Diagram) -> widip.Process:
    return widip.Process.from_callable(box)(widip.exec_dispatch)

# Compatibility
compile_exec = lambda diag, **kwargs: widip.exec_dispatch(diag)
