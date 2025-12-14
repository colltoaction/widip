from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run

from discopy.symmetric import Category, Functor, Ty, Box
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)
    def run_native_subprocess_map(*params):
        # TODO cat then copy to two
        # but formal is to pass through
        mapped = []
        start = 0
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            # note that the key cod and value dom might be different
            b0 = k(*tuplify(params))
            res = untuplify(v(*tuplify(b0)))
            mapped.append(untuplify(res))
        
        return untuplify(tuple(mapped))
    def run_native_subprocess_seq(*params):
        b0 = b[0](*untuplify(params))
        res = untuplify(b[1](*tuplify(b0)))
        return res
    def run_native_subprocess_inside(*params):
        try:
            io_result = run(
                b,
                check=True, text=True, capture_output=True,
                input="\n".join(params) if params else None,
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
    if hasattr(diagram, "to_diagram"):
        diagram = diagram.to_diagram()
    diagram = SHELL_COMPILER(diagram)
    return diagram
