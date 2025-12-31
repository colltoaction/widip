import asyncio

from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed

from .computer import *
from .thunk import thunk, unwrap


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
    # Pipeline execution: b[0](params) -> b[1](res0) -> ...
    if not b:
        return params # Or empty?

    res = b[0](*tuplify(params))
    for func in b[1:]:
        res = func(*tuplify(res))
    return res

def run_native_swap(ar, *args):
    n_left = len(ar.left)
    n_right = len(ar.right)
    left_args = args[:n_left]
    right_args = args[n_left : n_left + n_right]
    return untuplify(right_args + left_args)

def run_native_cast(ar, *args):
    b, params = split_args(ar, *args)
    func = b[0]
    return func

def run_native_copy(ar, *args):
    b, params = split_args(ar, *args)
    return b * ar.n

def run_native_discard(ar, *args):
    return ()

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
    async_b, async_params = map(unwrap, map(tuplify, split_args(ar, *args)))
    b, params = await asyncio.gather(async_b, async_params)
    name, cmd_args = (
        (ar.name, b) if ar.name 
        else (b[0], b[1:]) if b 
        else (None, ())
    )
    result = await run_command(name, cmd_args, params)
    return result if ar.cod else ()

def run_program(ar, *args):
    return ar.name

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(run_native_subprocess_constant, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(run_native_subprocess_map, ar)
    elif isinstance(ar, Pair):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Sequential):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Swap):
        t = partial(run_native_swap, ar)
    elif isinstance(ar, Cast):
        t = thunk(run_native_cast, ar)
    elif isinstance(ar, Copy):
        t = partial(run_native_copy, ar)
    elif isinstance(ar, Discard):
        t = partial(run_native_discard, ar)
    elif isinstance(ar, Exec):
         t = thunk(_deferred_exec_subprocess, ar)
    elif isinstance(ar, Program):
         t = thunk(run_program, ar)
    else:
        t = thunk(_deferred_exec_subprocess, ar)

    dom = SHELL_RUNNER(ar.dom)
    cod = SHELL_RUNNER(ar.cod)
    return Process(t, dom, cod)

class WidishFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: object,
            shell_runner_ar,
            dom=Computation,
            cod=Widish
        )

SHELL_RUNNER = WidishFunctor()
