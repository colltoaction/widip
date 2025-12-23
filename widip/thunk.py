from collections.abc import Iterator, Awaitable, Callable
from functools import partial
from typing import Any
import asyncio

type T = Any
type B = Any
type FoliatedObject[T, B] = tuple[T, B]

def thunk[T](f: Callable[..., T], *args: Any) -> Callable[[], T]:
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(partial, f, *args)

async def unwrap(x: Any, memo: dict[int, asyncio.Future] | None = None, _path: set[int] | None = None) -> Any:
    """Recursively forces thunks and awaits awaitables."""
    if memo is None:
        memo = {}
    if _path is None:
        _path = frozenset()

    if id(x) in memo:
        fut = memo[id(x)]
        if id(x) in _path:
            # Cycle detected: return the raw object to break recursion
            return x
        # Diamond / Shared Dependency: wait for the result
        return await fut

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    memo[id(x)] = fut
    current_path = _path | {id(x)}

    try:
        while callable(x) or isinstance(x, Awaitable):
            if callable(x):
                x = x()
            elif isinstance(x, Awaitable):
                res = await x
                if res is x:
                    break
                x = res
                if id(x) in memo:
                    other_fut = memo[id(x)]
                    if id(x) in current_path:
                        result = x
                    else:
                        result = await other_fut
                    fut.set_result(result)
                    return result

        if isinstance(x, (Iterator, tuple, list)):
            items = list(x)
            results = await asyncio.gather(*(unwrap(i, memo, current_path) for i in items))
            result = tuple(results)
        else:
            result = x

        fut.set_result(result)
        return result

    except Exception as e:
        if not fut.done():
            fut.set_exception(e)
        raise

def p_functor[T, B](obj: FoliatedObject[T, B]) -> B:
    """Maps an object to its base index (the 'fibre' it belongs to)."""
    return obj[1]

def vertical_map[T, B](obj: FoliatedObject[T, B], f: Callable[[T], T]) -> FoliatedObject[T, B]:
    """Transformation where P(f(obj)) == P(obj)."""
    return (f(obj[0]), obj[1])

def cartesian_lift[T, B](obj: FoliatedObject[T, B], new_index: B, lift_fn: Callable[[T, B], T]) -> FoliatedObject[T, B]:
    """Transformation that moves the object from one fibre to another."""
    return (lift_fn(obj[0], new_index), new_index)
