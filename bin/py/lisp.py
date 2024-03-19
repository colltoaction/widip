"""Convert YAML-based to Python-based LISP syntax"""
from discopy import python
from discopy.frobenius import Functor, Box, Ty, Category, Id, Spider
from discopy.cat import Arrow

from bin.py import PyFunction

def read_ar(ast: Box) -> Arrow:
    """takes a Diagram ast"""
    return Box(
                "tag:yaml.org,2002:python/input",
                Ty("io"),
                Ty("io") @ Ty("str"),)

def eval_ar(ar: Box) -> Arrow:
    # TODO do eval?
    return Id("io") @ Box(
        "tag:yaml.org,2002:python/eval",
        Ty("str"),
        Ty(""),)

def print_ar(ar: Box) -> Arrow:
    return Box(
        "tag:yaml.org,2002:python/print",
        Ty("io") @ Ty(""),
        Ty("io"),)

def lisp_ar(ar: Box) -> Arrow:
    match ar.name:
        case 'read': return read_ar(ar)
        case 'eval': return eval_ar(ar)
        case 'print': return print_ar(ar)
        case _: assert False

lisp_f = Functor(
    {Ty(""): Ty("io") @ Ty(""),
     Ty("io"): Ty("io")},
    lisp_ar)
