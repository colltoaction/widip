import asyncio
from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap, is_awaitable

async def _bridge_pipe(f, g, *args):
    # f and g are Processes. f(*args) returns Awaitable.
    res = await unwrap(f(*args))
    # g expects inputs. res is output of f.
    # g(*res) returns Awaitable.
    return await unwrap(g(*utils.tuplify(res)))

async def _tensor_inside(f, g, n, *args):
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(f(*args1))
    res2 = await unwrap(g(*args2))
    return tuplify(res1) + tuplify(res2)

async def _eval_func(f, *x):
    return await unwrap(f(*x))

def _lazy(func, ar):
    """Returns a function that returns a partial application of func."""
    async def wrapper(*args):
        # Return a partial (Runner)
        # This wrapper is an async function, so calling it returns a Coroutine (Awaitable).
        # This Coroutine resolves to the partial.
        return partial(func, ar, *args)
    return wrapper

class Process(python.Function):
    def __init__(self, inside, dom, cod):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    def then(self, other):
        return Process(
            partial(_bridge_pipe, self, other),
            self.dom,
            other.cod,
        )

    def tensor(self, other):
        return Process(
            partial(_tensor_inside, self, other, len(self.dom)),
            self.dom + other.dom,
            self.cod + other.cod
        )

    @classmethod
    def eval(cls, base, exponent, left=True):
        return Process(
            _eval_func,
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
        return untuplify(params)

    @classmethod
    async def run_map(cls, ar, *args):
        b, params = cls.split_args(ar, *args)

        async def run_branch(kv):
             # kv is Awaitable (resolving to Task).
             task = await unwrap(kv)
             # task is Task (partial). Run it.
             res = await unwrap(task(*tuplify(params)))
             return tuplify(res) # Ensure tuple for sum

        results = await asyncio.gather(*(run_branch(kv) for kv in b))
        return sum(results, ())

    @classmethod
    async def run_seq(cls, ar, *args):
        b, params = cls.split_args(ar, *args)
        if not b:
            return params

        # Resolve first task
        task = await unwrap(b[0])
        # Run it
        res = await unwrap(task(*tuplify(params)))

        for kv in b[1:]:
            task = await unwrap(kv)
            res = await unwrap(task(*tuplify(res)))

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
        # this enables non-executable
        # YAML files to be run as commands
        if name.endswith(".yaml"):
            args = (name, ) + args
            name = "bin/widish"

        process = await asyncio.create_subprocess_exec(
            name, *args,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        input_data = "\n".join(stdin).encode() if stdin else None
        stdout, stderr = await process.communicate(input=input_data)
        if stderr:
            import sys
            print(stderr.decode(), file=sys.stderr)
        return stdout.decode().rstrip("\n")

    @classmethod
    async def deferred_exec(cls, ar, *args):
        b, params = cls.split_args(ar, *args)

        async def resolve(x):
            if is_awaitable(x):
                x = await unwrap(x)
            # If it's a runner (partial) for a value (Program/Constant), run it to get the value
            if callable(x):
                return await unwrap(x())
            return x

        # Resolve inputs (Awaitables -> Runners -> Values)
        b = tuple([await resolve(x) for x in b])
        params = tuple([await resolve(x) for x in params])

        # Flatten params
        flat_params = []
        for p in params:
             if isinstance(p, tuple):
                 flat_params.extend(p)
             else:
                 flat_params.append(p)
        params = tuple(flat_params)

        # Flatten b
        flat_b = []
        for x in b:
            if isinstance(x, tuple):
                flat_b.extend(x)
            else:
                flat_b.append(x)
        b = tuple(flat_b)

        name, cmd_args = (
            (ar.name, b) if ar.name
            else (b[0], b[1:]) if b
            else (None, ())
        )

        # Generic brace expansion for any command
        # e.g. {a, b} -> ("a", "b")
        if len(cmd_args) == 1 and cmd_args[0].startswith("{") and cmd_args[0].endswith("}"):
            # Parse simple {a, b} syntax
            content = cmd_args[0][1:-1]
            split_args = [s.strip() for s in content.split(",")]
            cmd_args = tuple(split_args)

        result = await cls.run_command(name, cmd_args, params)
        return result

    @staticmethod
    def run_program(ar, *args):
        return ar.name

    @staticmethod
    def run_constant_gamma(ar, *args):
        return "bin/widish"

Widish = closed.Category(python.Ty, Process)

def shell_runner_ar(ar):
    if isinstance(ar, Data):
        t = _lazy(Process.run_constant, ar)
    elif isinstance(ar, Concurrent):
        t = _lazy(Process.run_map, ar)
    elif isinstance(ar, Pair):
        t = _lazy(Process.run_seq, ar)
    elif isinstance(ar, Sequential):
        t = _lazy(Process.run_seq, ar)
    elif isinstance(ar, Swap):
        t = partial(Process.run_swap, ar)
    elif isinstance(ar, Cast):
        t = _lazy(Process.run_cast, ar)
    elif isinstance(ar, Copy):
        t = partial(Process.run_copy, ar)
    elif isinstance(ar, Discard):
        t = partial(Process.run_discard, ar)
    elif isinstance(ar, Exec):
         gamma = Constant()
         diagram = gamma @ closed.Id(ar.dom) >> Eval(ar.dom, ar.cod)
         return SHELL_RUNNER(diagram)
    elif isinstance(ar, Constant):
         t = _lazy(Process.run_constant_gamma, ar)
    elif isinstance(ar, Program):
         t = _lazy(Process.run_program, ar)
    elif isinstance(ar, Eval):
         t = _lazy(Process.deferred_exec, ar)
    else:
        t = _lazy(Process.deferred_exec, ar)

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
