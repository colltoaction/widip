from discopy.frobenius import Id, Box, Ty

from .control import control_f


const_box = Box("const", Ty("a"), Ty("a"))
pure_box = Box("pure", Ty("a"), Ty("f") @ Ty("a"))
map_box = Box("map", Ty("f") @ Ty("a"), Ty("f") @ Ty("b"))
contramap_box = Box("contramap", Ty("f") @ Ty("b"), Ty("f") @ Ty("a"))

def test_id():
    d = Id("")
    assert control_f(d) == Id("functor")

def test_const():
    d = Box("functor", Ty("a"), Ty("a"))
    assert control_f(d) == const_box

def test_pure():
    d = Box("functor", Ty("a"), Ty("f") @ Ty("a"))
    assert control_f(d) == pure_box

def test_map():
    d = Box("functor", Ty("f") @ Ty("a"), Ty("f") @ Ty("b"))
    assert control_f(d) == map_box

def test_contramap():
    d = Box("functor", Ty("f") @ Ty("b"), Ty("f") @ Ty("a"))
    assert control_f(d) == contramap_box

def test_composition():
    i = Box("inputs", Ty(), Ty("f") @ Ty("a"))
    d = i >> Box("functor", Ty("f") @ Ty("a"), Ty("f") @ Ty("b"))
    assert control_f(d) == i >> map_box
