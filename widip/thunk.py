from collections.abc import Iterator, Callable, Awaitable
from contextlib import contextmanager
from functools import partial
from typing import Any, TypeVar, Union
import asyncio
import contextvars
import inspect

T = TypeVar("T")

Memo = dict[int, tuple[Any, asyncio.Future]]
memo_var: contextvars.ContextVar[Memo | None] = contextvars.ContextVar("memo", default=None)

# Thunk is a zero-argument callable, an awaitable, or the value itself
Thunk = Union[Callable[[], Union[Awaitable[T], T]], Awaitable[T], T]

@contextmanager
def recursion_scope():
    memo = memo_var.get()
    token = None
    if memo is None:
        memo = {}
        token = memo_var.set(memo)
    try:
        yield memo
    finally:
        if token:
            memo_var.reset(token)

def thunk(f: Callable[..., T], *args: Any) -> Callable[[], T]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(f, *args)

async def callable_unwrap(func: Callable[[], Thunk[T]]) -> T:
    # Thunk doesn't receive parameters
    result = func()
    return await awaitable_unwrap(result)

async def awaitable_unwrap(aw: Thunk[T]) -> T:
    while True:
        match aw:
            case _ if inspect.iscoroutine(aw) or inspect.isawaitable(aw):
                aw = await aw
            case _:
                return aw

async def thunk_map(b: Iterator[Callable[[], Thunk[T]]]) -> tuple:
    loop = asyncio.get_running_loop()
    coroutines = [unwrap(loop, kv()) for kv in b]
    results = await asyncio.gather(*coroutines)
    return sum(results, ())

async def thunk_reduce(b: Iterator[Callable[[], Thunk[T]]]) -> T:
    loop = asyncio.get_running_loop()
    res = None
    for f in b:
        res = f()
    return await unwrap(loop, res)

async def recurse(
        f: Callable[..., Any],
        x: Any,
        loop: asyncio.AbstractEventLoop,
        state: tuple[Memo, frozenset[int]] | None = None) -> Any:
    
    # Internal implementation details merged here
    if state is None:
         with recursion_scope() as memo:
             return await recurse(f, x, loop, (memo, frozenset()))

    memo, path = state
    id_x = id(x)
    
    if id_x in memo:
        _, fut = memo[id_x]
        if id_x in path:
            return x
        return await fut

    fut = loop.create_future()
    memo[id_x] = (x, fut)
    
    # Partial for the recursive step
    # We pass 'recurse' (this function) but pre-bound with loop and updated state
    # f expects: (rec_callback, x) return result
    
    # The callback f receives should accept (x) and run it recursively
    # We define the callback to match f's expected signature
    
    async def callback(item):
         return await recurse(f, item, loop, (memo, path | {id_x}))
         
    res = await callable_unwrap(lambda: f(callback, x))
    fut.set_result(res)
    return res

async def unwrap_step(rec: Callable[[Any], Awaitable[T]], x: Thunk[T]) -> T | tuple[T, ...]:
    """Step function for unwrap logic."""
    while True:
        match x:
            case _ if callable(x) and not isinstance(x, (list, tuple, dict, str)):
                 x = await callable_unwrap(x)
            case _ if inspect.iscoroutine(x) or inspect.isawaitable(x):
                 x = await awaitable_unwrap(x)
            case _:
                 break

    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(rec(i) for i in items))
        return tuple(results)

    return x

async def unwrap(loop: asyncio.AbstractEventLoop, x: Thunk[T]) -> T | tuple[T, ...]:
    return await recurse(unwrap_step, x, loop)
