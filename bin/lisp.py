import pathlib
from files import file_diagram, read_diagram_st, write_diagram
from discopy.frobenius import Functor, Box, Ty, Category

from .py_function import PyFunction


def input_ar():
    return input("- ")

def eval_ar(xs):
    # TODO try
    return eval(xs)

def print_ar(*xs):
    print(*xs)

def rep_ar(ar) -> PyFunction:
    match ar.name:
        case 'tag:yaml.org,2002:python/input': return input_ar
        case 'tag:yaml.org,2002:python/eval': return eval_ar
        case 'tag:yaml.org,2002:python/print': return print_ar
        case _: return lambda ast: ast

def rep():
    """A Python-based LISP dialect"""
    rep_d = file_diagram(pathlib.Path("bin/lisp.yaml"))
    py_lisp_f(rep_d)()

py_lisp_f = Functor(
    lambda ob: ob,
    rep_ar,
    cod=Category(Ty, PyFunction))
