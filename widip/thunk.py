from collections.abc import Iterator, Awaitable
from functools import partial
import asyncio


def thunk(f, *args):
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(partial, f, *args)


async def unwrap(x):
    """Recursively forces thunks and awaits awaitables."""
    while callable(x) or isinstance(x, Awaitable):
        if callable(x):
            x = x()
        elif isinstance(x, Awaitable):
            x = await x

    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(unwrap(i) for i in items))
        x = tuple(results)

    return x
