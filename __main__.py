import src
import pathlib
import sys
from discopy.frobenius import Id, Box, Ty

from files import path_diagram
from bin.lisp import lisp_functor

def argv_diagrams():
    paths = iter(sys.argv[1:])
    for path in map(pathlib.Path, paths):
        yield path_diagram(path)


f = lisp_functor()
while True:
    ds = Id()
    for d in argv_diagrams():
        # print(d)
        ds = ds @ d
        f(d)()
