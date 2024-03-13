import pathlib
from discopy.frobenius import Id, Box, Ty

from files import path_diagram

from .bool import bool_f

def test_true_false():
    t = Box("true", Ty(), Ty(""))
    f = Box("false", Ty(), Ty(""))
    assert bool_f(t)() == True
    assert bool_f(f)() == False

def test_bool_and():
    # TODO using a truth table diagram
    bool_and = path_diagram(pathlib.Path("src/data/bool/and.yaml"))
    assert bool_f(bool_and)(True, False) == (True, False)
