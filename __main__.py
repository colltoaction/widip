import pathlib
import sys
from files import path_diagram
from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy import python


class FrobeniusFunction(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        """"""
        return FrobeniusFunction(
            inside=lambda *_: f"{typ}",
            dom=Ty(*(n_legs_in * typ.inside)),
            cod=Ty(*(n_legs_out * typ.inside)),)

def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in map(pathlib.Path, paths):
        yield path_diagram(path)

def main_functor():
    return Functor(
        ob=lambda x: x,
        ar=lambda b: lambda *xs: eval(b.name)(*(xs or b.dom.inside)),
        cod=Category(Ty, FrobeniusFunction),)

while True:
    ast_diagram = Id().tensor(*argv_diagrams())
    # TODO gifs are created but should choose
    ast_diagram = main_functor()(ast_diagram)()
