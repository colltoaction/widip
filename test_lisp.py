import pathlib
from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from files import path_diagram
from lisp import lisp_functor


f = lisp_functor()

def test_empty_params():
    assert f(Id())() == ()
    assert f(Id("x"))() == ()
    assert f(Spider(0, 0, Ty("x")))() == ()
    assert f(Spider(0, 1, Ty("x")))() == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))() == ()
    assert f(Spider(0, 2, Ty("x")))() == ()

def test_one_param():
    assert f(Id())("y") == "y"
    assert f(Id("x"))("y") == "y"
    assert f(Spider(1, 0, Ty("x")))("y") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y") == "y"

def test_two_params():
    assert f(Id())("y", "z") == ("y", "z")
    assert f(Id("x"))("y", "z") == ("y", "z")
    assert f(Id("x") @ Id("x"))("y", "z") == ("y", "z")
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y", "z") == ("y", "z")
    assert f(Spider(2, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(2, 2, Ty("x")))("y", "z") == ("y", "z", "y", "z")

def test_eval():
    assert f(Box('eval', Ty(), Ty()))("2+2") == 4
    assert f(
        Box('eval', Ty(""), Ty("")) >>
        Box('eval', Ty(""), Ty())
        )("'2+2'") == 4

def test_bool_and():
    t = Spider(0, 1, Ty("true"))
    d = path_diagram(pathlib.Path("src/yaml/data/bool/and.yaml"))
    
    assert f(d)(0) == 1
    assert f(d)(1) == 3
    assert f(d)(2) == 5
    assert f(d)(3) == 7
    assert f(d)(4) == 9
