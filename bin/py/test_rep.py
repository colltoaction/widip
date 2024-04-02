from discopy.frobenius import Box, Ty, Diagram, Id, Spider

from .rep import py_rep_f


f = py_rep_f
eval_f = f(Box(
    "tag:yaml.org,2002:python/eval",
    Ty("") @ Ty("str"),
    Ty("") @ Ty(""),))

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

def test_two_params():
    assert f(Id())("y", "z") == ("y", "z")
    assert f(Id("x"))("y", "z") == ("y", "z")
    assert f(Id("x") @ Id("x"))("y", "z") == ("y", "z")
    assert f(Spider(1, 0, Ty("x")) @ Spider(1, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(0, 1, Ty("x")) @ Spider(0, 1, Ty("x")))("y", "z") == ("x", "x", "y", "z")
    assert f(Spider(2, 0, Ty("x")))("y", "z") == ()
    assert f(Spider(2, 2, Ty("x")))("y", "z") == ("y", "z", "y", "z")

def test_eval():
    assert eval_f("lambda: 2+2")() == 4
    assert eval_f("2+2") == 4
    assert eval_f("lambda x: x")("2+2") == "2+2"
