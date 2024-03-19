from discopy.frobenius import Id, Box, Ty, Functor, Category

from .nat import py_nat_f

plus_box = Box("plus", Ty("nat") @ Ty("nat"), Ty("nat"))
zero = Box("0", Ty(), Ty("nat"))
two = zero \
    >> Box("succ", Ty("nat"), Ty("nat")) \
    >> Box("succ", Ty("nat"), Ty("nat"))

def test_zero():
    assert py_nat_f(zero)() == 0

def test_two():
    assert py_nat_f(two)() == 2

def test_plus():
    four = two @ two >> plus_box
    assert py_nat_f(four)() == 4
