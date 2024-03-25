from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from bin.py.shell import shell_f, eval_box
from bin.py import py_lisp_f


f = shell_f >> py_lisp_f

def test_empty_params():
    assert f(Id())() == ()
    assert f(Id("x"))() == ()
    assert f(Spider(0, 0, Ty("x")))() == ()
    assert f(Spider(0, 1, Ty("x")))() == ("io",)
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))() == ("io", "io")
    assert f(Spider(0, 2, Ty("x")))() == ("io", "io")

def test_one_param():
    assert f(Id())("y") == "y"
    assert f(Id("x"))("y") == "y"
    assert f(Spider(1, 0, Ty("x")))("y") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y") == ("io", "io", "y")

def test_two_params():
    assert f(Id())("y", "z") == ("y", "z")
    assert f(Id("x"))("y", "z") == ("y", "z")
    assert f(Id("x") @ Id("x"))("y", "z") == ("y", "z")
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y", "z") == ("io", "io", "y", "z")
    assert f(Spider(2, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(2, 2, Ty("x")))("y", "z") == ("y", "z", "y", "z")

def test_eval():
    assert f(eval_box)("lambda: 2+2")() == 4
    assert f(eval_box)("2+2") == 4
    assert f(eval_box)("lambda x: x")("2+2") == "2+2"
