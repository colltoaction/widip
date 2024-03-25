import pathlib

from discopy.frobenius import Diagram, Box, Ty, Id

from bin.py.lisp import lisp_f
from composing import glue_all_diagrams


def shell_main(file_names):
    # TODO cuando levanto archivos del filesystem
    # usar IO entre las llamadas.
    # solo al final hacer como Haskell corre el IO en el momento.
    # se necesita implementar !file o tags de un search path.
    rep_d = Id().tensor(*(
        file_box
        for file_box in file_boxes(file_names)))
    rep_d = lisp_f(rep_d)
    return rep_d

def file_boxes(file_names):
    # TODO cuando levanto archivos del filesystem
    # usar IO entre las llamadas.
    # solo al final hacer como Haskell corre el IO en el momento.
    # se necesita implementar !file o tags de un search path.
    for file_name in file_names:
        yield lisp_f(Box('read', Ty(file_name), Ty()))