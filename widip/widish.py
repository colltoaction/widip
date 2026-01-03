import asyncio
from functools import partial
from typing import Awaitable, Callable, Sequence, IO, TypeVar, Generic

from io import StringIO
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap

U = TypeVar("U")
T = TypeVar("T")

async def _bridge_pipe(f: Callable[..., Awaitable[T]], g: Callable[..., Awaitable[U]], *args: T) -> U:
    res = await unwrap(f(*args))
    
    def is_failure(x: object) -> bool:
        if x is None: return True
        return False

    if is_failure(res):
        return res # type: ignore
    
    return await unwrap(g(*utils.tuplify(res)))

async def _tensor_inside(f: Callable[..., Awaitable[T]], g: Callable[..., Awaitable[U]], n: int, *args: object) -> tuple[T, ...]:
    # args tuple unpacking is hard to type precisely without Variadic Generics
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(f(*args1))
    res2 = await unwrap(g(*args2))
    return tuplify(res1) + tuplify(res2) # type: ignore

async def _eval_func(f: Callable[..., Awaitable[T]], *x: object) -> T:
    return await unwrap(f(*x))



class Process(python.Function, Generic[T]):
    def __init__(self, inside: Callable[..., Awaitable[T]], dom: closed.Ty, cod: closed.Ty):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    async def __call__(self, *args: object) -> T:
        # We need to unwrap the result of the internal function
        ar = getattr(self, "ar", None)
        # print(f"DEBUG: Process call ar={ar}", file=sys.stderr)
        res = await unwrap(self.inside(*args))
        
        # Feedback trace: print results of all atomic boxes
        from .exec import trace_output
        res = await trace_output(ar, res)

        return res

    def then(self, other: 'Process') -> 'Process':
        return Process(
            partial(_bridge_pipe, self, other),
            self.dom,
            other.cod,
        )

    def tensor(self, other: 'Process') -> 'Process':
        return Process(
            partial(_tensor_inside, self, other, len(self.dom)),
            self.dom + other.dom,
            self.cod + other.cod
        )

    @classmethod
    def eval(cls, base: closed.Ty, exponent: closed.Ty, left: bool = True) -> 'Process':
        return Process(
            _eval_func,
            (exponent << base) @ base,
            exponent
        )



    @staticmethod
    async def run_constant(ar: object, *args: object) -> tuple[IO, ...]:
        if ar.value:
            return (StringIO(ar.value), )
        n = 1
        return args[n:] if len(args) > n else ()

    @staticmethod
    async def run_map(runner: closed.Functor, ar: object, *args: object) -> tuple[object, ...]:
        inner_runner = runner(ar.args[0])
        res = await inner_runner(*args)
        return tuple(tuplify(res))

    @staticmethod
    async def run_seq(runner: closed.Functor, ar: object, *args: object) -> object:
        inner_runner = runner(ar.args[0])
        return await inner_runner(*args)

    @staticmethod
    def run_swap(ar: object, *args: object) -> tuple[object, ...]:
        n = len(ar.left)
        return args[n:] + args[:n]

    @staticmethod
    def run_cast(ar: object, *args: object) -> object:
        return args[0] if args else None

    @staticmethod
    async def run_copy(ar: object, *args: object) -> tuple[IO | None, ...]:
        val = args[0] if args else None
        if val is None:
             return (None,) * ar.n
        
        # If val is IO stream, read and replicate
        from .exec import safe_read_str
        if hasattr(val, 'read'):
             data = await safe_read_str(val)
             return tuple(StringIO(data) for _ in range(ar.n))
        return (val,) * ar.n

    @staticmethod
    async def run_discard(ar: object, *args: object) -> tuple[object, ...]:
        # Consume stream to avoid leaks/buffering issues?
        from .exec import safe_read_str
        for arg in args:
             await safe_read_str(arg)
        return ()

    @staticmethod
    async def run_merge(ar: object, *args: object) -> tuple[IO, ...]:
        # Merge streams into one
        contents = []
        from .exec import safe_read_str
        contents = []
        for arg in args:
             contents.append(await safe_read_str(arg))
        return (StringIO("".join(contents)),)







    @staticmethod
    def run_constant_gamma(ar: object, *args: object) -> str:
        return "bin/widish"


