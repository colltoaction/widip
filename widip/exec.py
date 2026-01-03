import asyncio
from typing import IO, Callable, Awaitable, TypeVar
from io import StringIO
from functools import partial

from discopy import closed, python

from .computer import *
# Process is needed for class definition
from .widish import Process

T = TypeVar("T")

U = TypeVar("U")

async def safe_read_str(item: T | U) -> str:
    if hasattr(item, 'read'):
        content = item.read()
        if asyncio.iscoroutine(content):
            content = await content
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return content if content is not None else ""
    return str(item) if item is not None else ""

def _lazy(func: Callable[..., Awaitable[T]], ar: object) -> Callable[..., Awaitable[T]]:
    """Returns a function that returns a partial application of func."""
    async def wrapper(*args: object) -> T:
        return partial(func, ar, *args) # type: ignore
    return wrapper

async def run_command(runner: T, name: object, args: tuple[str, ...], stdin: U) -> asyncio.StreamReader:
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

        # 2. Check for YAML execution wrapper
        if name.endswith(".yaml"):
            str_args = tuple(map(str, args))
            args = (name, ) + str_args
            name = "bin/widish"

    if not isinstance(name, str):
        return StringIO("")

    args = tuple(map(str, args))

    # 3. Subprocess Execution
    process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
        name, *args,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def pipe_input():
        try:
            content = await safe_read_str(stdin)
            if content:
                process.stdin.write(content.encode("utf-8"))
                await process.stdin.drain()
        except Exception:
            pass
        finally:
            process.stdin.close()

    asyncio.create_task(pipe_input())

    return process.stdout

Exec = closed.Category(python.Ty, Process)

def exec_ob(ob: closed.Ty) -> type:
    if ob == Language or getattr(ob, "name", "") == "IO":
        return IO
    return object


# exec_ar removed

from .thunk import unwrap

async def exec_deferred(runner: T, ar: object, *args: U) -> U:
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
            # Eval wrapping name? If name is stream, read it.
            if hasattr(name, 'read'):
                name = (await safe_read_str(name)).strip()
            
            stdin_wires = resolved[-1]
            if isinstance(stdin_wires, (tuple, list)):
                pass 
            else:
                stdin_wires = [stdin_wires]
                
            cmd_args = resolved[1:-1]

    # Unwrap arguments
    final_args = []
    for arg in cmd_args:
            if isinstance(arg, (tuple, list)):
                arg = arg[0] if arg else ""
            if hasattr(arg, 'read'):
                content = (await safe_read_str(arg)).strip()
                final_args.append(content)
            else:
                final_args.append(str(arg))
            
    # Prepare Stdin Stream
    stdin_contents = []
    if isinstance(stdin_wires, (tuple, list)):
            for w in stdin_wires:
                stdin_contents.append(await safe_read_str(w))
    else:
            stdin_contents.append(await safe_read_str(stdin_wires))
            
    stdin_stream = StringIO("".join(stdin_contents))

    return await run_command(runner, name, final_args, stdin_stream)


async def exec_program(runner: T, ar: object, *args: U) -> U:
    # Programs take all inputs from wires as stdin
    # Merge args into single stream
    contents = []
    for arg in args:
            contents.append(await safe_read_str(arg))
    stdin_stream = StringIO("".join(contents))
    
    return await run_command(runner, ar.name, ar.args, stdin_stream)


class ExecFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            exec_ob,
            self.ar_map,
            dom=Computation,
            cod=Exec
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

def flatten(x: IO | list | tuple | str | None) -> list[str]:
    if x is None: return []
    if hasattr(x, 'read'):
        content = x.read()
        return content.splitlines() if content else []
    if isinstance(x, (list, tuple)):
        res = []
        for item in x: res.extend(flatten(item))
        return res
    return [str(x)]

async def trace_output(ar: T, res: U) -> U:
    from discopy.utils import tuplify
    if ar and isinstance(ar, (Data, Eval, Program)):
             
             print_vals = []
             new_res_vals = []
             
             for item in tuplify(res):
                 if hasattr(item, "read"):
                      content = await safe_read_str(item)
                      print_vals.append(content)
                      new_res_vals.append(StringIO(content))
                 else:
                      print_vals.append(item)
                      new_res_vals.append(item)

             trace_out = flatten(print_vals)
             if trace_out:
                 print(*trace_out, sep="\n", flush=True)
            
             if len(new_res_vals) <= 1:
                 return new_res_vals[0] if new_res_vals else None
             else:
                 return tuple(new_res_vals)
    return res
