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
            io_result = run(
                b,
                check=True, text=True, capture_output=True,
                input="\n".join(params) if params else None,
                )
            res = io_result.stdout.rstrip("\n")
            if ar.cod == Ty():
                print(res)
                return ()
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
    if ar.dom == Ty():
        return ar.name

    # Generic process box (or G)
    # If it's not a special box, assume it's a command
    # ar.name is command, b are arguments
    # But run_native_subprocess_inside uses 'b' as args...
    # We need to prepend ar.name to b.

    # We create a new 'b' for the inner function
    # But run_native_subprocess_inside captures 'b' from THIS scope.
    # So we must modify 'b' or create a wrapper.

    if ar.name == "G" or ar.name == "G($)":
        command_args = b
    else:
        command_args = (ar.name,) + b

    def run_generic_inside(*params):
        # command_args captured? No, need to be careful with closure.
        # But 'b' is argument to run_native_subprocess.
        # We can define a new inner function that uses command_args.
        try:
            io_result = run(
                command_args,
                check=True, text=True, capture_output=True,
                input="\n".join(params) if params else None,
                )
            res = io_result.stdout.rstrip("\n")
            if ar.cod == Ty():
                print(res)
                return ()
            return res
        except CalledProcessError as e:
            return e.stderr

    if ar.cod == Ty():
        res = run_generic_inside()
        return ()

    return run_generic_inside

from discopy.utils import tuplify

def discard_print(*args):
    printed = []
    for arg in args:
        if callable(arg):
            try:
                res = arg("")
                if isinstance(res, tuple):
                    printed.extend(res)
                else:
                    printed.append(res)
            except Exception as e:
                printed.append(f"<Error executing: {e}>")
        else:
            printed.append(arg)

    if printed:
        for p in printed:
            print(p)
    return ()

SHELL_RUNNER = Functor(
    lambda ob: python.Ty(()) if ob == Ty() else python.Ty((str,)),
    lambda ar: discard_print if ar.name == "⏚" else partial(run_native_subprocess, ar),
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
