from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run, Popen, PIPE

from discopy.closed import Category, Functor, Ty, Box, Eval
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    def resolve(x):
        if isinstance(x, Popen):
            out, _ = x.communicate()
            return out.strip() if out else ""
        if callable(x):
             try:
                 res = x()
                 return resolve(res)
             except TypeError:
                 pass
        return str(x)

    def run_native_subprocess_constant(*params):
        val = ""
        if b:
            val = resolve(b[0])
        elif ar.dom:
            val = ar.dom.name

        return Popen(["echo", "-n", val], stdout=PIPE, text=True)

    def run_native_subprocess_map(*params):
        mapped = []
        for (dk, k), (dv, v) in batched(zip(ar.dom, b), 2):
            b0 = k(*tuplify(params))
            res = untuplify(v(*tuplify(b0)))
            mapped.append(untuplify(res))
        
        return untuplify(tuple(mapped))

    def run_native_subprocess_seq(*params):
        b0 = b[0](*untuplify(params))
        res = untuplify(b[1](*tuplify(b0)))
        return res

    def run_native_subprocess_inside(*params):
        cmd_parts = [resolve(x) for x in b]

        stdin = None
        if params:
            p_in = params[0]
            if isinstance(p_in, Popen):
                stdin = p_in.stdout

        try:
            # We return process, so no try/except needed for execution unless Popen init fails.
            proc = Popen(cmd_parts, stdin=stdin, stdout=PIPE, text=True)
            return proc
        except Exception as e:
            raise e

    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if ar.name == "g":
        res = run_native_subprocess_inside()
        return res
    if ar.name == "G":
        return run_native_subprocess_inside

SHELL_RUNNER = Functor(
    lambda ob: object,
    lambda ar: partial(run_native_subprocess, ar),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    lambda ob: ob,
    lambda ar: {
    }.get(ar.name, ar),)

def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
