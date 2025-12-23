import pytest
from widip.thunk import thunk, unwrap


async def async_val(val):
    return val

async def async_thunk(val):
    return thunk(lambda: val)

@pytest.mark.asyncio
@pytest.mark.parametrize("input_val, expected", [
    (1, 1),
    ("hello", "hello"),
    (thunk(lambda: 42), 42),
    (thunk(lambda: thunk(lambda: 100)), 100),
    (async_val(5), 5),
    (async_val(thunk(lambda: 10)), 10),
    (thunk(lambda: async_val(20)), 20),
    ((1, 2), (1, 2)),
    ([3, 4], (3, 4)),
    ((thunk(lambda: 1), thunk(lambda: 2)), (1, 2)),
    ((async_val(1), async_val(2)), (1, 2)),
    ([async_val(1), thunk(lambda: 2)], (1, 2)),
    ((1,), (1,)),
    ([1], (1,)),
    (thunk(lambda: (1,)), (1,)),
    (async_val((1,)), (1,)),
    (thunk(lambda: (lambda n: [n, n])([1])), ((1,), (1,))),
    (thunk(lambda: (lambda it: [it, it])(iter([1, 2, 3]))), ((1, 2, 3), (1, 2, 3))),
])
async def test_unwrap(input_val, expected):
    assert await unwrap(input_val) == expected

@pytest.mark.asyncio
async def test_unwrap_self_reference():
    l = []
    l.append(l)
    res = await unwrap(l)
    assert res[0] is l