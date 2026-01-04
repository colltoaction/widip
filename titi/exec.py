from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from discopy import closed, symmetric, frobenius
from .asyncio import run_command, unwrap
import discopy
from computer import python

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
    
    # The generic data/program box logic handles both tagged/untagged boxes.
    # We only need one async function prog_fn that dispatches correctly.
    
    # Program box logic
    async def prog_fn(*args):
        ctx = _EXEC_CTX.get()
        memo = {}
        unwrapped_args = []
        for stage in args:
            unwrapped_args.append(await unwrap(stage, ctx.loop, memo))
        
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
            res = await execute(inside, ctx.hooks, ctx.executable, ctx.loop, stdin_val)
            from .asyncio import printer
            await printer(None, res, ctx.hooks)
            result = res
        elif box.name == "alias":
            name = args_data[0]
            if name not in ctx.anchors:
                raise ValueError(f"Unknown anchor: {name}")
            res = await execute(ctx.anchors[name], ctx.hooks, ctx.executable, ctx.loop, stdin_val)
            from .asyncio import printer
            await printer(None, res, ctx.hooks)
            result = res
        elif box.name == "print":
             from .asyncio import printer
             await printer(None, stdin_val, ctx.hooks)
             result = () if not cod else stdin_val
        elif box.name == "read_stdin":
             result = ctx.hooks['stdin_read']()
        if type(box).__name__ == "Data":
             result = box.name
        elif type(box).__name__ == "Partial":
             from computer import Partial
             # Returning the box itself as a 'partial' application (callable/process)
             result = box 
        else:
             result = await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
        
        # Enforce DisCoPy Process return conventions
        n_out = len(cod)
        if n_out == 0: return ()
        if n_out == 1:
             if isinstance(result, tuple):
                  return result[0] if len(result) > 0 else None
             return result
        return discopy.utils.tuplify(result)
    return Process(prog_fn, dom, cod)

def any_ty(n: int):
    return python.Ty(*[object] * n)

def exec_swap(box: symmetric.Swap) -> Process:
    async def swap_fn(a, b):
        ctx = _EXEC_CTX.get()
        return (await unwrap(b, ctx.loop), await unwrap(a, ctx.loop))
    return Process(swap_fn, any_ty(len(box.dom)), any_ty(len(box.cod)))

# --- Dispatcher ---

def exec_dispatch(box: Any) -> Process:
    # 1. Handle algebraic operations regardless of exact class
    name = getattr(box, 'name', None)
    if name == "Δ": return exec_copy(box)
    if name == "μ": return exec_merge(box)
    if name == "ε": return exec_discard(box)
    if hasattr(box, 'is_swap') and box.is_swap: return exec_swap(box)

    # 2. Handle known box categories
    if isinstance(box, (closed.Box, symmetric.Box, frobenius.Box)):
        if isinstance(box, symmetric.Swap): return exec_swap(box)
        return exec_box(box)
    
    # 3. Default to identity
    return Process.id(any_ty(len(getattr(box, 'dom', closed.Ty()))))

# --- Core Combinators Execution ---

def exec_copy(box: closed.Box) -> Process:
    n = getattr(box, 'n', 2)
    if n == 0:
        return exec_discard(box)

    def copy_fn(x):
        loop = _EXEC_CTX.get().loop
        from .asyncio import unwrap
        import io

        async def loader():
             val = await unwrap(x, loop)
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
        # Await all inputs
        results = [await unwrap(a, loop) for a in args]
        # Return the last non-None result (shadowing/overwrite behavior)
        for r in reversed(results):
            if r is not None: return r
        return None
    return Process(merge_fn, any_ty(n), any_ty(1))

def exec_discard(box: closed.Box) -> Process:
    async def discard_fn(*args):
        from .asyncio import unwrap
        loop = _EXEC_CTX.get().loop
        import asyncio
        for a in args: 
             val = await unwrap(a, loop)
             if val is not None and hasattr(val, 'read'):
                 if asyncio.iscoroutinefunction(val.read): await val.read()
                 else:
                      res = val.read()
                      if asyncio.iscoroutine(res): await res
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

async def execute(diag: closed.Diagram, hooks: Dict[str, Callable],
                  executable: str = "python3", loop: Any = None, stdin: Any = None,
                  memo: dict | None = None) -> Any:
    """Execute a diagram using the async evaluation loop."""
    if loop is None:
        import asyncio
        loop = asyncio.get_event_loop()
    if memo is None: memo = {}
    
    ctx = ExecContext(hooks, executable, loop)
    token = _EXEC_CTX.set(ctx)
    try:
        proc = exec_functor(diag)
        # Default to empty bytes if no stdin provided but domain is non-empty
        active_stdin = stdin
        if active_stdin is None and len(proc.dom) > 0:
            active_stdin = b""
        arg = (active_stdin,) if proc.dom else ()
        res = await unwrap(proc(*arg), loop, memo)
        return res
    finally:
        try:
            _EXEC_CTX.reset(token)
        except ValueError: pass

class titi_runner:
    """Class-based context manager for running titi diagrams."""
    def __init__(self, hooks: Dict[str, Callable], executable: str = "python3", loop: Any = None):
        if loop is None:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None # Will be handled in __enter__ if needed

        self.hooks, self.executable, self.loop = hooks, executable, loop

    def __enter__(self):
        if self.loop is None:
            import asyncio
            self.loop = asyncio.get_event_loop()
            
        def runner(diag: closed.Diagram, stdin: Any = None):
            return execute(diag, self.hooks, self.executable, self.loop, stdin)
        return runner, self.loop

    def __exit__(self, *args):
        pass

compile_exec = exec_functor
__all__ = ['execute', 'ExecContext', 'exec_dispatch', 'Process', 'titi_runner', 'compile_exec']
