from collections.abc import Iterator, Awaitable
from functools import partial
import asyncio


def thunk(f, *args):
    """Creates a thunk (lazy evaluation wrapper)."""
    return partial(partial, f, *args)

def _force_call(thunk):
    """Forces execution of callables until a non-callable is returned."""
    while callable(thunk):
        thunk = thunk()
    return thunk

def force(x):
    """Recursively forces thunks and untuplifies results."""
    x = _force_call(x)
    if isinstance(x, (Iterator, tuple, list)):
        x = tuple(map(force, x))
    if isinstance(x, (tuple, list)) and len(x) == 1:
        return x[0]
    return x

async def uncoro(x):
    """Recursively awaits awaitables and gathers results."""
    if isinstance(x, (Iterator, tuple, list)):
        items = list(x)
        results = await asyncio.gather(*(uncoro(i) for i in items))
        return tuple(results)

    if isinstance(x, Awaitable):
        return await uncoro(await x)

    return x
