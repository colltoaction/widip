import pathlib
import sys
from discopy.frobenius import Id

from composing import box_expansion_functor
from files import path_diagram
from lisp import lisp_functor

def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in map(pathlib.Path, paths):
        yield path_diagram(path)

ds = argv_diagrams()
ast_diagram = Id().tensor(*ds)
f = lisp_functor()(ast_diagram)
# ast_diagram.draw()
# while True:
#     f()
