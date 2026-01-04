from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from discopy import closed, python, symmetric
from .asyncio import run_command, unwrap
from contextlib import contextmanager
import discopy

T = TypeVar("T")
Process = python.Function

# --- Execution Context ---
_EXEC_CTX = __import__('contextvars').ContextVar("exec_ctx")

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: Any):
        self.hooks, self.executable, self.loop = hooks, executable, loop
        self.anchors = {}

# --- Leaf Execution ---

def exec_box(box: closed.Box) -> Process:
    """Executes a leaf box (Data or Program)."""
    dom = any_ty(len(box.dom))
    cod = any_ty(len(box.cod))
    
    # Check for Data box (Identity with value)
    if not hasattr(box, 'args'):
        async def data_fn(*args):
            ctx = _EXEC_CTX.get()
            # Special case for ℙ -> ℙ data boxes (Identity/Pass-through)
            if args:
                 val = await unwrap(ctx.loop, args[0])
                 if val is None: return None
            return box.name
        return Process(data_fn, dom, cod)
    
    # Program box logic
    async def prog_fn(*args):
        ctx = _EXEC_CTX.get()
        unwrapped_args = []
        for stage in args:
            unwrapped_args.append(await unwrap(ctx.loop, stage))
        
        # Choice/Guard logic: skip on None input
        if len(dom) > 0 and unwrapped_args and unwrapped_args[0] is None:
             return None
        
        args_data = box.args if hasattr(box, 'args') else ()
        stdin_val = unwrapped_args[0] if unwrapped_args else None
        if len(unwrapped_args) > 1: stdin_val = unwrapped_args
        
        # Intercept Special Commands
        if box.name == "anchor":
            name, inside = args_data
            ctx.anchors[name] = inside
            return await execute(inside, ctx.hooks, ctx.executable, ctx.loop, stdin_val)
            
        if box.name == "alias":
            name = args_data[0]
            if name not in ctx.anchors:
                raise ValueError(f"Unknown anchor: {name}")
            return await execute(ctx.anchors[name], ctx.hooks, ctx.executable, ctx.loop, stdin_val)

        if box.name == "print":
             from .asyncio import printer
             await printer(None, stdin_val, ctx.hooks)
             # Return () if codomain is empty, else return value
             return () if not cod else stdin_val

        if box.name == "read_stdin":
             return ctx.hooks['stdin_read']()

        return await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
    return Process(prog_fn, dom, cod)

def any_ty(n: int):
    return python.Ty(n * [object])

def exec_swap(box: symmetric.Swap) -> Process:
    async def swap_fn(a, b):
        ctx = _EXEC_CTX.get()
        return (await unwrap(ctx.loop, b), await unwrap(ctx.loop, a))
    return Process(swap_fn, any_ty(len(box.dom)), any_ty(len(box.cod)))

# --- Dispatcher ---

def exec_dispatch(box: Any) -> Process:
    if isinstance(box, (closed.Box, symmetric.Box)):
        if isinstance(box, symmetric.Swap): return exec_swap(box)
        if hasattr(box, 'name'):
            if box.name == "Δ": return exec_copy(box)
            if box.name == "μ": return exec_merge(box)
            if box.name == "ε": return exec_discard(box)
        return exec_box(box)
    return Process.id(any_ty(getattr(box, 'dom', closed.Ty())))

# --- Core Combinators Execution ---

def exec_copy(box: closed.Box) -> Process:
    n = getattr(box, 'n', 2)
    def copy_fn(x):
        loop = _EXEC_CTX.get().loop
        from .asyncio import unwrap
        import io
        async def loader():
             val = await unwrap(loop, x)
             if val is None: return (None,) * n
             if hasattr(val, 'read'):
                  content = await val.read()
                  return tuple(io.BytesIO(content) for _ in range(n))
             return (val,) * n
        task = loop.create_task(loader())
        async def getter(i):
             res_tuple = await task
             return res_tuple[i]
        return tuple(getter(i) for i in range(n))
    return Process(copy_fn, any_ty(1), any_ty(n))

def exec_merge(box: closed.Box) -> Process:
    """Handles merging (μ). Prioritizes last non-None result."""
    n = getattr(box, 'n', 2)
    async def merge_fn(*args):
        from .asyncio import unwrap
        loop = _EXEC_CTX.get().loop
        results = [await unwrap(loop, a) for a in args]
        for r in reversed(results):
            if r is not None: return r
        return None
    return Process(merge_fn, any_ty(n), any_ty(1))

def exec_discard(box: closed.Box) -> Process:
    async def discard_fn(*args):
        from .asyncio import unwrap
        loop = _EXEC_CTX.get().loop
        for a in args: await unwrap(loop, a)
        return ()
    return Process(discard_fn, any_ty(len(box.dom)), any_ty(0))

class UniversalObMap:
    def __getitem__(self, _): return object
    def get(self, key, default=None): return object

def _exec_functor_impl(diag: closed.Diagram) -> Process:
    from discopy.closed import Functor
    f = Functor(ob=UniversalObMap(), ar=exec_dispatch, cod=python.Category())
    return f(diag)

from .yaml import Composable
exec_functor = Composable(_exec_functor_impl)

async def execute(diag: closed.Diagram, hooks: dict, executable: str, loop: Any, stdin: Any = None):
    parent = _EXEC_CTX.get(None)
    ctx = ExecContext(hooks, executable, loop)
    if parent:
        ctx.anchors.update(parent.anchors)
    token = _EXEC_CTX.set(ctx)
    try:
        proc = exec_functor(diag)
        arg = (stdin,) if proc.dom else ()
        res = await unwrap(loop, proc(*arg))
        return res
    finally:
        _EXEC_CTX.reset(token)

@contextmanager
def titi_runner(hooks: Dict[str, Callable], executable: str = "python3", loop: Any = None):
    if loop is None:
        import asyncio
        loop = asyncio.get_running_loop()
    ctx = ExecContext(hooks, executable, loop)
    def runner(diag: closed.Diagram, stdin: Any = None):
        return execute(diag, hooks, executable, loop, stdin)
    yield runner, loop

compile_exec = exec_functor
__all__ = ['execute', 'ExecContext', 'exec_dispatch', 'Process', 'titi_runner', 'compile_exec']
