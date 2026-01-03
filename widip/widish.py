import asyncio
from functools import partial
from typing import Awaitable, Callable, Sequence, IO, TypeVar, Generic, Any
import sys

from io import StringIO
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap, Thunk

U = TypeVar("U")
T = TypeVar("T")

async def _bridge_pipe(f: Callable[..., Thunk[T]], g: Callable[..., Thunk[U]], *args: T) -> U:
    loop = asyncio.get_running_loop()
    res = await unwrap(loop, f(*args))
    
    def is_failure(x: Any) -> bool:
        if x is None: return True
        return False

    if is_failure(res):
        return res # type: ignore
    
    return await unwrap(loop, g(*utils.tuplify(res)))

async def _tensor_inside(f: Callable[..., Thunk[T]], g: Callable[..., Thunk[U]], n: int, *args: T) -> tuple[T, ...]:
    # args tuple unpacking is hard to type precisely without Variadic Generics
    loop = asyncio.get_running_loop()
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(loop, f(*args1))
    res2 = await unwrap(loop, g(*args2))
    return tuplify(res1) + tuplify(res2) # type: ignore

async def _eval_func(f: Callable[..., Thunk[T]], *x: T) -> T:
    loop = asyncio.get_running_loop()
    return await unwrap(loop, f(*x))


class Process(python.Function, Generic[T]):
    def __init__(self, inside: Callable[..., Thunk[T]], dom: closed.Ty, cod: closed.Ty):
        super().__init__(inside, dom, cod)
        self.type_checking = False

    async def __call__(self, *args: T) -> T:
        # We need to unwrap the result of the internal function
        ar = getattr(self, "ar", None)
        loop = asyncio.get_running_loop()
        res = await unwrap(loop, self.inside(*args))
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
    async def run_constant(ar: Any, *args: T) -> tuple[T, ...]:
        if ar.value:
            return (StringIO(ar.value), )
        return args

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
    def run_swap(ar: Any, *args: T) -> tuple[T, ...]:
        n = len(ar.left)
        return args[n:] + args[:n]

    @staticmethod
    def run_cast(ar: Any, *args: T) -> T:
        return args[0] if args else None

    @staticmethod
    async def run_copy(ar: Any, *args: T) -> tuple[T, ...]:
        n = len(ar.cod)
        item = args[0] if args else ""
        if hasattr(item, 'read'):
            if hasattr(item, 'seek'): item.seek(0)
            data = item.read()
        else:
            data = str(item)
        return tuple(StringIO(data) for _ in range(n))

    @staticmethod
    async def run_discard(ar: Any, *args: T) -> tuple[T, ...]:
        for arg in args:
             if hasattr(arg, 'read'): arg.read()
        return ()

    @staticmethod
    async def run_merge(ar: Any, *args: T) -> tuple[T, ...]:
        contents = []
        for arg in args:
             if hasattr(arg, 'read'):
                 if hasattr(arg, 'seek'): arg.seek(0)
                 contents.append(arg.read())
             else:
                 contents.append(str(arg))
        return (StringIO("".join(contents)),)


    @staticmethod
    def run_constant_gamma(ar: Any, *args: T) -> str:
        return "bin/widish"
