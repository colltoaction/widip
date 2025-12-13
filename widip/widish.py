from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run
from typing import Callable, Any

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("s")

def run_native_subprocess(ar, *b):
    if ar.name == "id":
        return lambda s: s

    if ar.name == "⌜−⌝":
        val = ""
        if b:
            val = untuplify(b)

        def func(stdin):
            return str(val)
        return func

    if ar.name == "(||)":
        def func(stdin):
            results = []
            for k, v in batched(b, 2):
                if callable(k):
                    out_k = k(stdin)
                else:
                    out_k = str(k)

                if callable(v):
                    out_v = v(out_k)
                else:
                    out_v = str(v)
                results.append(out_v)
            return tuple(results)
        return func

    if ar.name == "(;)":
        f1, f2 = b
        def func(stdin):
            out1 = f1(stdin) if callable(f1) else str(f1)
            if isinstance(out1, tuple):
                out1 = "\n".join(map(str, out1))
            out2 = f2(out1) if callable(f2) else str(f2)
            return out2
        return func

    if ar.name == "g":
        pass

    if ar.name == "G":
        def func(stdin):
            if not b:
                return ""
            cmd = b[0]
            rest = b[1:]

            input_str = stdin
            if len(rest) > 0 and callable(rest[0]):
                f_prev = rest[0]
                input_str = f_prev(stdin)
                params = rest[1:]
            else:
                params = rest

            cmd_args = [cmd]
            for p in params:
                if not callable(p):
                    cmd_args.append(str(p))

            try:
                io_result = run(
                    cmd_args,
                    check=True, text=True, capture_output=True,
                    input=input_str if input_str else None,
                )
                res = io_result.stdout.rstrip("\n")
                return res
            except CalledProcessError as e:
                return ""
        return func

    return lambda s: ""

SHELL_RUNNER = Functor(
    lambda ob: object if ob == io_ty else str,
    lambda ar: partial(run_native_subprocess, ar),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    # lambda ob: Ty() if ob == Ty("io") else ob,
    lambda ob: ob,
    lambda ar: {
        # "ls": ar.curry().uncurry()
    }.get(ar.name, ar),)


def compile_shell_program(diagram):
    """
    close input parameters (constants)
    drop outputs matching input parameters
    all boxes are io->[io]"""
    # TODO compile sequences and parallels to evals
    diagram = SHELL_COMPILER(diagram)
    return diagram
