from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy import python

class FrobeniusFunction(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        """"""
        def inside(*xs):
            assert len(xs) == n_legs_in
            if n_legs_in == 0:
                xs = tuple(x.name for x in typ)
            return n_legs_out * xs
        return FrobeniusFunction(
            inside=inside,
            dom=Ty(*(n_legs_in * typ.inside)),
            cod=Ty(*(n_legs_out * typ.inside)),)

def try_read(b):
    return lambda *xs: input(*xs)

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
    print("loop")
    def loop(*xs):
        return b.name
    return loop

requirements = {
    'read': try_read,
    'eval': try_eval,
    'print': try_print,
    'loop': try_loop,
    # TODO use nat module
    '0': lambda ar: lambda: 0,
    'succ': lambda ar: lambda x: x+1,
    'plus': lambda ar: lambda *xs: sum(xs),
}

def lisp_ar(b):
    r = requirements.get(b.name, None)
    # TODO xs no es siempre, por ejemplo si
    # viene de un closed cable.
    # dependiendo del box cambia el lambda
    # no es siempre id
    return r(b) if r else lambda *xs: xs

def lisp_functor():
    """minimum requirements to bootstrap LISP"""
    return Functor(
        ob=lambda x: x,
        ar=lisp_ar,
        cod=Category(Ty, FrobeniusFunction),)
