from .rep import py_functor


py_bool_f = py_functor(
    lambda ar: {
        'true': lambda: True,
        'false': lambda: False,
        'and': lambda *xs: xs[0] and xs[1],}[ar.name],)
