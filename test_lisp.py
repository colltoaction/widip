import pathlib
from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from lisp import lisp_functor


f = lisp_functor()

def test_empty_params():
    assert f(Id())() == ()
    assert f(Id("x"))() == ()
    assert f(Spider(0, 1, Ty("x")))() == ()
    assert f(Spider(1, 0, Ty("x")))() == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))() == ()
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))() == ()
    assert f(Spider(2, 0, Ty("x")))() == ()
    assert f(Spider(0, 2, Ty("x")))() == ()

def test_one_param():
    assert f(Id())("y") == "y"
    assert f(Id("x"))("y") == "y"
    assert f(Spider(0, 0, Ty("x")))("y") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y") == "y"
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))("y") == ()
    assert f(Spider(0, 2, Ty("x")))("y") == ("y", "y")
    assert f(Spider(2, 0, Ty("x")))("y") == ()

def test_two_params():
    assert f(Id())("y", "z") == ("y", "z")
    assert f(Id("x"))("y", "z") == ("y", "z")
    assert f(Id("x") @ Id("x"))("y", "z") == ("y", "z")
    assert f(Spider(0, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y", "z") == ("y", "z")
    assert f(Spider(0, 2, Ty("x")))("y", "z") == ("y", "z", "y", "z")

def test_eval():
    assert f(Box('eval', Ty(), Ty()))("2+2") == 4
    assert f(
        Box('eval', Ty(""), Ty("")) >>
        Box('eval', Ty(""), Ty())
        )("'2+2'") == 4

# def test_fibonacci():
#     t = path_diagram(pathlib.Path("examples/rosetta/fibonacci.yaml"))
#     assert f(t)(0) == 0
#     assert f(t)(1) == 1
#     assert f(t)(2) == 1
#     assert f(t)(3) == 3
#     assert f(t)(4) == 5
