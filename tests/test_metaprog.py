import pytest

from widip.computer import *
from widip.metaprog import *
from os import path


# TODO deduplicate with SVG write logic from test_lang.py
SVG_ROOT_PATH = path.join("tests", "svg")

def svg_path(basename):
    return path.join(SVG_ROOT_PATH, basename)


@pytest.fixture(autouse=True)
def after_each_test(request):
    yield
    test_name = request.node.name

    data = getattr(request.node, "draw_objects", None)
    if not data:
        raise AttributeError(f"test {test_name} did not set draw_objects (left, right) attribute for drawing")
        
    comp, prog, mprog = data
    
    comp.draw(path=svg_path(f"{test_name}_comp.svg"))
    prog.draw(path=svg_path(f"{test_name}_prog.svg"))
    mprog.draw(path=svg_path(f"{test_name}_mprog.svg"))

def test_fig_6_1_program_and_metaprogram(request):
    """
    Fig. 6.1 program and metaprogram
    """
    A, B, X = Ty("A"), Ty("B"), Ty("X")
    comp = Computation("f", X, A, B)
    prog = Program(comp)
    mprog = Metaprogram(prog)
    right = MetaprogramFunctor()(mprog)
    assert right == prog
    right = ProgramFunctor()(right)
    assert right == comp
    request.node.draw_objects = (comp, prog, mprog)
