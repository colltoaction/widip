from functools import partial
from itertools import batched
from subprocess import CalledProcessError, run

from discopy.frobenius import Category, Functor, Ty, Box
from discopy.utils import tuplify, untuplify
from discopy import python


def run_native_subprocess(ar, *args):
    """
    Executes a shell command for the given box `ar` with input arguments `args`.
    """
    params = untuplify(args) if args else None

    # If the box is a literal (Ty() -> S), we expect no args.
    if ar.dom == Ty() and ar.cod == Ty("s"):
        return ar.name

    # If the box is a command, we run it.
    # Command usually takes input (stdin) and produces output (stdout).
    # S -> S or S -> Ty()

    input_str = None
    if isinstance(params, str):
        input_str = params
    elif isinstance(params, tuple):
        # Join tuple arguments with newline? Or handle as multiple args?
        # For now, assume string data flow.
        input_str = "\n".join(str(p) for p in params)

    cmd_name = ar.name
    # Handle "echo" explicitly if needed, but subprocess echo works too.
    # The user wanted echo to be S -> Ty() (Unit).

    if cmd_name == "echo":
        # We print and return Unit
        if input_str is not None:
            print(input_str)
        return ()

    # Generic command execution
    try:
        # If ar.dom is Ty(), we run without input?
        # If ar.cod is Ty(), we discard output?

        io_result = run(
            [cmd_name],
            check=True, text=True, capture_output=True,
            input=input_str,
        )
        output = io_result.stdout.rstrip("\n")

        if ar.cod == Ty():
            # Discard output, return Unit
            # Maybe print it if it's an effect?
            # User said "echo ... maps to terminal object".
            # For other commands, if they return Unit, maybe we just discard.
            return ()

        return output
        
    except FileNotFoundError:
        # If command not found, maybe it's a generator or special box?
        # Or just return arguments if identity?
        return params
    except CalledProcessError as e:
        return e.stderr

def shell_ob_map(ob):
    if ob.name == "s":
        return str
    return str

def shell_ar_map(ar):
    return partial(run_native_subprocess, ar)

SHELL_RUNNER = Functor(
    ob=lambda x: str,
    ar=shell_ar_map,
    cod=Category(python.Ty, python.Function)
)

SHELL_COMPILER = Functor(
    lambda ob: ob,
    lambda ar: ar
)

def compile_shell_program(diagram):
    return SHELL_COMPILER(diagram)
