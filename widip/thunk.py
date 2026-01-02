from collections.abc import Iterator, Callable
from contextlib import contextmanager
from functools import partial
from typing import Any
import asyncio
import contextvars
import inspect

Memo = dict[int, tuple[Any, asyncio.Future]]
memo_var: contextvars.ContextVar[Memo | None] = contextvars.ContextVar("memo", default=None)
path_var: contextvars.ContextVar[frozenset[int] | None] = contextvars.ContextVar("path", default=None)

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

def thunk[T](f: Callable[..., T], *args: Any) -> Callable[[], T]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(partial, f, *args)

def is_awaitable(x):
    return inspect.iscoroutine(x) or inspect.isawaitable(x)

def is_callable(x):
    return inspect.isroutine(x) or callable(x)

async def callable_unwrap(func, *args, **kwargs):
    result = func(*args, **kwargs)
    return await awaitable_unwrap(result)

async def awaitable_unwrap(aw):
    while is_awaitable(aw):
        aw = await aw
    return aw

async def thunk_map(b, *args):
    coroutines = [unwrap(kv(*args)) for kv in b]
    results = await asyncio.gather(*coroutines)
    return sum(results, ())

async def thunk_reduce(b, *args):
    for f in b:
        args = await unwrap(args)
        args = f(*args)
    return await unwrap(args)

def recurse(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to create a recursive fixed-point combinator with cycle detection."""
    async def wrapper(x: Any, state: tuple[Memo, frozenset[int]] | None = None) -> Any:
        if state is not None:
            return await _recurse_impl(f, x, state)

        with recursion_scope() as memo:
            return await _recurse_impl(f, x, (memo, frozenset()))
    return wrapper


async def _recurse_impl(
        f: Callable[..., Any],
        x: Any,
        state: tuple[Memo, frozenset[int]]) -> Any:
    memo, path = state
    id_x = id(x)
    if id_x in memo:
        _, fut = memo[id_x]
        if id_x in path:
            return x
        return await fut

    fut = asyncio.get_running_loop().create_future()
    memo[id_x] = (x, fut)
    call = partial(_recurse_impl, f, state=(memo, path | {id_x}))
    res = await callable_unwrap(f, call, x)
    fut.set_result(res)
    return res

@recurse
async def unwrap(recurse: Callable[[Any], Any], x: Any) -> Any:
    """Step function for unwrap logic."""
    while True:
        if is_callable(x):
            x = await callable_unwrap(x)
        elif is_awaitable(x):
            x = await awaitable_unwrap(x)
        else:
            break

    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        # Use recurse (the fixed-point step) for each item
        results = await asyncio.gather(*(recurse(i) for i in items))
        return tuple(results)

    return x
