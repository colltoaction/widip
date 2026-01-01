import asyncio

from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import thunk, unwrap

class Process(python.Function):
    def __init__(self, inside, dom, cod):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    def then(self, other):
        bridge_pipe = lambda *args: other(*utils.tuplify(self(*args)))
        return Process(
            bridge_pipe,
            self.dom,
            other.cod,
        )

    def tensor(self, other):
        return Process(
            super().tensor(other).inside,
            self.dom + other.dom,
            self.cod + other.cod
        )

    @classmethod
    def eval(cls, base, exponent, left=True):
        def func(f, *x):
             return f(*x)
        return Process(
            func,
            (exponent << base) @ base,
            exponent
        )

    @staticmethod
    def split_args(ar, *args):
        n = len(ar.dom)
        return args[:n], args[n:]

    @classmethod
    async def run_constant(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        if not params:
            if ar.dom == closed.Ty():
                return ()
            return ar.dom.name
        return untuplify(await unwrap(params))

    @classmethod
    def run_map(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        return untuplify(tuple(kv(*tuplify(params)) for kv in b))

    @classmethod
    def run_seq(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        if not b:
            return params

        res = b[0](*tuplify(params))
        for func in b[1:]:
            res = func(*tuplify(res))
        return res

    @staticmethod
    def run_swap(ar, *args):
        n_left = len(ar.left)
        n_right = len(ar.right)
        left_args = args[:n_left]
        right_args = args[n_left : n_left + n_right]
        return untuplify(right_args + left_args)

    @classmethod
    def run_cast(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        func = b[0]
        return func

    @classmethod
    def run_copy(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        return b * ar.n

    @staticmethod
    def run_discard(ar, *args):
        return ()

    @staticmethod
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

    @classmethod
    async def deferred_exec(cls, ar, *args):
        async_b, async_params = map(unwrap, map(tuplify, cls.split_args(ar, *args)))
        b, params = await asyncio.gather(async_b, async_params)
        name, cmd_args = (
            (ar.name, b) if ar.name
            else (b[0], b[1:]) if b
            else (None, ())
        )
        result = await cls.run_command(name, cmd_args, params)
        return result if ar.cod else ()

    @staticmethod
    def run_program(ar, *args):
        return ar.name

    @staticmethod
    def run_constant_gamma(ar, *args):
        return "bin/widish"

Widish = closed.Category(python.Ty, Process)

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = thunk(Process.run_constant, ar)
    elif isinstance(ar, Concurrent):
        t = thunk(Process.run_map, ar)
    elif isinstance(ar, Pair):
        t = thunk(Process.run_seq, ar)
    elif isinstance(ar, Sequential):
        t = thunk(Process.run_seq, ar)
    elif isinstance(ar, Swap):
        t = partial(Process.run_swap, ar)
    elif isinstance(ar, Cast):
        t = thunk(Process.run_cast, ar)
    elif isinstance(ar, Copy):
        t = partial(Process.run_copy, ar)
    elif isinstance(ar, Discard):
        t = partial(Process.run_discard, ar)
    elif isinstance(ar, Exec):
         gamma = Constant()
         diagram = gamma @ closed.Id(ar.dom) >> Eval(ar.dom, ar.cod)
         return SHELL_RUNNER(diagram)
    elif isinstance(ar, Constant):
         t = thunk(Process.run_constant_gamma, ar)
    elif isinstance(ar, Program):
         t = thunk(Process.run_program, ar)
    elif isinstance(ar, Eval):
         t = thunk(Process.deferred_exec, ar)
    else:
        t = thunk(Process.deferred_exec, ar)

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
