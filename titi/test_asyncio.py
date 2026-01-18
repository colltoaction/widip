
import pytest
import asyncio
from computer.asyncio import unwrap, pipe_async, tensor_async

# --- Fixtures ---

@pytest.fixture
def loop():
    return asyncio.get_event_loop()

# --- Unwrap Tests ---

@pytest.mark.asyncio
@pytest.mark.parametrize("val, expected", [
    (1, 1),
    ("hello", "hello"),
    (None, None),
    ((1, 2), (1, 2)),
    ([1, 2], [1, 2]), # Note: unwrap currently returns tuples for lists usually? Let's see. implementation says: if list/tuple -> returns tuple.
])
async def test_unwrap_literals(loop, val, expected):
    """Test unwrapping simple literals."""
    res = await unwrap(val, loop)
    # Lists are converted to tuples by unwrap_step for recursion gathering
    if isinstance(val, list):
        assert res == tuple(val)
    else:
        assert res == expected

@pytest.mark.asyncio
async def test_unwrap_async_val(loop):
    async def async_val(v): return v
    assert await unwrap(async_val(5), loop) == 5

@pytest.mark.asyncio
async def test_unwrap_nested_async(loop):
    async def foo(): return 1
    async def bar(): return foo()
    assert await unwrap(bar, loop) == 1

@pytest.mark.asyncio
async def test_unwrap_callable(loop):
    def simple(): return 123
    assert await unwrap(simple, loop) == 123

# --- Composition Tests ---

@pytest.mark.asyncio
async def test_pipe_async(loop):
    async def f1(x): return x + 1
    async def f2(x): return x * 2
    
    # f1(3) -> 4, f2(4) -> 8. pipe_async(f1, f2, loop, 3)
    # The implementation of pipe_async takes (left_fn, right_fn, loop, *args)
    res = await pipe_async(f1, f2, loop, 3)
    assert res == 8

@pytest.mark.asyncio
async def test_tensor_async(loop):
    async def f1(x): return x + 1
    async def f2(x): return x * 2
    
    # left_dom usually needed for splitting args. implementation: n=len(left_dom)
    # tensor_async(left_fn, left_dom, right_fn, loop, *args)
    # f1 takes 1 arg, f2 takes 1 arg. args=(3, 5) -> f1(3)=4, f2(5)=10 -> (4, 10)
    res = await tensor_async(f1, [object], f2, loop, 3, 5)
    assert res == (4, 10)
