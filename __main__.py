import pathlib
import sys
from files import file_functor, compose_graph_file
from discopy.frobenius import Id, Functor, Ty, Box


def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in paths:
        yield compose_graph_file(path)

def main_functor():
    return Functor(
        ob=lambda x: x,
        ar=lambda box: print(eval(box.name)))

diagram = Id().tensor(*argv_diagrams())
diagram = file_functor()(diagram)
diagram.draw()
# diagram = main_functor()(diagram)
# diagram.draw()
