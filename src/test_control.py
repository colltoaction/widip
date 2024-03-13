from discopy.frobenius import Id, Box, Ty, Functor

from .control import control_f


def test_const():
    d = Box("functor", Ty("a"), Ty("a"))
    const_fun = control_f(d)
    assert const_fun("const 1") == "const 1"

def test_pure():
    d = Box("functor", Ty("a"), Ty("f") @ Ty("a"))
    pure_fun = control_f(d)
    f, a = pure_fun("pure 1")
    assert f(a) == "pure 1"

def test_map():
    d = Box("functor", Ty("f") @ Ty("a"), Ty("f") @ Ty("b"))
    map_fun = control_f(d)
    assert map_fun(lambda x: f"mapped {x}", "1") == "mapped 1"

def test_contramap():
    d = Box("functor", Ty("f") @ Ty("b"), Ty("f") @ Ty("a"))
    contramap_fun = control_f(d)
    assert contramap_fun(lambda x: f"cmapped {x}", "1") == "cmapped 1"
