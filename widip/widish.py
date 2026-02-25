from functools import partial
from subprocess import CalledProcessError, run

from discopy.utils import tuplify, untuplify
from discopy import closed, python


io_ty = closed.Ty("io")

def split_args(ar, args):
    n = len(ar.dom)
    return args[:n], args[n:]

def run_native_subprocess_constant(ar, *args):
    b, params = split_args(ar, args)
    if not params:
        return "" if ar.dom == closed.Ty() else ar.dom.name
    return untuplify(params)

def run_native_subprocess_map(ar, *args):
    b, params = split_args(ar, args)
    mapped = []
    for kv in b:
        res = kv(*tuplify(params))
        mapped.append(untuplify(res))
    return untuplify(tuple(mapped))

def run_native_subprocess_seq(ar, *args):
    b, params = split_args(ar, args)
    b0 = b[0](*tuplify(params))
    b1 = b[1](*tuplify(b0))
    return untuplify(b1)

def run_native_subprocess_default(ar, *args):
    b, params = split_args(ar, args)
    io_result = run(
        (ar.name,) + b,
        check=True, text=True, capture_output=True,
        input="\n".join(params) if params else None,
        )
    res = io_result.stdout.rstrip("\n")
    return res

SHELL_RUNNER = closed.Functor(
    lambda ob: str,
    lambda ar: {
        # implementar gamma
        "⌜−⌝": partial(partial, run_native_subprocess_constant, ar), # cambiar a encode
        "(||)": partial(partial, run_native_subprocess_map, ar),
        "(;)": partial(partial, run_native_subprocess_seq, ar),
    }.get(ar.name, partial(partial, run_native_subprocess_default, ar)),
    cod=closed.Category(python.Ty, python.Function))


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
