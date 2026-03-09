import pytest

from widip.computer import *
from widip.lang import *


P = ProgramTy()

def test_fig_2_7_compile_sequential_to_left_side():
    """
    Fig. 2.7 sequential equation:
    """
    A, B, C = Ty("A"), Ty("B"), Ty("C")
    F = Box("F", A, P)
    G = Box("G", B, P)
    right = Sequential(F, G)
    compiler = Compile()
    left = F @ G @ A >> P @ Eval(A, P) >> Eval(P, P)
    compiled = compiler(right)
    assert compiled == left


def test_fig_2_7_compile_parallel_to_left_side():
    """
    Fig. 2.7 parallel equation:
    right side is `Parallel(A@U, B@V)`.
    """
    A, U, B, V = Ty("A"), Ty("U"), Ty("B"), Ty("V")
    f = Box("f", A, P)
    g = Box("g", U, P)
    right = Parallel(f, g)
    compiler = Compile()
    left = (
        f @ g @ A @ U
        >> (P @ Swap(P, A) @ U)
        >> (Eval(A, P) @ Eval(U, P))
    )
    compiled = compiler(right)
    assert compiled == left


def test_eq_2_6_compile_data_is_identity():
    """Eq. 2.6: uncurrying quoted data compiles to its uncurried form (box @ Id) >> Eval."""
    f = Data("A")
    left = Id("A")
    compiler = Compile()
    compiled = compiler(f)
    assert compiled == left


def test_eq_2_5_compile_partial_is_eval():
    """Eq. 2.5: uncurrying `[]` compiles to direct evaluator on `Y @ A`."""
    A, B, Y = Ty("A"), Ty("B"), Ty("Y")
    f = Box("f", A, P)
    right = Partial(f, Y)
    right.draw(path="test_compiler.svg")
    compiler = Compile()
    compiled = compiler(right)
    compiled.draw(path="test_compiler_left.svg")
    assert compiled == Eval(P @ A @ A, P)
