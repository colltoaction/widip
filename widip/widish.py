from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run
from typing import Callable, Any

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("")

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

    if ar.name not in ["id", "⌜−⌝", "(||)", "(;)"]:
        def func(stdin):
            # b contains inputs (from wires in domain).
            # The command is ar.name.
            # We must execute the command.
            # But wait, SHELL_RUNNER returns a Python Function.
            # If the diagram is `Box("echo", S, S)`, it returns a function `object -> object`.
            # This function takes the input on `S` wire.
            # The input on `S` wire is the "previous output" (e.g. from `⌜−⌝`).
            # `⌜−⌝` returns a function `str->str`.
            # So `b[0]` is a function `input_func`.

            # The command execution logic:
            cmd = ar.name

            # The function returned by this box:
            def execution_logic(upstream_data):
                # upstream_data is passed from the previous box in the chain if composed?
                # No, SHELL_RUNNER composition:
                # Box1 ; Box2.
                # Runner(Box1) -> f1. Runner(Box2) -> f2.
                # Runner(Box1 ; Box2) -> f2(f1(x)).
                # Here `x` is the input to the whole diagram.
                # In `widish_main`, we call `runner("")`.
                # So `upstream_data` starts as "".

                # Wait! `run_native_subprocess` is called with `b`.
                # `b` corresponds to the input wires of the Box.
                # If `Box` is `Box("echo", S, S)`.
                # `b` contains the result of the previous box on wire `S`.
                # So `b` IS the function f1 (or whatever is on the wire).

                input_func = b[0] if b else None

                # Now we need to determine the input string for the command.
                # The input string comes from executing `input_func`.
                # But `input_func` needs an argument!
                # What argument?
                # The argument passed to the whole chain?
                # Yes, `upstream_data`.
                # Wait, if `input_func` is already a result of `partial` application?
                # No, the wires carry VALUES.
                # The values in this category are FUNCTIONS `str->str`.
                # So `input_func` is a function `str->str`.
                # We call `input_func(upstream_data)` to get the string.

                input_str = ""
                if input_func:
                    if callable(input_func):
                        input_str = input_func(upstream_data)
                    else:
                        input_str = str(input_func)

                # Execute command
                cmd_args = [cmd]
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

            return execution_logic

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
