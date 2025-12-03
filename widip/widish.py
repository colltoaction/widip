from functools import partial
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        # res = tuplify(untuplify(params[:len(ar.cod.base)]) if params else ar.dom.name if ar.dom else "")
        res = tuple(map(untuplify, params)) + tuple(map(untuplify, b))
        return res
    def run_native_subprocess_map(*params):
        # TODO for each bases
        i = 0
        start = 0
        bps = []
        for i in range(len(b)):
            e = ar.dom[i].inside[0].exponent
            end = start+len(e)
            xp = params[start:end]
            bps.append(xp)
            start = end
        res = tuple((x(*tuplify(ps)) for x, ps in zip(b, bps)))
        return res
    def run_native_subprocess_seq(*params):
        b0 = b[0](*params)
        res = "\n".join(tuplify(b[1](*tuplify(b0))))
        return res
    def run_native_subprocess_inside(*params):
        try:
            io_result = run(
                b,
                check=True, text=True, capture_output=True,
                input="\n".join(params) or None,
                )
            res = io_result.stdout.rstrip("\n")
            return res
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
        return run_native_subprocess_inside

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
