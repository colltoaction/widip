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
    def run_native_subprocess_eval(*params):
        f, x = params
        return f(x)

    def run_native_subprocess_inside(*params):
        # Determine command to run
        cmd = b if b else (ar.name,)

        # If the command is empty (shouldn't happen with ar.name fallback), return empty
        if not cmd:
            return ""

        # Removed prefix stripping logic as we are not manipulating strings anymore.
        # User requested not to manipulate strings in diagram.

        # Construct arguments: command + inputs
        full_cmd = list(cmd) + list(params)

        # Ensure all elements are strings
        if not all(isinstance(x, str) for x in full_cmd):
            # If we have non-string arguments, we can't run subprocess.
            return ""

        try:
            io_result = run(
                full_cmd,
                check=True, text=True, capture_output=True,
                )
            res = io_result.stdout.rstrip("\n")
            return res
        except CalledProcessError as e:
            return e.stderr
        except FileNotFoundError:
             return f"Command not found: {cmd}"
        except TypeError as e:
            raise e

    # Check for known control boxes
    if ar.name == "⌜−⌝":
        return run_native_subprocess_constant
    if ar.name == "(||)":
        return run_native_subprocess_map
    if ar.name == "(;)":
        return run_native_subprocess_seq
    if isinstance(ar, Eval) or ar.name == "Eval":
        return run_native_subprocess_eval
    if ar.name == "g":
        res = run_native_subprocess_inside(*b)
        return res

    # Handle scalar values (single quotes check)
    if ar.name.startswith("'") and ar.name.endswith("'"):
        # It's a scalar value like 'Hello world!'
        # Return a function that returns the value (without quotes)
        val = ar.name[1:-1]
        def return_val(*params):
            return val
        return return_val

    # Removed handling for "Value: ..." prefix.

    # Default to running as a subprocess command
    # This covers "G" and now specific tags like "echo"
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
