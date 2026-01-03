import asyncio
import inspect

def is_awaitable(x):
    return inspect.isawaitable(x)

async def unwrap(x):
    """If x is awaitable, await it. Otherwise return x."""
    if is_awaitable(x):
        return await x
    return x

async def force_execution(val):
    """Recursively executes callables (Tasks) and unwraps iterables."""
    if is_awaitable(val):
        val = await val
        return await force_execution(val)

    if callable(val):
        # Assume it's a nullary task (args captured) or checks internally
        res = val()
        if is_awaitable(res):
            res = await res
        return await force_execution(res)

    if isinstance(val, (tuple, list)):
        # Execute in parallel
        results = await asyncio.gather(*(force_execution(x) for x in val))
        return type(val)(results)

    return val

def flatten(container):
    for i in container:
        if isinstance(i, (list, tuple)):
            yield from flatten(i)
        else:
            yield i
