from collections.abc import Iterator, Callable
from functools import partial
from typing import Any
import asyncio
import inspect

def thunk[T](f: Callable[..., T], *args: Any) -> Callable[[], T]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(partial, f, *args)

async def recurse(
        f: Callable[..., Any],
        x: Any,
        state: tuple[dict[int, asyncio.Future], frozenset[int]] | None = ({}, frozenset())) -> Any:
    """Generic recursive fixed-point combinator with cycle detection."""
    memo, path = state
    id_x = id(x)
    if id_x in memo:
        fut = memo[id_x]
        if id_x in path:
            # Cycle detected: return the raw object to break recursion
            return x
        # Diamond / Shared Dependency: wait for the result
        return await fut

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    memo[id_x] = fut
    new_path = path | {id_x}

    call = partial(recurse, f, state=(memo, new_path))
    res = await f(call, x)
    fut.set_result(res)
    return res

async def unwrap_step(recurse: Callable[[Any], Any], x: Any) -> Any:
    """Step function for unwrap logic."""
    while True:
        if inspect.isroutine(x) or callable(x):
            x = x()
        elif inspect.iscoroutine(x) or inspect.isawaitable(x):
            res = await x
            if res is x:
                break
            x = res
            return await recurse(x)
        else:
            break

    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(recurse(i) for i in items))
        return tuple(results)

    return x

unwrap = partial(recurse, unwrap_step)
