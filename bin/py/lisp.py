"""Convert YAML-based to Python-based LISP syntax"""
from discopy.frobenius import Functor, Box, Ty, Category, Id, Spider
from discopy.cat import Arrow


input_box = Box(
    "tag:yaml.org,2002:python/input",
    Ty("io"),
    Ty("io") @ Ty("str"),)
eval_box = Box(
    "tag:yaml.org,2002:python/eval",
    Ty("io") @ Ty("str"),
    Ty("io") @ Ty(""),)


def read_ar(ast: Box) -> Arrow:
    """takes a Diagram ast"""
    return input_box

def eval_ar(ar: Box) -> Arrow:
    # TODO do eval?
    return eval_box

def print_ar(ar: Box) -> Arrow:
    print_box = Box(
        "tag:yaml.org,2002:python/print",
        Ty("io") @ Ty(""),
        Ty("io"),)
    return print_box

def lisp_ar(ar: Box) -> Arrow:
    match ar.name:
        case 'read': return read_ar(ar)
        case 'eval': return eval_ar(ar)
        case 'print': return print_ar(ar)
        case _: return ar

lisp_f = Functor(
    lambda x: Ty("io"),
    lisp_ar)
