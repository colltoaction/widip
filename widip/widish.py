from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run

from discopy.frobenius import Category, Functor, Ty, Box, Spider
from discopy.utils import tuplify, untuplify
from discopy import python


io_ty = Ty("io")

def run_native_subprocess(ar, *b):
    """
    Executes the box logic immediately.
    ar: the Box object.
    *b: input arguments (strings).
    """
    try:
        # Debugging input
        # print(f"DEBUG: Box {ar.name} input: {b}")
        
        if ar.name.startswith("Value: "):
            val = ar.name[7:].strip()
            # Value box ignores input and returns value
            return val

        if ar.name.startswith("command: "):
            cmd = ar.name[9:]
            # Input to command is the first argument if present
            input_str = b[0] if b else None

            full_cmd = cmd.split()

            # print(f"DEBUG: Running {full_cmd} with input len={len(input_str) if input_str else 0}")

            io_result = run(
                full_cmd,
                check=True, text=True, capture_output=True,
                input=input_str,
                )
            res = io_result.stdout.rstrip("\n")
            return res

        if ar.name == "Discard":
            return () # Empty tuple for Discard (1 -> 0)

        return ""
    except CalledProcessError as e:
        return e.stderr
    except IndexError:
        return ""

def python_spiders(n_legs_in, n_legs_out, type):
    def spider_func(*args):
        # args is a tuple of inputs.
        if n_legs_in == 1:
            val = args[0]
            if n_legs_out == 0:
                return ()
            return (val,) * n_legs_out
        else:
             return args

    dom_type = (type,) * n_legs_in
    if isinstance(type, tuple):
        dom_type = type * n_legs_in

    cod_type = (type,) * n_legs_out
    if isinstance(type, tuple):
        cod_type = type * n_legs_out

    return python.Function(lambda *args: spider_func(*args), dom_type, cod_type)

python.Function.spiders = staticmethod(python_spiders)


SHELL_RUNNER = Functor(
    lambda ob: object,
    lambda ar: partial(run_native_subprocess, ar),
    cod=Category(python.Ty, python.Function))


SHELL_COMPILER = Functor(
    lambda ob: ob,
    lambda ar: ar)


def compile_shell_program(diagram):
    return SHELL_COMPILER(diagram)
