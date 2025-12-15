import sys
from functools import partial
from itertools import batched
from subprocess import Popen, PIPE

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def run_native_subprocess_constant(*params, capture=False, **kwargs):
        if not params:
            return "" if ar.dom == Ty() else ar.dom.name
        return untuplify(params)
    def run_native_subprocess_map(*params, capture=False, **kwargs):
        # TODO cat then copy to two
        # but formal is to pass through
        mapped = []
        start = 0
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            # note that the key cod and value dom might be different
            # Map always captures children output because results are aggregated
            b0 = k(*tuplify(params), capture=True)
            res = untuplify(v(*tuplify(b0), capture=True))
            mapped.append(untuplify(res))
        
        return untuplify(tuple(mapped))
    def run_native_subprocess_seq(*params, capture=False, **kwargs):
        # Sequence: First element must capture to pass to second.
        # Second element respects our capture request.
        b0 = b[0](*untuplify(params), capture=True)
        res = untuplify(b[1](*tuplify(b0), capture=capture))
        return res
    def run_native_subprocess_inside(*params, capture=False, **kwargs):
        try:
            with Popen(
                b,
                text=True,
                stdout=PIPE if capture else sys.stdout,
                stderr=sys.stderr,
                stdin=PIPE if params else sys.stdin
            ) as process:
                if params:
                    try:
                        for p in params:
                            process.stdin.write(p + "\n")
                    except BrokenPipeError:
                        pass
                    process.stdin.close()

                if capture:
                    stdout_data = process.stdout.read()
                else:
                    stdout_data = ""
                process.wait()

            if process.returncode != 0:
                return ""

            if capture:
                return stdout_data.rstrip("\n")
            return ""
        except Exception:
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
