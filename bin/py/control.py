from .rep import py_functor


py_control_f = py_functor(
    lambda ar: {
        'const': lambda *xs: xs[0],
        'map': lambda *xs: xs[0](xs[1]),
        'pure': lambda *xs: (lambda x: x, xs[0]),
        'contramap': lambda *xs: xs[0](xs[1]),}[ar.name],)
