from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy import python

class FrobeniusFunction(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        """"""
        return FrobeniusFunction(
            # TODO handle xs
            inside=lambda *xs: n_legs_out * xs,
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
    # TODO wow this works
    # '0': lambda ar: lambda: 0,
    # 'succ': lambda ar: lambda x: x+1,
    'read': try_read,
    'eval': try_eval,
    'print': try_print,
    'loop': try_loop,
}

def lisp_ar(b):
    r = requirements.get(b.name, None)
    return r(b) if r else lambda *xs: xs

def lisp_functor():
    """minimum requirements to bootstrap LISP"""
    return Functor(
        ob=lambda x: x,
        ar=lisp_ar,
        cod=Category(Ty, FrobeniusFunction),)
