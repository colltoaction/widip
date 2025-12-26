from discopy import closed
from .computer import Data, Sequential, Concurrent, Computation


class ShellFunctor(closed.Functor):
    def __init__(self):
        super().__init__(
            lambda ob: ob,
            lambda ar: {
                # "ls": ar.curry().uncurry()
            }.get(ar.name, ar),
            dom=Computation,
            cod=Computation
        )

SHELL_COMPILER = ShellFunctor()


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
