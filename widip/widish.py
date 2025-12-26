import asyncio

from discopy.utils import tuplify, untuplify
from discopy import closed, python

from .compiler import Data, Sequential, Concurrent
from .thunk import thunk, unwrap
from .yaml import Str, Seq, Map


def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

async def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, *args)
    if not params:
        if ar.dom == closed.Ty():
            return ()
        return ar.dom.name
    return untuplify(await unwrap(params))

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, *args)
    return untuplify(tuple(kv(*tuplify(params)) for kv in b))

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
    _b = await unwrap(tuplify(b))
    _params = await unwrap(tuplify(params))
    result = await run_command(ar.name, _b, _params)
    if not ar.cod:
        return ()
    return result

def _deferred_exec_subprocess_task(ar, *args):
    return asyncio.create_task(_deferred_exec_subprocess(ar, *args))

def shell_runner_ar(ar):
    if isinstance(ar, (Data, Str)):
        return thunk(run_native_subprocess_constant, ar)
    if isinstance(ar, (Concurrent, Map)):
        return thunk(run_native_subprocess_map, ar)
    if isinstance(ar, (Sequential, Seq)):
        return thunk(run_native_subprocess_seq, ar)
    return thunk(_deferred_exec_subprocess_task, ar)

SHELL_RUNNER = closed.Functor(
    lambda ob: object,
    shell_runner_ar,
    cod=closed.Category(python.Ty, python.Function))
