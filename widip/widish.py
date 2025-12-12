from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run

from discopy.closed import Category, Functor, Ty, Box, Eval
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
            # construct command from b (inputs) and params (stdin/program inputs)
            # b contains arguments from input wires (e.g. filename)
            # params contains arguments from program flow (stdin)
            cmd_args = list(b)
            # Filter empty strings (from unused/default S inputs)
            cmd_args = [x for x in cmd_args if x != ""]

            if ar.name.startswith("command: "):
                cmd = ar.name[9:]
                full_cmd = [cmd] + [str(x) for x in cmd_args]

                input_str = "\n".join(str(p) for p in params) if params else None

                io_result = run(
                    full_cmd,
                    check=True, text=True, capture_output=True,
                    input=input_str,
                    )
                res = io_result.stdout.rstrip("\n")
                return res
            return ""
        except CalledProcessError as e:
            return e.stderr

    if ar.name.startswith("Value: "):
        val = ar.name[7:]
        # Check if codomain involves "Over" (is a Program-like type)
        # Note: ar.cod might be "Ty(String)" or "Ty() << Ty(Output)".
        # We need to distinguish "Atomic String output" from "Program output".
        is_over = False
        try:
            if hasattr(ar.cod, "is_over") and ar.cod.is_over:
                is_over = True
            elif len(ar.cod) > 0 and hasattr(ar.cod[0], "is_over") and ar.cod[0].is_over:
                is_over = True
        except AttributeError:
            pass

        if is_over:
             if val == "None":
                 return lambda x: x
             return lambda *args: val

        # If not Over, return value directly.
        return val

    if ar.name.startswith("command: "):
        return run_native_subprocess_inside

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
    lambda ob: object,
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
