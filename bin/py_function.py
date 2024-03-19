from typing import Callable
from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider
from discopy.cat import Arrow
from discopy import python

class PyFunction(python.Function):
    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: Ty):
        """"""
        def inside(*xs):
            assert len(xs) == n_legs_in
            if n_legs_in == 0:
                xs = tuple(x.name for x in typ)
            return n_legs_out * xs
        return PyFunction(
            inside=inside,
            dom=Ty(*(n_legs_in * typ.inside)),
            cod=Ty(*(n_legs_out * typ.inside)),)


def box_fun_functor(box_fun: Callable[[Box], Arrow]) -> Functor:
    return Functor(
        ob=lambda x: x,
        ar=box_fun,
        cod=Category(Ty, PyFunction),)