"""Convert YAML-based to Python-based LISP syntax"""
from discopy.frobenius import Functor, Box, Ty, Category, Id, Spider, Diagram
from discopy.cat import Arrow


def read_ar(ar):
        # TODO this doesn't always work
    if ar.dom == Ty(""):
        return Id("")
    ar2 = Box(f"file://./{ar.dom}", Ty(""), Ty(""))
    # ar2 = adapt_to_interface(ar2, ar)
    return ar2

def eval_ar(ar: Box) -> Arrow:
    s = Id().tensor(*(Spider(0, 1, x) for x in ar.dom))
    ar2 = s >> Box(
        "tag:yaml.org,2002:python/eval",
        ar.dom,
        Ty(""),)
    return ar2

def print_ar(ar: Box) -> Arrow:
    print_box = Box(
        "tag:yaml.org,2002:python/print",
        ar.dom,
        Ty(),)
    return print_box

def shell_ar(ar: Box) -> Arrow:
    ar2 = ar
    match ar.name:
        case 'read': ar2 = read_ar(ar)
        case 'eval': ar2 = eval_ar(ar)
        case 'print': ar2 = print_ar(ar)
    return ar2

# TODO IOs don't compose
shell_f = Functor(
    # TODO sometimes return x sometimes io
    lambda x: x if x.name != "" else Ty(),
    # lambda x: x,
    shell_ar,)
