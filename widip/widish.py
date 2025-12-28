import asyncio
import inspect

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
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    return b1

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

async def run_native_trace(ar, *args):
    process = SHELL_RUNNER(ar.arg)
    n_left = len(ar.dom)
    n_trace = len(ar.arg.dom) - n_left

    loop = asyncio.get_running_loop()
    futures = [loop.create_future() for _ in range(n_trace)]

    inputs = args + tuple(futures)
    outputs = process(*inputs)

    if inspect.iscoroutine(outputs):
        outputs = await outputs

    outputs = tuplify(outputs)
    n_out = len(ar.cod)

    b_out = outputs[:n_out]
    u_out = outputs[n_out:]

    for f, val in zip(futures, u_out):
        f.set_result(val)

    return untuplify(b_out)

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
    elif isinstance(ar, Trace):
        t = thunk(run_native_trace, ar)
    else:
        t = thunk(_deferred_exec_subprocess_task, ar)

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
