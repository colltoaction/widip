"""
A Python-based LISP dialect with tags for REP:
* !!python/input
* !!python/eval
* !!python/print
"""
from discopy.frobenius import Ty, Functor, Category
from discopy import python


class PyFunction(python.Function):
    """Adds Frobenius to the Python category"""
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        def inside(*xs):
            assert len(xs) == n_legs_in
            if n_legs_in == 0:
                xs = tuple(x.name for x in typ)
            return n_legs_out * xs
        return PyFunction(
            inside=inside,
            dom=Ty(*(n_legs_in * typ.inside)),
            cod=Ty(*(n_legs_out * typ.inside)),)


def input_ar():
    return input("- ")

def eval_ar(src):
    return eval(src)

def print_ar(*xs):
    # TODO handle !print Hello world!
    # dom=cod="hw", so we need to use the
    print(*xs)

def py_lisp_ar(ar):
    match ar.name:
        case 'tag:yaml.org,2002:python/input': return input_ar
        case 'tag:yaml.org,2002:python/eval': return eval_ar
        # TODO handle !!python/print Hello world!
        # where dom is turned into input and and cod is discarded.
        case 'tag:yaml.org,2002:python/print': return lambda *_: print(ar.dom) or (None, )
        case _: return lambda *x: x

def py_functor(ar):
    return Functor(
        lambda x: x,
        ar,
        cod=Category(Ty, PyFunction))

py_lisp_f = py_functor(py_lisp_ar)
