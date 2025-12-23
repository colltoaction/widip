import pytest
from widip.thunk import thunk, unwrap, p_functor, vertical_map, cartesian_lift


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

@pytest.mark.parametrize("data, base", [
    (1, "A"),
    ({"x": 1}, "ENV"),
    ([1, 2, 3], 0),
])
def test_p_functor(data, base):
    obj = (data, base)
    assert p_functor(obj) == base
    assert obj[0] == data

@pytest.mark.parametrize("start_data, func, expected_data", [
    (1, lambda x: x + 1, 2),
    (10, lambda x: x * 2, 20),
    ("hello", lambda x: x.upper(), "HELLO"),
])
def test_vertical_map(start_data, func, expected_data):
    base = "BASE"
    obj = (start_data, base)
    new_obj = vertical_map(obj, func)
    assert new_obj[0] == expected_data
    assert new_obj[1] == base
    assert p_functor(new_obj) == base

@pytest.mark.parametrize("start_data, new_base, lift_fn, expected_data", [
    (10, "B", lambda d, b: d + len(b), 11),
    ({"k": "v"}, "PROD", lambda d, b: {**d, "env": b}, {"k": "v", "env": "PROD"}),
])
def test_cartesian_lift(start_data, new_base, lift_fn, expected_data):
    base = "A"
    obj = (start_data, base)
    new_obj = cartesian_lift(obj, new_base, lift_fn)
    assert new_obj[1] == new_base
    assert new_obj[0] == expected_data
