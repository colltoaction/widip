from discopy.frobenius import Id, Box, Ty, Functor, Category

from .nat import py_nat_f


def test_zero():
    zero = Box("0", Ty(), Ty("nat"))
    assert py_nat_f(zero)() == 0

def test_two():
    two = Box("0", Ty(), Ty("nat")) \
        >> Box("succ", Ty("nat"), Ty("nat")) \
        >> Box("succ", Ty("nat"), Ty("nat"))
    assert py_nat_f(two)() == 2
