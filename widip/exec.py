import asyncio
import sys
from typing import IO, Callable, Awaitable, TypeVar, Any, Sequence
from io import StringIO
from functools import partial

from discopy import closed, python, utils

from .computer import *
from .widish import Process
from .thunk import unwrap, Thunk

T = TypeVar("T")
U = TypeVar("U")

class Exec(closed.Box):
    def __init__(self, dom: closed.Ty, cod: closed.Ty):
        super().__init__("exec", dom, cod)

def _read_content(item: Any) -> str:
    if hasattr(item, 'read'):
        if hasattr(item, 'seek'): item.seek(0)
        return item.read()
    return str(item)

async def _unwrap_content(loop, item: Any) -> str:
     if isinstance(item, (list, tuple)):
         res = []
         for i in item:
             res.append(_read_content(i))
         return "".join(res)
     return _read_content(item)


async def run_command(runner: 'ExecFunctor', loop: asyncio.AbstractEventLoop, name: str, args: Sequence[str], stdin: IO[str]) -> StringIO:
    # Explicit loop parameter threading
    if name in (registry := RECURSION_REGISTRY.get()):
         item = registry[name]
         if not callable(item):
              item = runner(item)
              # Copy on write
              new_registry = registry.copy()
              new_registry[name] = item
              RECURSION_REGISTRY.set(new_registry)
         # Unwrap result with explicitly passed loop
         return await unwrap(loop, item(stdin))

    import subprocess
    cmd = [name] + list(args)
    
    # Read stdin content manually
    stdin_content = _read_content(stdin)
    
    # Use native asyncio subprocess
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout_data, stderr_data = await process.communicate(input=stdin_content.encode())
    
    return StringIO(stdout_data.decode())


async def exec_generic(runner: 'ExecFunctor', loop: asyncio.AbstractEventLoop, ar: object, *args: Any) -> tuple[str, list[str], StringIO]:
    # Pass loop to unwrap
    resolved = [await unwrap(loop, arg) for arg in args]
    
    if isinstance(ar, Program):
        name, raw_args, stdin_val = ar.name, ar.args, resolved
    elif isinstance(ar, (Exec, Eval)) and resolved:
        name, raw_args, stdin_val = _read_content(resolved[0]), resolved[1:-1], resolved[-1:]
    else:
        name, raw_args, stdin_val = str(getattr(ar, 'name', ar)), [], resolved

    cmd_args = []
    for arg in raw_args:
        if isinstance(arg, closed.Diagram):
            # Pass loop
            arg_res = await unwrap(loop, runner(arg)(*utils.tuplify(stdin_val)))
            cmd_args.append(await _unwrap_content(loop, arg_res))
        else:
            cmd_args.append(await _unwrap_content(loop, arg))

    # Return components
    return name, cmd_args, StringIO(await _unwrap_content(loop, stdin_val))


class ExecFunctor(closed.Functor):
    def __init__(self, executable: Any = None, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__(self.ob_map, self.ar_map, dom=Computation, cod=ExecCategory)
        self._executable, self._loop = executable, loop

    def ob_map(self, ob: closed.Ty) -> type:
        return IO if ob == Language else Thunk

    def ar_map(self, ar: object) -> Process:
        mapping = {Data: Process.run_constant, Swap: Process.run_swap, Copy: Process.run_copy,
                   Merge: Process.run_merge, Discard: Process.run_discard}
        
        func = mapping.get(type(ar))
        
        async def generic_wrapper(*args):
            if func:
                return await func(ar, *args)
            
            # Explicitly thread self._loop to generic handlers
            name, cmd_args, stdin = await exec_generic(self, self._loop, ar, *args)
            return await run_command(self, self._loop, name, cmd_args, stdin)

        async def traced_t(*args: Any) -> Any:
            # Pass self._loop
            res = await unwrap(self._loop, generic_wrapper(*args))
            if isinstance(ar, (Data, Eval, Program)):
                # Manual unwrap using local helper
                unwrapped_items = [
                    StringIO(_read_content(i)) if hasattr(i, 'read') else i 
                    for i in utils.tuplify(res)
                ]
                res = utils.untuplify(tuple(unwrapped_items))
            return res

        res = Process(traced_t, self(ar.dom), self(ar.cod))
        res.ar = ar
        return res


ExecCategory = closed.Category(python.Ty, Process)
