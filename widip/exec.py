from __future__ import annotations
import sys
import contextlib
from typing import Any, Sequence, TypeVar, Union, Iterator, Callable
from functools import partial

from discopy import closed, python, utils, monoidal, symmetric

from .computer import *
from .asyncio import unwrap, Thunk, run_command, loop_scope, AbstractEventLoop, loop_var, pipe_async, tensor_async
from . import widish

T = TypeVar("T")

class Process(python.Function):
    """Wraps an async function with loop context awareness."""
    def __init__(self, inside: Callable, dom: closed.Ty, cod: closed.Ty, loop: AbstractEventLoop | None = None):
        super().__init__(inside, dom, cod)
        self.loop = loop

    def then(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or loop_var.get()
        return Process(lambda *args: pipe_async(self.inside, other.inside, loop, *args), 
                      self.dom, other.cod, loop=loop)

    def tensor(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or loop_var.get()
        return Process(lambda *args: tensor_async(self.inside, self.dom, other.inside, loop, *args), 
                      self.dom + other.dom, self.cod + other.cod, loop=loop)

    @classmethod
    def id(cls, dom: closed.Ty) -> 'Process':
        return cls(lambda *args: args, dom, dom, loop=loop_var.get())

    @classmethod
    def get_category(cls) -> closed.Category:
        return closed.Category(closed.Ty, cls)

    @classmethod
    def from_callable(cls, diagram: closed.Diagram, ar: Callable[[closed.Box|closed.Diagram], 'Process']) -> 'Process':
        return closed.Functor(ob=lambda x: x, ar=ar, cod=cls.get_category())(diagram)

@contextlib.contextmanager
def widip_runner(hooks: dict, executable: str | None = None, loop: AbstractEventLoop | None = None):
    """Runner setup: creates ExecFunctor and handles KeyboardInterrupt."""
    exec_path = executable or hooks['get_executable']()
    with loop_scope(hooks, loop) as loop:
        runner = ExecFunctor(hooks=hooks, executable=exec_path, loop=loop)
        yield runner, loop

class ExecFunctor(closed.Functor):
    """Compiles a diagram into a runnable Process."""
    def __init__(self, hooks: dict, executable: str, loop: AbstractEventLoop):
        super().__init__(ob=lambda x: x, ar=lambda f: f, cod=Process.get_category())
        self.hooks = hooks
        self.executable = executable
        self.loop = loop

    def __call__(self, diag: closed.Diagram) -> Process:
        # Resolve classes from computer and yaml modules for case matching
        import widip.computer as comp
        import widip.yaml as yaml

        def ar(box):
            if isinstance(box, comp.Data):
                return Process(lambda *_: box.value, box.dom, box.cod, loop=self.loop)
            if isinstance(box, comp.Program):
                return Process(lambda *args: run_command(self, self.loop, box.name, args, None, self.hooks), 
                             box.dom, box.cod, loop=self.loop)
            if isinstance(box, yaml.Scalar):
                return Process(lambda *_: box.value, box.dom, box.cod, loop=self.loop)
            if box.name == "exec":
                return Process(lambda name, *args: run_command(self, self.loop, name, args, None, self.hooks), 
                             box.dom, box.cod, loop=self.loop)
            if isinstance(box, (yaml.Sequence, yaml.Mapping)):
                inside = getattr(box, 'diagram', None) or getattr(box, 'inside', None)
                if inside is not None: return self(inside)
                return Process(lambda *args: args, box.dom, box.cod, loop=self.loop)
            if isinstance(box, yaml.Anchor):
                return self(box.inside)

            # Default: treat box as command
            return Process(lambda name, *args: run_command(self, self.loop, name, args, None, self.hooks), 
                         box.dom, box.cod, loop=self.loop)

        return Process.from_callable(diag, ar)

def flatten(val: Any) -> Iterator[Any]:
    """Recursively flatten tuples and lists."""
    if isinstance(val, (tuple, list)):
        for i in val:
            yield from flatten(i)
    else:
        yield val
