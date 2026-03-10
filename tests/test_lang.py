from functools import partial

import pytest

from widip.to_py import to_py
from widip.lang import *
from discopy import closed, python
from os import path


X, A = Ty("X"), Ty("A")

SVG_ROOT_PATH = path.join("tests", "svg")

def svg_path(filename):
    return path.join(SVG_ROOT_PATH, filename)


def test_distinguished_program_type():
    assert ProgramTy() != closed.Ty()
    assert ProgramTy() != closed.Ty("P")
    assert ProgramOb() != cat.Ob()

def test_fig_2_13():
    """Fig 2.13: {} induces the X-indexed family runAB_X"""
    G = Id()
    assert run(G, G.dom[1:], G.cod) == run(G, G.dom[:1], G.cod)

def test_fig_2_14():
    """Fig 2.14: naturality requirement for runAB"""
    G = Id()
    s = Id()
    assert run(G, G.dom[1:], G.cod) >> s == run(G >> s, G.dom[:1], G.cod)

def test_eq_2_15():
    """Eq 2.15"""
    G = Id()
    assert run(G, G.dom[1:], G.cod) == eval_f(G)

def test_fig_2_16():
    """Fig 2.16: {} == runAB_P(id)"""
    G = Id(ProgramTy())
    assert Eval(Ty(), Ty()) == run(G, Ty(), Ty())

def test_fig_7_2():
    """Eq 2.2: g = (G × A) ; {} with G : X⊸P and g : X×A→B."""
    X, A, B = Ty("X"), Ty("A"), Ty("B")
    G = Box("G", X, ProgramTy())
    g = (G @ A) >> run(G, A, B)
    assert g == (G @ A) >> Eval(A, B)
    assert g.dom == X @ A
    assert g.cod == B

###
# Python-based axiom checks
###

@pytest.mark.parametrize(["diagram_left", "diagram_right", "expected"],[
    (Copy(A) >> Copy(A) @ A, Copy(A) >> A @ Copy(A), ("s0", "s0", "s0")),
    (Id(A), Copy(A) >> Delete(A) @ A, "s0"),
    (Id(A), Copy(A) >> A @ Delete(A), "s0"),
    (Copy(A), Copy(A) >> Swap(A, A), ("s0", "s0")),
    (Id(), Copy(Ty()), ()),
    (Id(), Delete(Ty()), ()),
    ],
)
def test_cartesian_data_services(diagram_left, diagram_right, expected):
    """Eq 1.2"""
    left_f = to_py(diagram_left)
    right_f = to_py(diagram_right)
    assert len(diagram_left.dom) == len(diagram_right.dom)
    assert len(diagram_left.cod) == len(diagram_right.cod)
    inputs = tuple(f"s{i}" for i in range(len(left_f.dom)))
    with python.Function.no_type_checking:
        left = left_f(*inputs)
        assert left == expected
        assert left == right_f(*inputs)
