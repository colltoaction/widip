import asyncio

from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import Data, Sequential, Concurrent, Swap, Copy, Discard, Cast, Computation
from .thunk import thunk, unwrap


def split_args(ar, *args):
    n = len(ar.dom)
    return args[:n], args[n:]

async def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, *args)
    if not params:
        if ar.dom == closed.Ty():
            if ar.cod and ar.cod != closed.Ty():
                return ar.cod.name
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
    left_len = len(ar.left)
    left_args = args[:left_len]
    right_args = args[left_len:]
    return untuplify(tuple(right_args + left_args))

def run_native_copy(ar, *args):
    if len(ar.dom) == 1:
        val = args[0]
        return untuplify(tuple(val for _ in range(len(ar.cod))))
    if len(ar.dom) == len(ar.cod):
         return untuplify(args)
    return untuplify(args)

def run_native_discard(ar, *args):
    return ()

def run_native_cast(ar, *args):
    return untuplify(args)

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

async def _deferred_exec_subprocess_value(name, args):
    _args = await unwrap(tuplify(args))
    return await run_command(name, [], _args)


class Process(python.Function):
    def then(self, other):
        # TODO thunk
        def bridge_pipe(*args):
             res = self(*args)
             tup_res = utils.tuplify(res)
             return other(*tup_res)

        return Process(
            bridge_pipe,
            self.dom,
            other.cod,
        )

    @classmethod
    def eval(cls, dom, cod):
        def func(f, *x):
            if isinstance(f, str):
                return _deferred_exec_subprocess_value(f, x)
            return f(*x)
        # Correct domain construction for Eval: (dom >> cod) @ dom
        return cls(func, (dom >> cod) @ dom, cod)


Widish = closed.Category(python.Ty, Process)


def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(run_native_subprocess_constant, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(run_native_subprocess_map, ar)
    elif isinstance(ar, Sequential):
        t = thunk(run_native_subprocess_seq, ar)
    elif isinstance(ar, Swap):
        t = thunk(run_native_swap, ar)
    elif isinstance(ar, Copy):
        t = thunk(run_native_copy, ar)
    elif isinstance(ar, Discard):
        t = thunk(run_native_discard, ar)
    elif isinstance(ar, Cast):
        t = thunk(run_native_cast, ar)
    else:
        t = thunk(_deferred_exec_subprocess_task, ar)

    # python.Ty takes a list of types as a single argument to avoid unpacking issues
    dom = python.Ty([object] * len(ar.dom))
    cod = python.Ty([object] * len(ar.cod))
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
