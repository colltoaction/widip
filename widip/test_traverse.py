import pytest
from widip.traverse import get_base, get_fiber, vertical_map, cartesian_lift

@pytest.mark.parametrize("data, base", [
    (1, "A"),
    ({"x": 1}, "ENV"),
    ([1, 2, 3], 0),
])
def test_get_base(data, base):
    obj = (data, base)
    assert get_base(obj) == base
    assert get_fiber(obj) == data

@pytest.mark.parametrize("data, base", [
    (1, "A"),
    ({"x": 1}, "ENV"),
    ([1, 2, 3], 0),
])
def test_get_fiber(data, base):
    obj = (data, base)
    assert get_fiber(obj) == data
    assert get_base(obj) == base

@pytest.mark.parametrize("start_data, func, expected_data", [
    (1, lambda x: x + 1, 2),
    (10, lambda x: x * 2, 20),
    ("hello", lambda x: x.upper(), "HELLO"),
])
def test_vertical_map(start_data, func, expected_data):
    base = "BASE"
    obj = (start_data, base)
    new_obj = vertical_map(obj, func)
    assert get_fiber(new_obj) == expected_data
    assert get_base(new_obj) == base
    assert get_base(new_obj) == base

@pytest.mark.parametrize("start_data, new_base, lift_fn, expected_data", [
    (10, "B", lambda d, b: d + len(b), 11),
    ({"k": "v"}, "PROD", lambda d, b: {**d, "env": b}, {"k": "v", "env": "PROD"}),
])
def test_cartesian_lift(start_data, new_base, lift_fn, expected_data):
    base = "A"
    obj = (start_data, base)
    new_obj = cartesian_lift(obj, new_base, lift_fn)
    assert get_base(new_obj) == new_base
    assert get_fiber(new_obj) == expected_data
