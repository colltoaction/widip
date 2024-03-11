import pathlib
from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from files import path_diagram
from lisp import lisp_functor


f = lisp_functor()

def test_empty_params():
    assert f(Id())() == ()
    assert f(Id("x"))() == ()
    assert f(Spider(0, 0, Ty("x")))() == ()
    assert f(Spider(0, 1, Ty("x")))() == ("x",)
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))() == ("x", "x")
    assert f(Spider(0, 2, Ty("x")))() == ("x", "x")

def test_one_param():
    assert f(Id())("y") == "y"
    assert f(Id("x"))("y") == "y"
    assert f(Spider(1, 0, Ty("x")))("y") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y") == ("x", "x", "y")

def test_two_params():
    assert f(Id())("y", "z") == ("y", "z")
    assert f(Id("x"))("y", "z") == ("y", "z")
    assert f(Id("x") @ Id("x"))("y", "z") == ("y", "z")
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y", "z") == ("x", "x", "y", "z")
    assert f(Spider(2, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(2, 2, Ty("x")))("y", "z") == ("y", "z", "y", "z")

def test_eval():
    assert f(Box('eval', Ty(), Ty()))("2+2") == 4
    assert f(
        Box('eval', Ty(""), Ty("")) >>
        Box('eval', Ty(""), Ty())
        )("'2+2'") == 4
