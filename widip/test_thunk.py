import pytest
from widip.thunk import thunk, unwrap, thunk_map, thunk_reduce


async def async_val(val):
    return val

def clean_val(val):
    return val

@pytest.mark.asyncio
@pytest.mark.parametrize("input_val, expected", [
    # Basic values
    (1, 1),
    ("hello", "hello"),
    (None, None),

    # Thunks
    (thunk(lambda: 42), 42),
    (thunk(lambda: thunk(lambda: 100)), 100),
    (thunk(clean_val, 10), 10),

    # Async
    (async_val(5), 5),
    (async_val(thunk(lambda: 10)), 10),
    (thunk(lambda: async_val(20)), 20),

    # Structures (Lists/Tuples mapped to Tuples recursively)
    ((1, 2), (1, 2)),
    ([3, 4], (3, 4)),
    ((thunk(lambda: 1), thunk(lambda: 2)), (1, 2)),
    ((async_val(1), async_val(2)), (1, 2)),
    ([async_val(1), thunk(lambda: 2)], (1, 2)),

    # Single element tuples/lists
    ((1,), (1,)),
    ([1], (1,)),
    (thunk(lambda: (1,)), (1,)),
    (async_val((1,)), (1,)),

    # Recursive/Shared structures
    (thunk(lambda: (lambda n: [n, n])([1])), ((1,), (1,))),
    (thunk(lambda: (lambda it: [it, it])(iter([1, 2, 3]))), ((1, 2, 3), (1, 2, 3))),
])
async def test_thunk_cases(input_val, expected):
    """Parametrized test covering various value types, thunks, asyncs, and collections."""
    assert await unwrap(input_val) == expected

@pytest.mark.asyncio
async def test_complex_thunk_pipeline():
    # Stage 1: Inputs
    inputs = (17,)

    # Stage 2: Map (Double)
    def double(x): return (x * 2,)
    async def async_double(x): return (x * 2,)

    funcs_stage_2 = [thunk(double), thunk(async_double)]
    stage_2_result = await thunk_map(funcs_stage_2, *inputs)
    # ((34,), (34,)) -> flattened (34, 34)
    assert stage_2_result == (34, 34)

    # Stage 3: Reduce (Sum)
    # f1(acc) -> f2(acc) ...
    def sum_vals(x, y): return (x + y,)
    def square(x): return (x * x,)

    funcs_stage_3 = [sum_vals, thunk(square)]
    stage_3_result = await thunk_reduce(funcs_stage_3, *stage_2_result)
    # sum_vals(34, 34) -> (68,)
    # square(68) -> (4624,)
    assert stage_3_result == (4624,)

@pytest.mark.asyncio
async def test_nested_thunks_pipeline():
    # Create a lazy pipeline that isn't evaluated until unwrap.
    t1 = thunk(lambda: (19,))

    async def add_one(x):
        val = await unwrap(x)
        return (val[0] + 1,)

    async def async_double_tuple(x):
         val = await unwrap(x)
         return (val[0] * 2,)

    t2 = thunk(add_one, t1)
    t3 = thunk(async_double_tuple, t2)
    res = await unwrap(t3)
    # 19 -> 20 -> 40
    assert res == (40,)

