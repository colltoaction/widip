import asyncio
import sys
from typing import IO, Callable, Awaitable, TypeVar
from io import StringIO
from functools import partial

from discopy import closed, python

from .computer import *
# Process is needed for class definition
from .widish import Process

T = TypeVar("T")

U = TypeVar("U")


async def to_stream(item: T | U) -> StringIO:
    """Convert any item to a StringIO stream."""
    if isinstance(item, StringIO):
        # Create a copy to avoid consuming the original
        return StringIO(item.getvalue())
    if isinstance(item, (tuple, list)):
        # Flatten tuple/list by recursively converting elements
        parts = []
        for sub_item in item:
            if isinstance(sub_item, StringIO):
                parts.append(sub_item.getvalue())
            elif isinstance(sub_item, (tuple, list)):
                parts.append((await to_stream(sub_item)).getvalue())
            else:
                parts.append(str(sub_item) if sub_item is not None else "")
        return StringIO("".join(parts))
    # Convert to string and wrap in StringIO
    return StringIO(str(item) if item is not None else "")



def _lazy(func: Callable[..., Awaitable[T]], ar: object) -> Callable[..., Awaitable[T]]:
    """Returns a function that returns a partial application of func."""
    async def wrapper(*args: object) -> T:
        return partial(func, ar, *args) # type: ignore
    return wrapper

async def run_command(
    runner: closed.Functor,
    name: str | object,
    args: tuple[str, ...],
    stdin: StringIO
) -> StringIO:

    # Logic merged from widish.py
    
    # 1. Check for Recursion / Registry
    if isinstance(name, str):
        if name in (registry := RECURSION_REGISTRY.get()):
             item = registry[name]
             if not callable(item):
                  from .compiler import SHELL_COMPILER
                  compiled = SHELL_COMPILER(item)
                  compiled_runner = runner(compiled)
                  registry[name] = compiled_runner
                  RECURSION_REGISTRY.set(dict(registry))
             else:
                  compiled_runner = item
             return await compiled_runner(stdin)


    if not isinstance(name, str):
        return StringIO("")

    args = tuple(map(str, args))

    # Subprocess Execution in text mode
    process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
        name, *args,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        stderr=None,
        text=True
    )

    # Use communicate to handle stdin/stdout
    stdout, _ = await process.communicate(stdin.getvalue())
    return StringIO(stdout)


ExecCategory = closed.Category(python.Ty, Process)

def exec_ob(ob: closed.Ty) -> type:
    if ob == Language:
        return IO
    return object


# exec_ar removed

from .thunk import unwrap

async def exec_deferred(runner: T, ar: object, *args: U) -> U:
    # ... resolution logic ...
    async def resolve(x: T | U) -> T | U:
        if callable(x):
            return await unwrap(x())
        return x

    resolved = []
    for x in args:
        res = await resolve(x)
        resolved.append(res)
    
    if ar.name:
            name = ar.name
            cmd_args = resolved
            stdin_wires = []
    else:
            if not resolved: return StringIO("")
            name = resolved[0]
            if isinstance(name, StringIO):
                name = name.getvalue().strip()
            
            stdin_wires = resolved[-1]
            if not isinstance(stdin_wires, (tuple, list)):
                stdin_wires = [stdin_wires]
                
            cmd_args = resolved[1:-1]

    # Unwrap arguments
    final_args = []
    for arg in cmd_args:
            if isinstance(arg, (tuple, list)):
                arg = arg[0] if arg else ""
            if isinstance(arg, StringIO):
                final_args.append(arg.getvalue().strip())
            else:
                final_args.append(str(arg))
            
    # Prepare Stdin Stream - normalize to single stream
    if len(stdin_wires) == 1:
         stdin_stream = await to_stream(stdin_wires[0])
    else:
         stdin_stream = await to_stream(stdin_wires)

    return await run_command(runner, name, final_args, stdin_stream)


async def exec_program(runner: T, ar: object, *args: U) -> U:
    # Normalize args to single stream
    if len(args) == 1:
         stdin_stream = await to_stream(args[0])
    else:
        stdin_stream = await to_stream(args)
    
    return await run_command(runner, ar.name, ar.args, stdin_stream)



class ExecFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            exec_ob,
            self.ar_map,
            dom=Computation,
            cod=ExecCategory
        )

    def ar_map(self, ar: object) -> Process:
        if isinstance(ar, Data):
            t = _lazy(Process.run_constant, ar)
        elif isinstance(ar, Swap):
            t = partial(Process.run_swap, ar)
        elif isinstance(ar, Copy):
            t = partial(Process.run_copy, ar)
        elif isinstance(ar, Merge):
            t = partial(Process.run_merge, ar)
        elif isinstance(ar, Discard):
            t = partial(Process.run_discard, ar)
        elif isinstance(ar, Exec):
             t = _lazy(partial(exec_deferred, self), ar)
        elif isinstance(ar, Program):
             t = _lazy(partial(exec_program, self), ar)
        elif isinstance(ar, Eval):
             t = _lazy(partial(exec_deferred, self), ar)
        else:
            t = _lazy(partial(exec_deferred, self), ar)

        dom = self(ar.dom)
        cod = self(ar.cod)
        res = Process(t, dom, cod)
        res.ar = ar
        return res


EXEC = ExecFunctor()

async def flatten(x: IO | list | tuple | str | None) -> list[str]:
    if x is None: return []
    if isinstance(x, StringIO):
        content = x.getvalue()
        return content.splitlines() if content else []
    if isinstance(x, (list, tuple)):
        res = []
        for item in x: res.extend(await flatten(item))
        return res
    if isinstance(x, str):
        return x.splitlines() if x else []
    return [str(x)]


async def trace_output(ar: T, res: U) -> U:
    from discopy.utils import tuplify
    # Only replicate streams, don't print
    if ar and isinstance(ar, (Data, Eval, Program)):
             
             new_res_vals = []
             
             for item in tuplify(res):
                 if isinstance(item, StringIO):
                      new_res_vals.append(StringIO(item.getvalue()))
                 else:
                      new_res_vals.append(item)

             if len(new_res_vals) <= 1:
                 return new_res_vals[0] if new_res_vals else None
             else:
                 return tuple(new_res_vals)
    return res
