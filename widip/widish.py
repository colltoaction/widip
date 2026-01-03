import asyncio
from functools import partial
from typing import Awaitable, Callable, Sequence, IO, TypeVar, Generic, Any
import sys
import contextvars
from contextlib import contextmanager

from io import StringIO, BytesIO
from discopy.utils import tuplify, untuplify
from discopy import closed, python, utils

from .computer import *
from .thunk import unwrap, Thunk
from .io import MultiStreamReader

U = TypeVar("U")
T = TypeVar("T")

# Internal detail: ContextVar to store the loop for factories and processes that don't have it.
LOOP_VAR: contextvars.ContextVar[asyncio.AbstractEventLoop | None] = contextvars.ContextVar("loop", default=None)

@contextmanager
def loop_scope(loop: asyncio.AbstractEventLoop | None):
    token = LOOP_VAR.set(loop)
    try:
        yield
    finally:
        LOOP_VAR.reset(token)

async def _bridge_pipe(loop: asyncio.AbstractEventLoop, f: Callable[..., Thunk[T]], g: Callable[..., Thunk[U]], *args: T) -> U:
    res = await unwrap(loop, f(*args))
    if res is None:
        return res # type: ignore
    return await unwrap(loop, g(*utils.tuplify(res)))

async def _tensor_inside(loop: asyncio.AbstractEventLoop, f: Callable[..., Thunk[T]], g: Callable[..., Thunk[U]], n: int, *args: T) -> tuple[T, ...]:
    args1, args2 = args[:n], args[n:]
    res1 = await unwrap(loop, f(*args1))
    res2 = await unwrap(loop, g(*args2))
    return tuplify(res1) + tuplify(res2) # type: ignore

async def _eval_func(loop: asyncio.AbstractEventLoop, f: Callable[..., Thunk[T]], *x: T) -> T:
    return await unwrap(loop, f(*x))


class Process(python.Function, Generic[T]):
    def __init__(self, inside: Callable[..., Thunk[T]], dom: closed.Ty, cod: closed.Ty, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__(inside, dom, cod)
        self.type_checking = False
        self.loop = loop

    async def __call__(self, *args: T) -> T:
        loop = self.loop or LOOP_VAR.get()
        if loop is None:
            raise RuntimeError(f"Process {self} called without an event loop")
        res = await unwrap(loop, self.inside(*args))
        return res

    def then(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(partial(_bridge_pipe, loop, self, other), self.dom, other.cod, loop=loop)

    def tensor(self, other: 'Process') -> 'Process':
        loop = self.loop or getattr(other, 'loop', None) or LOOP_VAR.get()
        return Process(partial(_tensor_inside, loop, self, other, len(self.dom)), self.dom + other.dom, self.cod + other.cod, loop=loop)

    @classmethod
    def eval(cls, base: closed.Ty, exponent: closed.Ty, left: bool = True) -> 'Process':
        loop = LOOP_VAR.get()
        return Process(partial(_eval_func, loop), (exponent << base) @ base, exponent, loop=loop)

    @staticmethod
    async def run_constant(ar: Any, *args: T) -> tuple[T, ...]:
        if ar.value:
            # Thread raw bytes stream instead of string
            return (BytesIO(ar.value.encode() if isinstance(ar.value, str) else ar.value), )
        return args

    @staticmethod
    async def run_map(runner: closed.Functor, ar: object, *args: object) -> tuple[object, ...]:
        return tuple(tuplify(await runner(ar.args[0])(*args)))

    @staticmethod
    async def run_seq(runner: closed.Functor, ar: object, *args: object) -> object:
        return await runner(ar.args[0])(*args)

    @staticmethod
    def run_swap(ar: Any, *args: T) -> tuple[T, ...]:
        n = len(ar.left)
        return args[n:] + args[:n]

    @staticmethod
    def run_cast(ar: Any, *args: T) -> T:
        return args[0] if args else None

    @staticmethod
    async def run_copy(ar: Any, *args: T) -> tuple[T, ...]:
        # Fulfills "don't read here": thread the same stream or data to all branches.
        # Note: If the input is a stream, it will be shared (consumed by the first reader).
        item = args[0] if args else b""
        return tuple(item for _ in range(len(ar.cod)))

    @staticmethod
    async def run_discard(ar: Any, *args: T) -> tuple[T, ...]:
        # Discarding means not reading
        return ()

    @staticmethod
    async def run_merge(ar: Any, *args: T) -> tuple[T, ...]:
        # Fulfills "don't read here": lazily merge multiple inputs without eager read to memory.
        return (MultiStreamReader(args),)

    @staticmethod
    def run_constant_gamma(ar: Any, *args: Any) -> Any:
        # Fulfills "thread this variable through Exec(sys.executable)"
        import sys
        return BytesIO(sys.executable.encode())
