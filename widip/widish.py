from functools import partial
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        return tuplify(params[0] if params else ar.dom.name if ar.dom else "")
    def run_native_subprocess_map(*params):
        res = tuple((x(p) for x, p in zip(b, params)))
        return untuplify(res)
    def run_native_subprocess_seq(*params):
        res = tuplify(b[1](b[0](*params)))
        return res
    def run_native_subprocess_inside(*params):
        try:
            io_result = run(
                b,
                check=True, text=True, capture_output=True,
                # input=params,
                )
            res = io_result.stdout.rstrip("\n")
            return tuplify(res)
        except CalledProcessError as e:
            return e.stderr
    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if ar.name == "g":
        res = run_native_subprocess_inside(*b)
        return res
    if ar.name == "G":
        return run_native_subprocess_constant

SHELL_RUNNER = Functor(
    lambda ob: str,
    lambda ar: partial(run_native_subprocess, ar),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    # lambda ob: Ty() if ob == Ty("io") else ob,
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
