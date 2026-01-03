from __future__ import annotations
from typing import Any, Callable, Awaitable, Dict, Iterator, TypeVar
from functools import partial

from discopy import closed, python, utils, monoidal, symmetric

from .computer import Language
from .asyncio import unwrap, Thunk, run_command, loop_scope, AbstractEventLoop, loop_var, pipe_async, tensor_async
from . import widish

T = TypeVar("T")

class Process(python.Function):
    """Wraps an async function with loop context awareness."""
    def __init__(self, inside: Callable[..., Awaitable[Any] | Any], 
                 dom: closed.Ty, cod: closed.Ty, 
                 loop: AbstractEventLoop | None = None):
        super().__init__(inside, dom, cod)
        self.loop = loop

    def then(self, other: Process) -> Process:
        loop = self.loop or getattr(other, 'loop', None) or loop_var.get()
        return Process(lambda *args: pipe_async(self.inside, other.inside, loop, *args), 
                      self.dom, other.cod, loop=loop)

    def tensor(self, other: Process) -> Process:
        loop = self.loop or getattr(other, 'loop', None) or loop_var.get()
        return Process(lambda *args: tensor_async(self.inside, self.dom, other.inside, loop, *args), 
                      self.dom + other.dom, self.cod + other.cod, loop=loop)

    @classmethod
    def id(cls, dom: closed.Ty) -> Process:
        return cls(lambda *args: args, dom, dom, loop=loop_var.get())

    @classmethod
    def get_category(cls) -> closed.Category:
        return closed.Category(closed.Ty, cls)

    @classmethod
    def from_callable(cls, diagram: closed.Diagram) -> Callable[[Callable], Process]:
        """Annotation-style entry point for compiling a diagram into a Process."""
        def decorator(ar: Callable[[closed.Box | closed.Diagram], Process]) -> Process:
             return closed.Functor(ob=lambda x: x, ar=ar, cod=cls.get_category())(diagram)
        return decorator

async def widip_runner(hooks: Dict[str, Callable], executable: str | None = None, loop: AbstractEventLoop | None = None):
    """Runner setup: creates a compiler function and handles context."""
    exec_path = executable or hooks['get_executable']()
    with loop_scope(hooks, loop) as loop:
        def runner(diag: closed.Diagram) -> Process:
             return compile_exec(diag, hooks, exec_path, loop)
        yield runner, loop

def compile_exec(diag: closed.Diagram, hooks: Dict[str, Callable], executable: str, loop: AbstractEventLoop) -> Process:
    """Compiles a diagram into a runnable Process using a local arrow mapping."""
    import widip.computer as comp
    import widip.yaml as yaml

    @Process.from_callable(diag)
    def ar(box: closed.Box | closed.Diagram) -> Process:
        # Match data boxes
        if isinstance(box, comp.Data):
            return Process(lambda *_: box.value, box.dom, box.cod, loop=loop)
        
        # Match program boxes
        if isinstance(box, comp.Program):
            return Process(lambda *args: run_command(lambda d: compile_exec(d, hooks, executable, loop), loop, box.name, args, None, hooks), 
                         box.dom, box.cod, loop=loop)
        
        # Match structural YAML boxes
        if isinstance(box, yaml.Scalar):
            return Process(lambda *_: box.value, box.dom, box.cod, loop=loop)
        
        # Match generic execution boxes
        if box.name == "exec":
            return Process(lambda name, *args: run_command(lambda d: compile_exec(d, hooks, executable, loop), loop, name, args, None, hooks), 
                         box.dom, box.cod, loop=loop)
        
        # Match containers and recursion
        if isinstance(box, (yaml.Sequence, yaml.Mapping)):
            inside = getattr(box, 'inside', None) or (box.arg if hasattr(box, 'arg') else None)
            if inside is not None and isinstance(inside, (closed.Diagram, monoidal.Diagram, symmetric.Diagram)):
                 return compile_exec(inside, hooks, executable, loop)
            return Process.id(box.dom)
            
        if isinstance(box, yaml.Anchor):
            return compile_exec(box.inside, hooks, executable, loop)

        # Default: treat box as a shell command
        return Process(lambda name, *args: run_command(lambda d: compile_exec(d, hooks, executable, loop), loop, name, args, None, hooks), 
                     box.dom, box.cod, loop=loop)

    return ar

