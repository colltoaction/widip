"""Convert YAML-based to Python-based LISP syntax"""
from discopy.frobenius import Functor, Box, Ty, Category, Id, Spider, Diagram
from discopy.cat import Arrow


input_box = Box(
    "tag:yaml.org,2002:python/input",
    Ty(""),
    Ty("") @ Ty("str"),)
eval_box = Box(
    "tag:yaml.org,2002:python/eval",
    Ty("") @ Ty("str"),
    Ty("") @ Ty(""),)


def read_ar(ar):
    return Box(f"file://./{ar.dom}", Ty(""), Ty(""))

def eval_ar(ar: Box) -> Arrow:
    s = Id().tensor(*(Spider(0, 1, x) for x in ar.dom))
    return s >> Box(
        "tag:yaml.org,2002:python/eval",
        ar.dom,
        Ty(""),)

def print_ar(ar: Box) -> Arrow:
    """Plugs the box name constant into the native Python print"""
    # TODO 
    # adapted = adapt_to_interface(path_d, ar)
    # adapted.draw()
    s = Id("") @ Id().tensor(*(Spider(0, 1, x) for x in ar.dom))
    print_box = s >> Box(
        "tag:yaml.org,2002:python/print",
        Ty("") @ ar.dom,
        Ty(""),)
    return print_box

def shell_ar(ar: Box) -> Arrow:
    match ar.name:
        # TODO don't immediately read and use files_f instead
        case 'read': return files_ar(ar)
        case 'eval': return eval_ar(ar)
        case 'print': return print_ar(ar)
        case _: return ar

shell_f = Functor(
    lambda x: Ty(""),
    shell_ar)
