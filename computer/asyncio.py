"""Async operations for computer module

Provides async/await functionality for computational diagrams.
"""

import asyncio
from functools import wraps

def unwrap(value):
    """Unwrap a value, handling async results
    
    Args:
        value: Value to unwrap
        
    Returns:
        Unwrapped value
    """
    if asyncio.iscoroutine(value):
        return asyncio.run(value)
    return value

async def pipe_async(*funcs):
    """Async pipe composition
    
    Args:
        *funcs: Functions to compose
        
    Returns:
        Composed async function
    """
    async def composed(x):
        result = x
        for f in funcs:
            if asyncio.iscoroutinefunction(f):
                result = await f(result)
            else:
                result = f(result)
        return result
    return composed

async def tensor_async(*funcs):
    """Async tensor product
    
    Args:
        *funcs: Functions to tensor
        
    Returns:
        Tensored async function
    """
    async def tensored(*args):
        results = await asyncio.gather(*[
            f(arg) if asyncio.iscoroutinefunction(f) else asyncio.coroutine(lambda: f(arg))()
            for f, arg in zip(funcs, args)
        ])
        return results
    return tensored

__all__ = ['unwrap', 'pipe_async', 'tensor_async']
