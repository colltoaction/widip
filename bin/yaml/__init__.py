import pathlib

from discopy.frobenius import Diagram, Box, Ty

from bin.py.lisp import lisp_f
from bin.py.files import files_f
from composing import glue_all_diagrams


def shell_main(file_names):
    # TODO cuando levanto archivos del filesystem
    # usar IO entre las llamadas.
    # solo al final hacer como Haskell corre el IO en el momento.
    # se necesita implementar !file o tags de un search path.
    file_diagrams = []
    for file_box in file_boxes(file_names):
        fd = files_f(file_box)
        file_diagrams.append(fd)
    rep_d = glue_all_diagrams(file_diagrams)
    rep_d = lisp_f(rep_d)
    rep_d = files_f(rep_d)
    return rep_d

def file_boxes(file_names):
    # TODO cuando levanto archivos del filesystem
    # usar IO entre las llamadas.
    # solo al final hacer como Haskell corre el IO en el momento.
    # se necesita implementar !file o tags de un search path.
    for file_name in file_names:
        yield Box(file_name, Ty(), Ty())