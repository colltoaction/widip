from functools import partial
from itertools import repeat
import operator

from discopy import python, symmetric
from discopy.utils import tuplify as discopy_tuplify
from .lang import *


tuplify = partial(operator.call, discopy_tuplify)
partial_const = partial(next, repeat(partial))
empty_tuple = partial(next, repeat(()))
tuple_type = partial(operator.mul, (partial, ))
copy_builder = partial(operator.call, python.Function.copy)
delete_builder = partial(operator.call, python.Function.discard)

def to_py_ar(ar):
    if not ar.dom:
        return empty_tuple
    dom = tuple_type(len(ar.dom))
    if isinstance(ar, Copy):
        return copy_builder(dom)
    if isinstance(ar, Delete):
        return delete_builder(dom)
    assert not ar

to_py = symmetric.Functor(
    partial_const,
    to_py_ar,
    dom=Category(),
    cod=python.Category())
