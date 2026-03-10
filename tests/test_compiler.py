import pytest

from widip.computer import *
from widip.lang import *
from os import path

SVG_ROOT_PATH = path.join("tests", "svg")

def svg_path(basename):
    return path.join(SVG_ROOT_PATH, basename)

P = ProgramTy()

@pytest.fixture(autouse=True)
def after_each_test(request):
    yield
    test_name = request.node.name

    data = getattr(request.node, "draw_objects", None)
    if not data:
        raise AttributeError(f"test {test_name} did not set draw_objects (left, right) attribute for drawing")
        
    left, right = data
    
    left.draw(path=svg_path(f"{test_name}_left.svg"))
    right.draw(path=svg_path(f"{test_name}_right.svg"))

def test_fig_2_7_compile_sequential_to_left_side(request):
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
    request.node.draw_objects = (left, right)



def test_fig_2_7_compile_parallel_to_left_side(request):
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
    request.node.draw_objects = (left, right)

def test_eq_2_6_compile_data_is_identity(request):
    """Eq. 2.6: uncurrying quoted data compiles to its uncurried form (box @ Id) >> Eval."""
    f = Data("A")
    left = Id("A")
    compiler = Compile()
    compiled = compiler(f)
    assert compiled == left
    right = f
    request.node.draw_objects = (left, right)


def test_eq_2_5_compile_partial_is_eval(request):
    """Eq. 2.5: uncurrying `[]` compiles to direct evaluator on `Y @ A`."""
    A, B, Y = Ty("A"), Ty("B"), Ty("Y")
    f = Box("f", A, P)
    right = Partial(f, Y)
    compiler = Compile()
    compiled = compiler(right)
    left = Eval(P @ A @ A, P)
    assert compiled == left
    request.node.draw_objects = (left, right)

