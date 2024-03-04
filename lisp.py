from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy import python

class FrobeniusFunction(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        """"""
        return FrobeniusFunction(
            inside=lambda *_: f"{typ}",
            dom=Ty(*(n_legs_in * typ.inside)),
            cod=Ty(*(n_legs_out * typ.inside)),)

def try_read(b):
    return lambda *xs: input(b.dom.inside[0])

def try_eval(b):
    try:
        f = eval(b.name)
        return lambda *xs: f(*xs)
    except NameError:
        return lambda *_: b

def try_print(b):
    return lambda *xs: print(*xs)

def try_loop(b):
    """each is an execution cycle"""
    def loop(*xs):
        # f(*xs)
        return b.name
    return loop

requirements = {
    'read': try_read,
    'eval': try_eval,
    'print': try_print,
    'loop': try_loop,
}

def lisp_functor():
    """minimum requirements to bootstrap LISP"""
    return Functor(
        ob=lambda x: x,
        ar=lambda b: requirements.get(b.name, lambda *_: lambda: b.name)(b),
        cod=Category(Ty, FrobeniusFunction),)
