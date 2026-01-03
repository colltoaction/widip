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
        from functools import partial
        return Process(partial(pipe_async, self, other, None), self.dom, other.cod)

    def tensor(self, other):
        from functools import partial
        return Process(partial(tensor_async, self, self.dom, other, None), self.dom @ other.dom, self.cod @ other.cod)


# --- Execution Context ---

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: AbstractEventLoop):
        self.hooks = hooks
        self.executable = executable
        self.loop = loop

_EXEC_CTX: ContextVar[ExecContext] = ContextVar("exec_ctx")


# --- Execution Dispatcher (Top Level) ---

# --- Execution Dispatcher (Top Level) ---

@singledispatch
def exec_dispatch(box: Any) -> Process:
    """Default dispatcher acting as identity/fallback."""
    # Identity process
    async def id_fn(*args): return args
    return Process(id_fn, box.dom, box.cod)

def exec_data(box: comp.Data) -> Process:
    async def data_fn(*args): return box.value
    return Process(data_fn, box.dom, box.cod)

exec_dispatch.register(comp.Data, exec_data)

def exec_program(box: comp.Program) -> Process:
    # Use context bound at runtime
    ctx = _EXEC_CTX.get()
    async def prog_fn(*args):
        cmd_args = box.args if hasattr(box, "args") else ()
        stdin_val = args[0] if args else None
        if len(args) > 1: stdin_val = args
        return await run_command(lambda x: x, ctx.loop, box.name, cmd_args, stdin_val, ctx.hooks)
    return Process(prog_fn, box.dom, box.cod)

exec_dispatch.register(comp.Program, exec_program)

def exec_discard(box: comp.Discard) -> Process:
    async def discard_fn(*args): return ()
    return Process(discard_fn, box.dom, box.cod)

exec_dispatch.register(comp.Discard, exec_discard)

def exec_swap(box: closed.Swap) -> Process:
    async def swap_fn(a, b): return (b, a)
    return Process(swap_fn, box.dom, box.cod)

exec_dispatch.register(closed.Swap, exec_swap)

def exec_diagram(box: closed.Diagram) -> Process:
    # Recursion: Apply the functor logic to the nested diagram
    return Process.from_callable(box)(exec_dispatch)

exec_dispatch.register(closed.Diagram, exec_diagram)


def execute(diag: closed.Diagram, hooks: Dict[str, Callable], executable: str, loop: AbstractEventLoop) -> Process:
    """Execute a diagram by compiling it to a Process with context."""
    token = _EXEC_CTX.set(ExecContext(hooks, executable, loop))
    try:
        # We call exec_dispatch on the diagram, which recurses via exec_diagram
        return exec_dispatch(diag)
    finally:
        _EXEC_CTX.reset(token)



