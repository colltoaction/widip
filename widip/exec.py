import asyncio
import sys
import os
import contextlib
from typing import Any, Sequence, TypeVar, Union
from functools import partial

from discopy import closed, python, utils

from .computer import *
from .widish import Process, LOOP_VAR, loop_scope
from .thunk import unwrap, Thunk
from .io import run_command

T = TypeVar("T")

@contextlib.contextmanager
def setup_loop():
    """Environment setup: recursion limit and asyncio event loop."""
    sys.setrecursionlimit(10000)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if __debug__:
            import matplotlib
            matplotlib.use('agg')
        yield loop
    finally:
        loop.close()

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


class ExecFunctor(closed.Functor):
    def __init__(self, executable: Any = None, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__(self.ob_map, self.ar_map, dom=Computation, cod=ExecCategory)
        self._executable, self._loop = executable, loop

    def ob_map(self, ob: closed.Ty) -> type:
        from typing import IO
        return IO if ob == Language else Thunk

    def ar_map(self, ar: object) -> Process:
        mapping = {Data: Process.run_constant, Swap: Process.run_swap, Copy: Process.run_copy,
                   Merge: Process.run_merge, Discard: Process.run_discard}
        
        func = mapping.get(type(ar))
        
        async def generic_wrapper(*args):
            if func:
                return await func(ar, *args)
            name, cmd_args, stdin = await exec_generic(self, self._loop, ar, *args)
            return await run_command(self, self._loop, name, cmd_args, stdin)

        async def traced_t(*args: Any) -> Any:
            with loop_scope(self._loop):
                return await unwrap(self._loop, generic_wrapper(*args))

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
