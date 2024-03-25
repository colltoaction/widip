"""Convert YAML-based to Python-based LISP syntax"""
from discopy.frobenius import Functor, Box, Ty, Category, Id, Spider
from discopy.cat import Arrow

from bin.py.files import files_ar


input_box = Box(
    "tag:yaml.org,2002:python/input",
    Ty("io"),
    Ty("io") @ Ty("str"),)
eval_box = Box(
    "tag:yaml.org,2002:python/eval",
    Ty("io") @ Ty("str"),
    Ty("io") @ Ty(""),)


def eval_ar(ar: Box) -> Arrow:
    s = Id().tensor(*(Spider(0, 1, x) for x in ar.dom))
    return s >> Box(
        "tag:yaml.org,2002:python/eval",
        ar.dom,
        Ty("io"),)

def print_ar(ar: Box) -> Arrow:
    """Plugs the box name constant into the native Python print"""
    s = Id("io") @ Id().tensor(*(Spider(0, 1, x) for x in ar.dom))
    print_box = s >> Box(
        "tag:yaml.org,2002:python/print",
        Ty("io") @ ar.dom,
        Ty("io"),)
    return print_box

def lisp_ar(ar: Box) -> Arrow:
    match ar.name:
        case 'read': return files_ar(ar)
        case 'eval': return eval_ar(ar)
        case 'print': return print_ar(ar)
        case _: return ar

lisp_f = Functor(
    lambda x: Ty("io"),
    lisp_ar)
