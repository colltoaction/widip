from collections.abc import Iterator, Awaitable
from functools import cache, partial
import asyncio

from discopy.utils import tuplify
from discopy import closed, python


def thunk(f, *args):
    return partial(partial, f, *args)

@cache
def _force_call(thunk):
    while callable(thunk):
        thunk = thunk()
    return thunk

def force(x):
    x = _force_call(x)
    if isinstance(x, (Iterator, tuple, list)):
        # Recursively force items in iterator or sequence
        x = tuple(map(force, x))
    
    # "untuplify" logic: unwrap singleton tuple/list
    if isinstance(x, (tuple, list)) and len(x) == 1:
        return x[0]
    return x

async def uncoro(x):
    if isinstance(x, Awaitable):
        return await uncoro(await x)
        
    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(uncoro(i) for i in items))
        return tuple(results)

    return x

def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, *args)
    if not params:
        if ar.dom == closed.Ty():
            return ()
        return ar.dom.name
    return force(params)

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, *args)
    return force(kv(*tuplify(params)) for kv in b)

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, *args)
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    return b1

async def run_command(name, args, stdin):
    process = await asyncio.create_subprocess_exec(
        name, *args,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    input_data = "\n".join(stdin).encode() if stdin else None
    stdout, stderr = await process.communicate(input=input_data)
    return stdout.decode().rstrip("\n")

async def _deferred_exec_subprocess(ar, *args):
    b, params = split_args(ar, *args)
    _b = await uncoro(tuplify(force(b)))
    _params = await uncoro(tuplify(force(params)))
    result = await run_command(ar.name, _b, _params)
    if not ar.cod:
        return ()
    return result

def _deferred_exec_subprocess_task(ar, *args):
    return asyncio.create_task(_deferred_exec_subprocess(ar, *args))


SHELL_RUNNER = closed.Functor(
    lambda ob: object,
    lambda ar: {
        "⌜−⌝": thunk(run_native_subprocess_constant, ar),
        "(||)": thunk(run_native_subprocess_map, ar),
        "(;)": thunk(run_native_subprocess_seq, ar),
    }.get(ar.name, thunk(_deferred_exec_subprocess_task, ar)),
    cod=closed.Category(python.Ty, python.Function))
