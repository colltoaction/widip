from discopy.frobenius import Box, Ty

from .bool import py_bool_f


t = Box("true", Ty(), Ty(""))
f = Box("false", Ty(), Ty(""))
a = Box("and", Ty("") @ Ty(""), Ty(""))

def test_true_false():
    assert py_bool_f(t)() == True
    assert py_bool_f(f)() == False

def test_bool_and():
    assert py_bool_f(t @ t >> a)() == True
    assert py_bool_f(t @ f >> a)() == False
    assert py_bool_f(f @ t >> a)() == False
    assert py_bool_f(f @ f >> a)() == False
