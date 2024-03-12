from discopy.frobenius import Id, Box, Ty

from .nat import nat_f

def test_nat_zero():
    zero = Box("0", Ty(), Ty(""))
    assert nat_f(zero)() == 0

def test_nat_two():
    two = Box("0", Ty(), Ty("")) \
        >> Box("succ", Ty(""), Ty("")) \
        >> Box("succ", Ty(""), Ty(""))
    assert nat_f(two)() == 2
