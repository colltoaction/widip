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


def input_ar(prompt):
    return input(prompt)

def eval_ar(src):
    # TODO catch and use io
    return eval(src)

def print_ar(*xs):
    print(*xs)

# TODO read box with filename
# is a commonly used pattern.
# we can load the python code into an eval.

# we treat files from the filesystem and argv especially.

def py_rep_ar(ar):
    match ar.name:
        case 'tag:yaml.org,2002:python/input': return input_ar
        case 'tag:yaml.org,2002:python/eval': return eval_ar
        case 'tag:yaml.org,2002:python/print': return print_ar
        case _: return lambda *x: x

def py_functor(ar):
    return Functor(
        lambda x: x,
        ar,
        cod=Category(Ty, PyFunction))

py_rep_f = py_functor(py_rep_ar)
