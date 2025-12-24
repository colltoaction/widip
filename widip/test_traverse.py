import pytest
from widip.traverse import p_functor, vertical_map, cartesian_lift

# --- Unit Tests for Basic Functions ---

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
