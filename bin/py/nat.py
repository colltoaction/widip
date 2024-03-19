from . import py_functor


py_nat_f = py_functor(
    lambda ar: {
        '0': lambda: 0,
        'succ': lambda x: int(x) + 1,
        'plus': lambda *xs: sum(xs),}[ar.name],)
