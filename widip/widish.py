import asyncio
import sys
from functools import partial
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap

async def _bridge_pipe(f, g, *args):
    res = await unwrap(f(*args))
    
    def is_failure(x):
        if x is None: return True
        if isinstance(x, (list, tuple)):
            return not x or all(is_failure(i) for i in x)
        return False

    if is_failure(res):
        return res
    
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
        return partial(func, ar, *args)
    return wrapper

class Process(python.Function):
    def __init__(self, inside, dom, cod):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    async def __call__(self, *args):
        # We need to unwrap the result of the internal function
        ar = getattr(self, "ar", None)
        res = await unwrap(self.inside(*args))
        
        # Feedback trace: print results of all atomic boxes
        if ar and isinstance(ar, (Data, Eval, Program)):
             from .interactive import flatten
             filtered = flatten(res)
             if filtered:
                 print(*filtered, sep="\n", flush=True)
        return res

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
        # We need to handle when dom is not a Ty (e.g. object)
        try:
            n = len(ar.dom)
        except TypeError:
            n = 1
        return args[:n], args[n:]

    @classmethod
    async def run_constant(cls, ar, *args):
        if ar.value:
            return (ar.value, )
        b, params = cls.split_args(ar, *args)
        return untuplify(params)

    @classmethod
    async def run_map(cls, ar, *args):
        # Delegates to the internal diagram which handles Copy and tensor
        runner = SHELL_RUNNER(ar.args[0])
        res = await runner(*args)
        # Filter out None values (failed branches)
        from .interactive import flatten
        return tuple(flatten(res))

    @classmethod
    async def run_seq(cls, ar, *args):
        # Delegates to the internal diagram
        runner = SHELL_RUNNER(ar.args[0])
        return await runner(*args)

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
        val = b[0] if b else params[0] if params else ""
        if val is None:
             return (None,) * ar.n
        return (val,) * ar.n

    @staticmethod
    def run_discard(ar, *args):
        return ()

    @staticmethod
    def run_merge(ar, *args):
        from .interactive import flatten
        return tuple(flatten(args))

    @staticmethod
    async def run_command(name, args, stdin):
        from .widish import SHELL_RUNNER
        from .compiler import SHELL_COMPILER
        
        if any(x is None for x in stdin):
             return (None,)

        if not isinstance(name, str):
             return await unwrap(name(*(tuplify(args) + tuplify(stdin))))

        # Recurse
        if name in (registry := RECURSION_REGISTRY.get()):
             item = registry[name]
             if not callable(item):
                  compiled = SHELL_COMPILER(item)
                  runner = SHELL_RUNNER(compiled)
                  registry[name] = runner
                  RECURSION_REGISTRY.set(dict(registry))
             else:
                  runner = item
             return await runner(*tuplify(stdin))

        if name.endswith(".yaml"):
            args = (name, ) + args
            name = "bin/widish"
            
        process = await asyncio.create_subprocess_exec(
            name, *map(str, args),
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        input_data = "\n".join(map(str, stdin)).encode() if stdin else None
        stdout, stderr = await process.communicate(input=input_data)
        
        if process.returncode != 0:
             return (None,)

        res_str = stdout.decode()
        if not res_str.strip():
             if name in ("awk", "grep"): return (None,)
             return tuple(stdin)
        
        return tuple(res_str.splitlines())

    @classmethod
    async def deferred_exec(cls, ar, *args):
        async def resolve(x):
            if callable(x):
                return await unwrap(x())
            return x

        # Resolve all input wires
        resolved = []
        for x in args:
            res = await resolve(x)
            # If it's a tuple of lines (from a command), we keep it as a single unit for now
            # unless it's explicitly multiple wires. 
            # But Eval expects 1 object per wire.
            resolved.append(res)
        
        if ar.name:
             # Constant/Program call
             name = ar.name
             cmd_args = resolved
             stdin = ()
        else:
             # Eval case: (Name, [Args...], Stdin)
             if not resolved: return (None,)
             name = resolved[0]
             stdin = resolved[-1]
             cmd_args = resolved[1:-1]

        # Unwrap name if it is a list/tuple (e.g. from Data box or ar.name)
        if isinstance(name, (list, tuple)):
            if len(name) == 1:
                name = name[0]
            elif not name:
                return (None,)
        
        # Unwrap arguments
        cmd_args = [x[0] if isinstance(x, (list, tuple)) and len(x) == 1 else x for x in cmd_args]
             
        # Ensure stdin is a collection of lines

        # Ensure stdin is a collection of lines
        if isinstance(stdin, str): stdin = (stdin,)
        if stdin is None: stdin = ()
        # If it's a tuple of tuples (nested), flatten it
        def flatten_lines(x):
            if isinstance(x, (list, tuple)):
                res = []
                for i in x: res.extend(flatten_lines(i))
                return res
            return [x]
        stdin = flatten_lines(stdin)

        return await cls.run_command(name, cmd_args, stdin)

    @classmethod
    async def run_program(cls, ar, *args):
        # Programs take all inputs from wires as stdin
        return await cls.run_command(ar.name, ar.args, args)

    @staticmethod
    def run_constant_gamma(ar, *args):
        return "bin/widish"

Widish = closed.Category(python.Ty, Process)

def shell_runner_ar(ar):
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
         t = _lazy(Process.deferred_exec, ar)
    elif isinstance(ar, Program):
         t = _lazy(Process.run_program, ar)
    elif isinstance(ar, Eval):
         t = _lazy(Process.deferred_exec, ar)
    else:
        t = _lazy(Process.deferred_exec, ar)

    dom = SHELL_RUNNER(ar.dom)
    cod = SHELL_RUNNER(ar.cod)
    res = Process(t, dom, cod)
    res.ar = ar
    return res

class WidishFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: object,
            shell_runner_ar,
            dom=Computation,
            cod=Widish
        )

SHELL_RUNNER = WidishFunctor()
