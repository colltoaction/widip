from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")


class IO(python.Function):
    """ IO class to handle shell execution logic """
    @staticmethod
    def runner(cmd, input_str):
        try:
            io_result = run(
                cmd,
                check=True, text=True, capture_output=True,
                input=input_str or None,
            )
            return io_result.stdout.rstrip("\n")
        except CalledProcessError as e:
            return e.stderr


def run_native_subprocess(ar):
    dom, cod = tuple(str for _ in ar.dom), tuple(str for _ in ar.cod)

    if ar.name == "⌜−⌝":
        def func(*params):
            if not params:
                return "" if ar.dom == Ty() else ar.dom.name
            return untuplify(params)
        return IO(func, dom, cod)

    if ar.name == "(||)":
        def func(*params):
            def inner_runner(*args):
                input_val = untuplify(args)
                mapped = []
                for (dk, k), (dv, v) in batched(zip(ar.dom, params), 2):
                    b0 = k(input_val)
                    res = v(b0)
                    mapped.append(res)
                return untuplify(tuple(mapped))
            return IO(inner_runner, (str,), (str,))
        return IO(func, dom, cod)

    if ar.name == "(;)":
        def func(*params):
            return params[0] >> params[1]
        return IO(func, dom, cod)

    if ar.name == "g":
        def func(*params):
            return IO.runner(params, None)
        return IO(func, dom, cod)

    if ar.name == "G":
        def func(*params):
            return IO(lambda *args: IO.runner(params, untuplify(args)), (str,), (str,))
        return IO(func, dom, cod)

    return IO(lambda *args: args, dom, cod)

SHELL_RUNNER = Functor(
    lambda ob: str,
    lambda ar: run_native_subprocess(ar),
    cod=Category(python.Ty, IO))


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
