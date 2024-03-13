import pathlib
from discopy.frobenius import Id, Box, Ty

from files import path_diagram

from .nat import nat_f

def test_zero():
    zero = Box("0", Ty(), Ty(""))
    assert nat_f(zero)() == 0

def test_two():
    two = Box("0", Ty(), Ty("")) \
        >> Box("succ", Ty(""), Ty("")) \
        >> Box("succ", Ty(""), Ty(""))
    assert nat_f(two)() == 2

def test_fibonacci():
    fibonacci = path_diagram(pathlib.Path("examples/rosetta/fibonacci.yaml"))
    # TODO after recursion
    assert nat_f(fibonacci)(2) == 5
