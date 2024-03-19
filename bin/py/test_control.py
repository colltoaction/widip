from discopy.frobenius import Box, Ty

from .control import py_control_f


const_box = Box("const", Ty("a"), Ty("a"))
pure_box = Box("pure", Ty("a"), Ty("f") @ Ty("a"))
map_box = Box("map", Ty("f") @ Ty("a"), Ty("f") @ Ty("b"))
contramap_box = Box("contramap", Ty("f") @ Ty("b"), Ty("f") @ Ty("a"))

def test_const():
    const_fun = py_control_f(const_box)
    assert const_fun("const 1") == "const 1"

def test_pure():
    pure_fun = py_control_f(pure_box)
    f, a = pure_fun("pure 1")
    assert f(a) == "pure 1"

def test_map():
    map_fun = py_control_f(map_box)
    assert map_fun(lambda x: f"mapped {x}", "1") == "mapped 1"

def test_contramap():
    contramap_fun = py_control_f(contramap_box)
    assert contramap_fun(lambda x: f"cmapped {x}", "1") == "cmapped 1"
