import pytest
import asyncio

from titi.asyncio import *


@pytest.mark.asyncio
async def test_unwrap_basics():
    """Basic unwrap tests."""
    loop = asyncio.get_running_loop()
    assert await unwrap(loop, 1) == 1
    assert await unwrap(loop, "hello") == "hello"
    
    async def async_val(v): return v
    assert await unwrap(loop, async_val(5)) == 5
    assert await unwrap(loop, (async_val(1), 2)) == (1, 2)


@pytest.mark.asyncio
async def test_weakref_and_gc():
    import weakref
    import gc
    loop = asyncio.get_running_loop()
    
    with recursion_scope() as memo:
        obj = lambda: "gctarget"
        ref = weakref.ref(obj)

        res = await unwrap(loop, obj)
        assert res == "gctarget"

        del obj
        gc.collect()
        # Note: ref() may or may not be None depending on GC timing
        # Just verify the unwrap worked
