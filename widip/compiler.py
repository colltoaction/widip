from collections.abc import Iterator
from discopy import closed

def force(x):
    while callable(x):
        x = x()
    if isinstance(x, (Iterator, tuple, list)):
        # Recursively force items in iterator or sequence
        x = tuple(map(force, x))
    
    # "untuplify" logic: unwrap singleton tuple/list
    if isinstance(x, (tuple, list)) and len(x) == 1:
        return x[0]
    return x

SHELL_COMPILER = closed.Functor(
    lambda ob: ob,
    lambda ar: {
        # "ls": ar.curry().uncurry()
    }.get(ar.name, ar),)
    # TODO remove .inside[0] workaround
    # lambda ar: ar)


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
