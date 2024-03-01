import pathlib
import sys
from files import path_diagram
from discopy.frobenius import Id, Functor, Ty, Box


def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in map(pathlib.Path, paths):
        yield path_diagram(path)

def main_functor():
    return Functor(
        ob=lambda x: x,
        ar=lambda box: print(eval(box.name)))

diagram = Id().tensor(*argv_diagrams())
# diagram.draw()
# diagram = main_functor()(diagram)
