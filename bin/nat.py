from discopy.frobenius import Id, Functor, Ty, Box, Category, Spider

from bin.py_function import PyFunction


py_nat_f = Functor(
    lambda x: x,
    lambda ar: {'0': lambda: 0, 'succ': lambda x: int(x) + 1}[ar.name],
    cod=Category(Ty, PyFunction))
