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


async def safe_read_str(item: IO[str] | str | Sequence[Any] | None) -> str:
    """Safely read content from anything into a string."""
    if item is None: return ""
    if hasattr(item, 'read'):
        res = item.read()
        if hasattr(item, 'seek'): item.seek(0)
        return res
    if isinstance(item, (list, tuple)):
        return "".join([await safe_read_str(i) for i in item])
    return str(item)


async def run_command(runner: 'ExecFunctor', name: str, args: Sequence[str], stdin: IO[str]) -> StringIO:
    if name in (registry := RECURSION_REGISTRY.get()):
         item = registry[name]
         if not callable(item):
              item = runner(item)
              registry[name] = item
              RECURSION_REGISTRY.set(dict(registry))
         return await unwrap(item(stdin))

    import subprocess
    cmd = [name] + list(args)
    stdin_content = await safe_read_str(stdin)
    result = await runner.loop.run_in_executor(
        None, partial(subprocess.run, cmd, input=stdin_content, capture_output=True, text=True)
    )
    return StringIO(result.stdout)


async def exec_generic(runner: 'ExecFunctor', ar: object, *args: Any) -> Any:
    resolved = [await unwrap(arg) for arg in args]
    
    if isinstance(ar, Program):
        name, raw_args, stdin_val = ar.name, ar.args, resolved
    elif isinstance(ar, (Exec, Eval)) and resolved:
        name, raw_args, stdin_val = await safe_read_str(resolved[0]), resolved[1:-1], resolved[-1:]
    else:
        name, raw_args, stdin_val = str(getattr(ar, 'name', ar)), [], resolved

    cmd_args = []
    for arg in raw_args:
        if isinstance(arg, closed.Diagram):
            arg_res = await unwrap(runner(arg)(*utils.tuplify(stdin_val)))
            cmd_args.append(await safe_read_str(arg_res))
        else:
            cmd_args.append(await safe_read_str(arg))

    return await run_command(runner, name, cmd_args, StringIO(await safe_read_str(stdin_val)))


class ExecFunctor(closed.Functor):
    def __init__(self, executable: Any = None, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__(self.ob_map, self.ar_map, dom=Computation, cod=ExecCategory)
        self.executable, self.loop = executable, loop

    def ob_map(self, ob: closed.Ty) -> type:
        return IO if ob == Language else object

    def ar_map(self, ar: object) -> Process:
        mapping = {Data: Process.run_constant, Swap: Process.run_swap, Copy: Process.run_copy,
                   Merge: Process.run_merge, Discard: Process.run_discard}
        t = partial(mapping.get(type(ar), partial(exec_generic, self)), ar)

        async def traced_t(*args: Any) -> Any:
            res = await unwrap(t(*args))
            if isinstance(ar, (Data, Eval, Program)):
                res = utils.untuplify(tuple(StringIO(await safe_read_str(i)) if hasattr(i, 'read') else i 
                                           for i in utils.tuplify(res)))
            return res

        res = Process(traced_t, self(ar.dom), self(ar.cod))
        res.ar = ar
        return res


ExecCategory = closed.Category(python.Ty, Process)


async def flatten(x: Any) -> list[str]:
    return (await safe_read_str(x)).splitlines()
