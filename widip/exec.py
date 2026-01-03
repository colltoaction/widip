from __future__ import annotations
import asyncio
import sys
import contextlib
from typing import Any, Sequence, TypeVar, Union
from functools import partial

from discopy import closed, python, utils

from .computer import *
from .io import run_command, Process, loop_scope
from .thunk import unwrap, Thunk
from . import widish

T = TypeVar("T")

@contextlib.contextmanager
def widip_runner(executable: str = sys.executable, loop: asyncio.AbstractEventLoop | None = None):
    """Runner setup: creates ExecFunctor and handles KeyboardInterrupt."""
    runner = ExecFunctor(executable=executable, loop=loop)
    try:
        yield runner
    except KeyboardInterrupt:
        pass

class Exec(closed.Box):
    def __init__(self, dom: closed.Ty, cod: closed.Ty):
        super().__init__("exec", dom, cod)

async def exec_generic(runner: 'ExecFunctor', loop: asyncio.AbstractEventLoop, ar: object, *args: Any) -> tuple[Any, list[Any], Any]:
    resolved = [await unwrap(loop, arg) for arg in args]
    
    if isinstance(ar, Program):
        name, raw_args, stdin_val = ar.name, ar.args, resolved
    elif isinstance(ar, (Exec, Eval)) and resolved:
        name, raw_args, stdin_val = resolved[0], resolved[1:-1], resolved[-1:]
    else:
        name, raw_args, stdin_val = ar, [], resolved

    cmd_args = []
    for arg in raw_args:
        if isinstance(arg, closed.Diagram):
            cmd_args.append(await unwrap(loop, runner(arg)(*utils.tuplify(stdin_val))))
        else:
            cmd_args.append(arg)

    if isinstance(stdin_val, (list, tuple)) and len(stdin_val) == 1:
        return name, cmd_args, stdin_val[0]
    return name, cmd_args, stdin_val

async def _exec_wrapper(runner: ExecFunctor, loop: asyncio.AbstractEventLoop, ar: Any, *args: Any) -> Any:
    # Top-level execution wrapper - Lisp-like eval
    mapping = {
        Data: widish.run_constant, 
        Swap: widish.run_swap, 
        Copy: widish.run_copy,
        Merge: widish.run_merge, 
        Discard: widish.run_discard
    }
    
    # Handle Gamma constant specially if requested via a check
    # Refactoring suggestion was to make this contain "typical lisp eval code"
    # This implies evaluating the operator first if it's not a primitive.
    
    # 1. Primitive forms (Data, Swap, Copy, Merge, Discard)
    func = mapping.get(type(ar))
    if func:
        if func in (widish.run_map, widish.run_seq):
             return await func(runner, ar, *args)
        return await func(ar, *args)
    
    # 3. Application / Function Call
    # evaluate operator (name) and arguments
    name, cmd_args, stdin = await exec_generic(runner, loop, ar, *args)
    
    # 4. Apply
    return await run_command(runner, loop, name, cmd_args, stdin)


class ExecFunctor(closed.Functor):
    def __init__(self, executable: Any = None, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__(self.ob_map, self.ar_map, dom=Computation, cod=ExecCategory)
        self._executable, self._loop = executable, loop

    def ob_map(self, ob: closed.Ty) -> type:
        from typing import IO
        return object if ob == Language else Thunk

    def ar_map(self, ar: object) -> Process:
        async def traced_t(*args: Any) -> Any:
            with loop_scope(self._loop):
                return await unwrap(self._loop, _exec_wrapper(self, self._loop, ar, *args))

        res = Process(traced_t, self(ar.dom), self(ar.cod), loop=self._loop)
        res.ar = ar
        return res

    def __call__(self, ar_or_ob):
        with loop_scope(self._loop):
            res = super().__call__(ar_or_ob)
            if isinstance(res, Process) and res.loop is None:
                 res.loop = self._loop
            return res

ExecCategory = closed.Category(python.Ty, Process)
