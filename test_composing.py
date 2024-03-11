from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from composing import expand_name_functor


name = "expansion"
name_ty = Ty(name)
f = expand_name_functor(name)

def test_expansion():
    x, y = Ty("x"), Ty("y")
    box = Box(name, x @ Ty("") @ y, y)
    # TODO id should be Id(name)
    id = Box(name, name_ty, name_ty)
    assert f(box) == \
            Box("x", x, name_ty) @ id @ Box("y", y, name_ty) \
            >> Spider(3, 1, name_ty) \
            >> Box("y", name_ty, y)
