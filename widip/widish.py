import sys
from functools import partial
from itertools import batched
from subprocess import Popen, PIPE

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params, capture=False):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)
    def run_native_subprocess_map(*params, capture=False):
        mapped = []
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            key_res = k(*tuplify(params), capture=True)
            kv_res = untuplify(v(*tuplify(key_res), capture=True))
            mapped.append(untuplify(kv_res))

        if capture:
            return "\n".join(mapped)
        print("\n".join(mapped))

    def run_native_subprocess_seq(*params, capture=False):
        # Sequence: First element must capture to pass to second.
        # Second element respects our capture request.
        b0 = b[0](*untuplify(params), capture=True)
        res = untuplify(b[1](*tuplify(b0), capture=capture))
        return res
    def run_native_subprocess_inside(*params, capture=False):
        with Popen(
            b,
            text=True,
            stdout=PIPE if capture else sys.stdout,
            stderr=sys.stderr,
            stdin=PIPE if params else sys.stdin
        ) as process:
            for p in params:
                process.stdin.write(p + "\n")
            if params:
                process.stdin.close()

            if capture:
                return process.stdout.read().rstrip("\n")
            return ""

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
