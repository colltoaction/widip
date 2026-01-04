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
        
        # Intercept Special Commands
        if box.name == "anchor":
            name, inside = args_data
            ctx.anchors[name] = inside
            # Execute the inner diagram
            return await execute(inside, ctx.hooks, ctx.executable, ctx.loop, stdin_val)
            
        if box.name == "alias":
            name = args_data[0]
            if name not in ctx.anchors:
                raise ValueError(f"Unknown anchor: {name}")
            # Recurse
            return await execute(ctx.anchors[name], ctx.hooks, ctx.executable, ctx.loop, stdin_val)

        return await run_command(lambda x: x, ctx.loop, box.name, args_data, stdin_val, ctx.hooks)
    return Process(prog_fn, dom, cod)

def any_ty(n: int):
    """Returns a tensor of n object types."""
    return python.Ty(n * [object])

def exec_swap(box: symmetric.Swap) -> Process:
    return Process(lambda a, b: (b, a), any_ty(2), any_ty(2))

# --- Dispatcher ---

def exec_dispatch(box: Any) -> Process:
    if isinstance(box, (closed.Box, symmetric.Box)):
        if isinstance(box, symmetric.Swap): return exec_swap(box)
        if hasattr(box, 'name') and box.name == "Δ": return exec_copy(box)
        return exec_box(box)
    return Process.id(any_ty(getattr(box, 'dom', closed.Ty())))

# --- Copy Execution ---

def exec_copy(box: closed.Box) -> Process:
    """Handles async copy by returning multiple awaitables."""
    import asyncio
    
    async def _resolve_and_copy(shared_task, index):
        res = await shared_task
        # Logic matches _copy service: value or stream tee
        if hasattr(res, 'read'):
            # TODO: robust caching/teeing for streams. 
            # For now assume memory IO or lightweight streams that support seek/copy?
            # Or use native _copy logic which reads fully.
            # We can reuse _copy logic but we need to run it once.
            pass
        return res # Placeholder, correct logic below

    def copy_fn(x):
        # x is the input awaitable/value
        # Create a shared task to resolve x ONCE
        loop = _EXEC_CTX.get().loop
        
        async def loader():
             # We rely on the native _copy anchor logic to do the heavy lifting (reading/teeing)!
             # But _copy expects input. 
             # We unwrap x using standard unwrap.
             # Then call _copy logic.
             from .asyncio import unwrap
             val = await unwrap(loop, x)
             
             # Reuse native _copy implementation from anchors?
             # But anchors are async def.
             # Let's verify if we can just return copies of x if x is awaitable?
             # No, x is single input.
             # We must resolve x.
             
             if hasattr(val, 'read'):
                  content = await val.read()
                  import io
                  return (io.BytesIO(content), io.BytesIO(content))
             return (val, val)

        # Shared task
        task = loop.create_task(loader())
        
        # Return N awaitables that wait for task and pick their component
        async def getter(i):
             res_tuple = await task
             return res_tuple[i]
             
        return (getter(0), getter(1))

    return Process(copy_fn, any_ty(1), any_ty(2))

def exec_functor(diag: closed.Diagram) -> Process:
    """Manual functor implementation to avoid DisCoPy version issues."""
    from discopy.closed import Functor
    # Map Language to Any in the python category
    f = Functor(ob={closed.Ty("P")[0]: object, discopy.cat.Ob("object"): object}, 
                ar=exec_dispatch, cod=python.Category())
    return f(diag)

async def execute(diag: closed.Diagram, hooks: dict, executable: str, loop: Any, stdin: Any = None):
    parent = _EXEC_CTX.get(None)
    ctx = ExecContext(hooks, executable, loop)
    if parent:
        ctx.anchors.update(parent.anchors)

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
def titi_runner(hooks: Dict[str, Callable], executable: str = "python3", loop: Any = None):
    """Context manager for the execution environment."""
    if loop is None:
        import asyncio
        loop = asyncio.get_running_loop()
    ctx = ExecContext(hooks, executable, loop)
    def runner(diag: closed.Diagram, stdin: Any = None):
        return execute(diag, hooks, executable, loop, stdin)
    yield runner, loop

# Legacy alias for tests
compile_exec = exec_functor

__all__ = ['execute', 'ExecContext', 'exec_dispatch', 'Process', 'titi_runner', 'compile_exec']
