import sys
from functools import partial
from itertools import batched
from subprocess import Popen, PIPE

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)

    def run_native_subprocess_map(*params, stdin=None):
        mapped = []
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            def chain(stdin=stdin, k=k, v=v):
                p_k = k(*tuplify(params), stdin=stdin)
                p_v = v(stdin=p_k.stdout)
                p_k.stdout.close()
                return p_v
            mapped.append(chain)
        return tuple(mapped)

    def run_native_subprocess_seq(*params, stdin=None):
        def lazy_seq(stdin=stdin):
            p1 = b[0](stdin=stdin)
            p2 = b[1](stdin=p1.stdout)
            p1.stdout.close()
            return p2
        return lazy_seq

    def run_native_subprocess_inside(*params, stdin=None):
        def lazy_popen(stdin=stdin):
            process = Popen(
                b,
                text=True,
                stdout=PIPE,
                stderr=sys.stderr,
                stdin=stdin or PIPE
            )
            if params and process.stdin:
                for p in params:
                    process.stdin.write(p + "\n")
                process.stdin.close()
                process.stdin = None
            return process
        return lazy_popen

    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map()
    if ar.name == "(;)":
        return run_native_subprocess_seq()
    if ar.name == "g":
        return run_native_subprocess_inside(*b)
    if ar.name == "G":
        return run_native_subprocess_inside(*b)

SHELL_RUNNER = Functor(
    lambda ob: Popen if ob == io_ty else str,
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
