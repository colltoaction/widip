from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from functools import singledispatch
from contextvars import ContextVar
from discopy import closed, python, utils
import widip.computer as comp
from .asyncio import unwrap, run_command, loop_scope, AbstractEventLoop, loop_var

T = TypeVar("T")

# --- Process Definition ---

class Process(python.Function):
    """
    A process is a function from inputs to outputs (as tuples),
    wrapped in a DisCoPy box for composition.
    """
    def __init__(self, inside: Callable[..., Any], dom: closed.Ty, cod: closed.Ty):
        self.inside = inside
        self.dom, self.cod = dom, cod

    def __call__(self, *args):
        return self.inside(*args)

    @classmethod
    def from_callable(cls, diagram: closed.Diagram):
        """Decorator to create an execution functor from a diagram's structure."""
        def decorator(func):
            F = closed.Functor(
                ob=lambda x: x,
                ar=func,
                cod=python.Category(closed.Ty, Process)
            )
            return F(diagram)
        return decorator
    
    def then(self, other):
        async def composed(*args):
            mid = await unwrap(loop_var.get(), self(*args))
            if mid is None: return None
            return await other(*utils.tuplify(mid))
        return Process(composed, self.dom, other.cod)

    def tensor(self, other):
        async def composed(*args):
            n = len(self.dom)
            args1, args2 = args[:n], args[n:]
            res1 = await unwrap(loop_var.get(), self(*args1))
            res2 = await unwrap(loop_var.get(), other(*args2))
            return utils.tuplify(res1) + utils.tuplify(res2)
        return Process(composed, self.dom @ other.dom, self.cod @ other.cod)


# --- Execution Context ---

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: AbstractEventLoop):
        self.hooks = hooks
        self.executable = executable
        self.loop = loop

_EXEC_CTX: ContextVar[ExecContext] = ContextVar("exec_ctx")


# --- Execution Dispatcher (Top Level) ---

@singledispatch
def exec_dispatch(box: Any) -> Process:
    """Default dispatcher acting as identity/fallback."""
    async def id_fn(*args): return args
    return Process(id_fn, box.dom, box.cod)

@exec_dispatch.register(comp.Data)
def _(box) -> Process:
    async def data_fn(*args): return box.value
    return Process(data_fn, box.dom, box.cod)

@exec_dispatch.register(comp.Program)
def _(box) -> Process:
    # Use context bound at runtime
    ctx = _EXEC_CTX.get()
    async def prog_fn(*args):
        cmd_args = box.args if hasattr(box, "args") else ()
        stdin_val = args[0] if args else None
        if len(args) > 1: stdin_val = args
        return await run_command(lambda x: x, ctx.loop, box.name, cmd_args, stdin_val, ctx.hooks)
    return Process(prog_fn, box.dom, box.cod)

@exec_dispatch.register(comp.Discard)
def _(box) -> Process:
    async def discard_fn(*args): return ()
    return Process(discard_fn, box.dom, box.cod)

@exec_dispatch.register(closed.Swap)
def _(box) -> Process:
    async def swap_fn(a, b): return (b, a)
    return Process(swap_fn, box.dom, box.cod)

@exec_dispatch.register(closed.Diagram)
def _(box) -> Process:
    # Recursion: Apply the functor logic to the nested diagram
    # The context is preserved via the ContextVar as we are in the same async trace
    return Process.from_callable(box)(exec_dispatch)


def compile_exec(diag: closed.Diagram, hooks: Dict[str, Callable], executable: str, loop: AbstractEventLoop) -> Process:
    """Compiles a diagram into a runnable Process using shared context."""
    token = _EXEC_CTX.set(ExecContext(hooks, executable, loop))
    try:
        return Process.from_callable(diag)(exec_dispatch)
    finally:
        _EXEC_CTX.reset(token)

@closed.Diagram.from_callable(comp.Language(), comp.Language())
def SHELL_COMPILER(diagram_source: Any) -> closed.Diagram:
    """Entry point for compiling YAML into computer diagrams."""
    # This was previously in computer/__init__.py but moved here or duplicated?
    # SHELL_COMPILER was moved to exec.py earlier.
    # We maintain it here as a top-level from_callable as requested.
    import widip.yaml as yaml
    res = yaml.load(diagram_source)
    if isinstance(res, (closed.Box, comp.Program, comp.Data)):
         return closed.Id(res.dom) >> res
    return res

def widip_runner(hooks: Dict, executable: str):
    """Context manager for running widip processes."""
    return loop_scope(hooks)
