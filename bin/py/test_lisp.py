from .lisp import lisp_f
from files import file_diagram

lisp_d = file_diagram(open("bin/yaml/lisp.yaml"))
py_lisp_d = file_diagram(open("bin/py/lisp.yaml"))


def test_to_py_lisp():
    d = lisp_f(lisp_d)
    assert d == py_lisp_d
